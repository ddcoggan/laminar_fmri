# /usr/bin/python
# Created by David Coggan on 2022 10 11

import os
import glob
import datetime
import nighres
import os.path as op
import subprocess
import itertools

def registration(overwrite):

    print('Performing registration...')
    subject, session = 'M001', '1'
    fs_subject = f'sub-{subject}'

    # directories
    fs_dir = f'{os.environ["SUBJECTS_DIR"]}/{fs_subject}'
    xform_dir = f'{fs_dir}/mri/transforms'
    fnirt_dir = f'{fs_dir}/mri/transforms/fnirt'
    os.makedirs(fnirt_dir, exist_ok=True)
    reg_dir = f'derivatives/registration/sub-{subject}'
    os.makedirs(reg_dir, exist_ok=True)

    # reference images
    ref_func = (f'sub-{subject}/ses-{session}/func/sub-'
                f'{subject}_ses-{session}_task-restingState_run-1_part'
                f'-mag_bold_motcor_Tmean.nii.gz')
    if not op.isfile(ref_func):
        ref_base = ref_func.split("_motcor")[0]
        os.system(f'mcflirt -in {ref_base} -out {ref_base}_motcor')
        os.system(f'fslmaths {ref_base}_motcor -Tmean {ref_func}')
    ref_anat = f'{fs_dir}/mri/orig/001.nii'
    ref_anat_brain = f'{fs_dir}/mri/orig/001_brain.nii.gz'
    ref_std = f'{os.environ["FSLDIR"]}/data/standard/MNI152_T1_2mm.nii.gz'
    ref_std_brain = f'{ref_std[:-7]}_brain.nii.gz'
    ref_std_mask = f'{ref_std[:-7]}_brain_mask_dil.nii.gz'

    # transform 1: between standard space and anatomical space
    # this is all done in subject's freesurfer directory

    # freesurfer method
    standard2highres_lta = f'{xform_dir}/reg.mni152.2mm.lta'
    if not op.isfile(standard2highres_lta):
        os.system(f'mni152reg --s {fs_subject}')

    # FSL method

    # make links to reference images
    for in_path, label in zip(
            [ref_anat, ref_std, ref_std_brain],
            ['highres.nii.gz', 'standard_head.nii.gz', 'standard.nii.gz']):
        out_path = f'{fnirt_dir}/{label}'
        if not op.exists(out_path):
            os.system(f'ln -s {in_path} {out_path}')

    # linear
    highres2standard = f'{fnirt_dir}/highres2standard.mat'
    if not op.isfile(highres2standard) or 'anat_std' in overwrite:
        os.system(f'flirt '
                  f'-in {ref_anat} '
                  f'-ref {ref_std} '
                  f'-omat {highres2standard} '
                  f'-cost corratio '
                  f'-dof 12 '
                  f'-searchrx -90 90 '
                  f'-searchry -90 90 '
                  f'-searchrz -90 90 '
                  f'-interp trilinear')
    standard2highres = f'{fnirt_dir}/standard2highres.mat'
    if not op.isfile(standard2highres) or 'anat_std' in overwrite:
        os.system(f'convert_xfm -inverse '
                  f'-omat {standard2highres} '
                  f'{highres2standard}')

    # non-linear
    highres2standard_warp = f'{fnirt_dir}/highres2standard_warp.nii.gz'
    if not op.isfile(highres2standard_warp) or 'anat_std' in overwrite:
        os.system(f'fnirt '
                  f'--in={ref_anat} '
                  f'--ref={ref_std} '
                  f'--refmask={ref_std_mask} '
                  f'--config=T1_2_MNI152_2mm '
                  f'--aff={highres2standard} '
                  f'--cout={highres2standard_warp} '
                  f'--iout={fnirt_dir}/highres2standard_head '
                  f'--jout={fnirt_dir}/highres2highres_jac '
                  f'--warpres=10,10,10')
    standard2highres_warp = f'{fnirt_dir}/standard2highres_warp.nii.gz'
    if not op.isfile(standard2highres_warp) or 'anat_std' in overwrite:
        os.system(f'invwarp '
                  f'-w {highres2standard_warp} '
                  f'-o {standard2highres_warp} '
                  f'-r {ref_anat}')

    # apply transform to ref anat
    highres2standard_img = f'{fnirt_dir}/highres2standard.nii.gz'
    if not op.isfile(highres2standard_img) or 'anat_std' in overwrite:
        os.system(f'applywarp '
                  f'-i {ref_anat_brain} '
                  f'-r {ref_std_brain} '
                  f'-o {highres2standard_img} '
                  f'-w {highres2standard_warp}')

    # make reg images
    d = fnirt_dir
    if not op.isfile(
            f'{d}/highres2standard.png') or 'anat_std' in overwrite:
        slicer_str = (
            f'-x 0.35 {d}/sla.png -x 0.45 {d}/slb.png '
            f'-x 0.55 {d}/slc.png -x 0.65 {d}/sld.png '
            f'-y 0.35 {d}/sle.png -y 0.45 {d}/slf.png '
            f'-y 0.55 {d}/slg.png -y 0.65 {d}/slh.png '
            f'-z 0.35 {d}/sli.png -z 0.45 {d}/slj.png '
            f'-z 0.55 {d}/slk.png -z 0.65 {d}/sll.png')
        append_str = ' + '.join([f'{d}/sl{i}.png' for i in 'abcdefghijkl'])

        cmd = f'slicer {d}/highres2standard {d}/standard -s 2 {slicer_str}'
        subprocess.Popen(cmd.split()).wait()

        cmd = f'pngappend {append_str} {d}/highres2standard1.png'
        subprocess.Popen(cmd.split()).wait()

        cmd = f'slicer {d}/standard {d}/highres2standard -s 2 {slicer_str}'
        subprocess.Popen(cmd.split()).wait()

        cmd = f'pngappend {append_str} {d}/highres2standard2.png'
        subprocess.Popen(cmd.split()).wait()

        cmd = (f'pngappend {d}/highres2standard1.png - '
               f'{d}/highres2standard2.png {d}/highres2standard.png')
        subprocess.Popen(cmd.split()).wait()

    # clean up
    for search in ['*1.png', '*2.png', 'sl?.png']:
        imgs = glob.glob(f'{d}/{search}')
        for img in imgs:
            os.remove(img)

    # put link to everything in local project reg dir
    in_paths = glob.glob(f'{fnirt_dir}/*')
    for path in in_paths:
        outpath = f'{reg_dir}/{op.basename(path)}'
        if not op.exists(outpath):
            os.system(f'ln -s {path} {outpath}')

    # transform 2: between anatomical space and functional space
    method = 'freesurfer'# 'FSL'

    # link to example_func
    out_path = f'{reg_dir}/example_func.nii.gz'
    if not op.exists(out_path):
        os.system(f'ln -s {op.abspath(ref_func)} {out_path}')

    if method == 'FSL':

        example_func2highres = f'{reg_dir}/example_func2highres.mat'
        if not op.isfile(example_func2highres) or 'func_anat' in overwrite:
            # BBR
            os.system(
                f'epi_reg '
                f'--epi={ref_func} '
                f'--t1={ref_anat} '
                f'--t1brain='
                f'{ref_anat_brain} '
                f'--out={example_func2highres[:-4]}')

            # linear search
            # os.system(f'flirt -in {ref_anat_brain} -ref {ref_func}
            #     -omat {highres2example_func}')

        highres2example_func = f'{reg_dir}/highres2example_func.mat'
        if not op.isfile(highres2example_func) or 'func_anat' in overwrite:
            os.system(f'convert_xfm '
                      f'-omat {highres2example_func} '
                      f'-inverse '
                      f'{example_func2highres}')

    elif method == 'freesurfer':

        lta = f'{reg_dir}/example_func2highres.lta'
        if not op.isfile(lta) or 'func_anat' in overwrite:
            os.system(f'bbregister '
                      f'--s {fs_subject} '
                      f'--mov {ref_func} '
                      f'--init-fsl '
                      f'--lta {lta} '
                      f'--bold')

        example_func2highres = f'{reg_dir}/example_func2highres.mat'
        if not op.isfile(example_func2highres) or 'func_anat' in overwrite:
            os.system(f'lta_convert '
                      f'--inlta {lta} '
                      f'--outfsl {example_func2highres} '
                      f'--src {ref_func} '
                      f'--trg {ref_anat}')

        lta_inv = f'{reg_dir}/highres2example_func.lta'
        if not op.isfile(lta_inv) or 'func_anat' in overwrite:
            os.system(f'lta_convert '
                      f'--inlta {lta} '
                      f'--outlta {lta_inv} '
                      f'--invert')

        highres2example_func = f'{reg_dir}/highres2example_func.mat'
        if not op.isfile(highres2example_func) or 'func_anat' in overwrite:
            os.system(f'lta_convert '
                      f'--inlta {lta_inv} '
                      f'--outfsl {highres2example_func} '
                      f'--src {ref_anat} '
                      f'--trg {ref_func}')

    # apply transform to ref func
    example_func2highres_img = f'{reg_dir}/example_func2highres.nii.gz'
    if not op.isfile(example_func2highres_img) or 'func_anat' in overwrite:
        os.system(f'flirt '
                  f'-in {ref_func} '
                  f'-ref {ref_anat} '
                  f'-applyxfm -init {example_func2highres} '
                  f'-out {example_func2highres_img}')

    # make reg images
    d = reg_dir
    if (not op.isfile(f'{d}/example_func2highres.png') or 'func_anat' in
            overwrite):
        slicer_str = (
            f'-x 0.35 {d}/sla.png -x 0.45 {d}/slb.png '
            f'-x 0.55 {d}/slc.png -x 0.65 {d}/sld.png '
            f'-y 0.35 {d}/sle.png -y 0.45 {d}/slf.png '
            f'-y 0.55 {d}/slg.png -y 0.65 {d}/slh.png '
            f'-z 0.35 {d}/sli.png -z 0.45 {d}/slj.png '
            f'-z 0.55 {d}/slk.png -z 0.65 {d}/sll.png')
        append_str = ' + '.join(
            [f'{d}/sl{i}.png' for i in 'abcdefghijkl'])

        cmd = f'slicer {d}/example_func2highres {d}/highres -s 2 {slicer_str}'
        subprocess.Popen(cmd.split()).wait()

        cmd = f'pngappend {append_str} {d}/example_func2highres1.png'
        subprocess.Popen(cmd.split()).wait()

        cmd = (f'slicer {d}/highres {d}/example_func2highres -s 2'
               f' {slicer_str}')
        subprocess.Popen(cmd.split()).wait()

        cmd = f'pngappend {append_str} {d}/example_func2highres2.png'
        subprocess.Popen(cmd.split()).wait()

        cmd = (f'pngappend {d}/example_func2highres1.png - '
               f'{d}/example_func2highres2.png {d}/example_func2highres.png')
        subprocess.Popen(cmd.split()).wait()

    # clean up
    for search in ['*1.png', '*2.png', 'sl?.png']:
        imgs = glob.glob(f'{d}/{search}')
        for img in imgs:
            os.remove(img)


    # transform 3: between functional space and standard space

    # concatenate func to standard and standard to func (linear)
    example_func2standard = f'{reg_dir}/example_func2standard.mat'
    if not op.isfile(example_func2standard) or len(overwrite):
        os.system(f'convert_xfm '
                  f'-omat {example_func2standard} '
                  f'-concat {example_func2highres} {highres2standard}')
    standard2example_func = f'{reg_dir}/standard2example_func.mat'
    if not op.isfile(standard2example_func) or len(overwrite):
        os.system(f'convert_xfm '
                  f'-omat {standard2example_func} '
                  f'-concat {standard2highres} {highres2example_func}')

    # concatenate func to standard and standard to func (non-linear)
    example_func2standard_warp = (
        f'{reg_dir}/example_func2standard_warp.nii.gz')
    if not op.isfile(example_func2standard_warp) or len(overwrite):
        os.system(f'convertwarp '
                  f'--ref={ref_std_brain} '
                  f'--premat={example_func2highres} '
                  f'--warp1={highres2standard_warp} '
                  f'--out={example_func2standard_warp}')
    standard2example_func_warp = (
        f'{reg_dir}/standard2example_func_warp.nii.gz')
    if not op.isfile(standard2example_func_warp) or len(overwrite):
        os.system(f'invwarp '
                  f'-w {example_func2standard_warp} '
                  f'-o {standard2example_func_warp} '
                  f'-r {ref_func}')

    # apply transform to ref func
    example_func2standard_img = f'{reg_dir}/example_func2standard.nii.gz'
    if not op.isfile(example_func2standard_img) or len(overwrite):
        os.system(f'applywarp '
                  f'-i {ref_func} '
                  f'-r {ref_std_brain} '
                  f'-o {reg_dir}/example_func2standard '
                  f'-w {reg_dir}/example_func2standard_warp')

    # make reg images
    d = reg_dir
    if not op.isfile(f'{d}/example_func2standard.png') or len(overwrite):
        slicer_str = (
            f'-x 0.35 {d}/sla.png -x 0.45 {d}/slb.png '
            f'-x 0.55 {d}/slc.png -x 0.65 {d}/sld.png '
            f'-y 0.35 {d}/sle.png -y 0.45 {d}/slf.png '
            f'-y 0.55 {d}/slg.png -y 0.65 {d}/slh.png '
            f'-z 0.35 {d}/sli.png -z 0.45 {d}/slj.png '
            f'-z 0.55 {d}/slk.png -z 0.65 {d}/sll.png')
        append_str = ' + '.join([f'{d}/sl{i}.png' for i in 'abcdefghijkl'])

        cmd = f'slicer {d}/example_func2standard {d}/standard -s 2 {slicer_str}'
        subprocess.Popen(cmd.split()).wait()

        cmd = f'pngappend {append_str} {d}/example_func2standard1.png'
        subprocess.Popen(cmd.split()).wait()

        cmd = f'slicer {d}/standard {d}/example_func2standard -s 2 {slicer_str}'
        subprocess.Popen(cmd.split()).wait()

        cmd = f'pngappend {append_str} {d}/example_func2standard2.png'
        subprocess.Popen(cmd.split()).wait()

        cmd = (f'pngappend {d}/example_func2standard1.png - '
               f'{d}/example_func2standard2.png {d}/example_func2standard.png')
        subprocess.Popen(cmd.split()).wait()

    for search in ['*1.png', '*2.png', 'sl?.png']:
        imgs = glob.glob(f'{d}/{search}')
        for img in imgs:
            os.remove(img)

    # collate registrations for inspection
    for transform in ['highres2standard', 'example_func2standard']:
        plot_dir = f'derivatives/registration/plots/{transform}'
        os.makedirs(plot_dir, exist_ok=True)
        out_path = f'{plot_dir}/{subject}.png'
        if not op.isfile(out_path):
            image = f'{reg_dir}/{transform}.png'
            os.system(f'ln -sf {op.abspath(image)} {out_path}')


if __name__ == "__main__":
    overwrite = []
    registration(overwrite)


