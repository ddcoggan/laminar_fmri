# /usr/bin/python
# Created by David Coggan on 2023 06 23
import os
import os.path as op
import json
import glob
import shutil
import pandas as pd

from .test_NORDIC import test_NORDIC

def preprocess(n_procs):

    subjects = ['M001']#json.load(open('participants.json', 'r+'))

    # NORDIC correction
    test_NORDIC()

    # run data quality measures for each
    for preproc_dir in [''] + glob.glob('derivatives/NORDIC*'):

        # mriqc (data quality measures)
        version = '23.1.0'
        indir = op.abspath(preproc_dir)
        outdir = op.join(indir, f'derivatives/mriqc-{version}')
        os.makedirs(outdir, exist_ok=True)
        workdir = op.join(indir, f'derivatives/mriqc-work')
        if op.isdir(workdir):
            shutil.rmtree(workdir)
        os.makedirs(workdir)

        # individual subjects
        new_subjects = False
        cmd_base = f'docker run --rm ' \
                   f'--mount type=bind,src={indir},dst=/data ' \
                   f'--mount type=bind,src={outdir},dst=/out ' \
                   f'--mount type=bind,src={workdir},dst=/work ' \
                   f'--memory=32g ' \
                   f'--memory-swap=64g ' \
                   f'nipreps/mriqc:{version} ' \
                   f'--nprocs {n_procs} ' \
                   f'--verbose-reports ' \
                   f'--resource-monitor ' \
                   f'-f ' \
                   f'-w /work ' \
                   f'/data /out '
        for subject in subjects:
            if not op.isdir(f'{outdir}/sub-{subject}'):
                cmd = cmd_base + f'participant --participant-label {subject}'
                print(cmd)
                os.system(cmd)
                new_subjects = True

        # group level
        if not os.path.isfile(f'{outdir}/group_bold.html') or new_subjects:
            cmd = cmd_base + 'group'
            print(cmd)
            os.system(cmd)

        shutil.rmtree(workdir)


    # fMRIprep (preprocessing)

    # These are performed on individual basis as fmriprep does not check which
    # subjects are already processed
    # TODO: allow to run these in parallel if > 16 cores, 8 cores per subject
    # https://fmriprep.org/en/stable/faq.html#running-subjects-in-parallel
    version = '23.0.2'
    indir = op.abspath('')
    outdir = op.abspath(f'derivatives/fmriprep-{version}')
    os.makedirs(outdir, exist_ok=True)
    workdir = op.abspath('derivatives/fmriprep_work')
    if op.isdir(workdir):
        shutil.rmtree(workdir)
    os.makedirs(workdir)
    subjdir = op.abspath(os.environ['SUBJECTS_DIR'])

    for subject in subjects:
        if not op.isdir(f'{outdir}/sub-{subject}'):
            cmd = f'docker run --rm ' \
                  f'--mount type=bind,src={indir},dst=/data ' \
                  f'--mount type=bind,src={outdir},dst=/out ' \
                  f'--mount type=bind,src={subjdir},dst=/fs_subjects ' \
                  f'--mount type=bind,src={workdir},dst=/work ' \
                  f'--memory=32g ' \
                  f'--memory-swap=64g ' \
                  f'nipreps/fmriprep:{version} ' \
                  f'--clean-workdir ' \
                  f'--resource-monitor ' \
                  f'--anat-only ' \
                  f'--skip-bids-validation ' \
                  f'--nprocs {n_procs} ' \
                  f'--mem-mb 64000 ' \
                  f'--fs-license-file /fs_subjects/license.txt ' \
                  f'--fs-subjects-dir /fs_subjects ' \
                  f'--output-spaces func ' \
                  f'-w /work ' \
                  f'/data /out ' \
                  f'participant --participant-label {subject}'
            print(cmd)
            os.system(cmd)

    shutil.rmtree(workdir)


    fs_dir = f'{os.environ["SUBJECTS_DIR"]}/sub-{subjects[0]}'

    # convert anatomicals to nifti and extract brain
    # (final preprocessed anatomical and original anatomical)
    for mgz in [f'{fs_dir}/mri/T1.mgz', f'{fs_dir}/mri/orig/001.mgz']:

        # convert to nifti
        nii = f'{mgz[:-4]}.nii'
        if not op.isfile(nii):
            os.system(f'mri_convert {mgz} {nii}')

        # extract brain
        nii_brain = f'{mgz[:-4]}_brain.nii.gz'
        if not op.isfile(nii_brain):
            os.system(f'mri_synthstrip -i {nii} -o {nii_brain}')# -g')


