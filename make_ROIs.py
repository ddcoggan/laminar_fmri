# /usr/bin/python
# Created by David Coggan on 2022 10 11

import os
import glob
import datetime
import nighres
import os.path as op
import subprocess
import itertools

def make_ROIs(overwrite):
    
    subjects = ['M001']
    regions_std = ['V1']
    
    # CONVERT EACH ROI
    for subject in subjects:

        # directories
        fs_dir = f'{os.environ["SUBJECTS_DIR"]}/sub-{subject}'
        reg_dir = f'derivatives/registration/sub-{subject}'
        roi_dir = f'derivatives/ROIs/sub-{subject}'
        os.makedirs(roi_dir, exist_ok=True)
        highres2example_func = f'{reg_dir}/highres2example_func.mat'

        # reference images
        ref_func = (f'derivatives/registration/sub'
                    f'-{subject}/example_func.nii.gz')
        ref_anat = f'{fs_dir}/mri/orig/001.nii'
        ref_anat_brain = f'{fs_dir}/mri/orig/001_brain.nii.gz'
        ref_std = f'{os.environ["FSLDIR"]}/data/standard/MNI152_T1_2mm.nii.gz'
        ref_std_brain = f'{ref_std[:-7]}_brain.nii.gz'
        ref_std_mask = f'{ref_std[:-7]}_brain_mask_dil.nii.gz'

        # cortex
        for hemi in ['lh', 'rh']:

            # cortex mgz to nifti
            mgz_fs = f'{fs_dir}/mri/{hemi}.ribbon.mgz'
            mgz_native = f'{fs_dir}/mri/orig/{hemi}.ribbon.mgz'
            ref_anat_mgz = f'{fs_dir}/mri/orig/001.mgz'
            nii = f'{fs_dir}/mri/orig/{hemi}.ribbon.nii.gz'
            if not os.path.exists(nii) or overwrite:
                print(f'Converting {hemi} cortex from fs to native space...')
                os.system(f'mri_vol2vol '
                          f'--mov {mgz_fs} '
                          f'--targ {ref_anat_mgz} '
                          f'--regheader '
                          f'--o {mgz_native} '
                          f'--nearest '
                          f'--no-save-reg')
                print(f'Converting {hemi} cortex from mgz to nifti...')
                os.system(f'mri_convert '
                          f'--in_type mgz '
                          f'--out_type nii '
                          f'-rt nearest '
                          f'{mgz_native} {nii}')

        cortex_highres = f'{fs_dir}/mri/orig/bi.ribbon.nii.gz'
        if not op.isfile(cortex_highres) or overwrite:
            print(f'Combining left and right hemispheres...')
            os.system(
                f'fslmaths {fs_dir}/mri/orig/lh.ribbon.nii.gz -add'
                f' {fs_dir}/mri/orig/rh.ribbon.nii.gz -bin {cortex_highres}')


        # func space
        cortex_func = f'{roi_dir}/cortex.nii.gz'
        if not op.isfile(cortex_func) or overwrite:
            print('Transforming cortex mask to functional space...')
            os.system(f'flirt '
                      f'-in {fs_dir}/mri/orig/bi.ribbon.nii.gz '
                      f'-ref {ref_func} '
                      f'-out {cortex_func} '
                      f'-applyxfm -init {highres2example_func} '
                      f'-interp nearestneighbour')


        # standard space masks
        for region in regions_std:

            mask_std = glob.glob(os.path.expanduser(
                f'~/david/masks/**/{region}.nii.gz'))[0]
            mask_func = f'{roi_dir}/{region}.nii.gz'

            if not os.path.exists(mask_func) or overwrite:
                os.system(f'applywarp '
                          f'-i {mask_std} '
                          f'-r {ref_func} '
                          f'-o {mask_func} '
                          f'-w {reg_dir}/standard2example_func_warp '
                          f'--interp=nn')

            # combine cortex mask with ROI mask
            mask_final = f'{roi_dir}/{region}_cortex.nii.gz'
            if not os.path.isfile(mask_final) or overwrite:
                print('Combining ROI mask with cortical mask...')
                os.system(f'fslmaths {roi_dir}/cortex.nii.gz '
                          f'-mul {mask_func} {mask_final}')


if __name__ == "__main__":

    overwrite = False
    make_ROIs(overwrite)


