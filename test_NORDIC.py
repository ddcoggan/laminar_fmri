# /usr/bin/python
# Created by David Coggan on 2024 08 23
import os
import os.path as op
import datetime
import matlab.engine
import sys
import glob
import shutil
from itertools import product as itp
import gzip


def test_NORDIC():

    """
    This function tests the TSNR gains for all possible combinations of
    magnitude/phase components, i.e., whether we take them directly from the
    scanner or calculate them from other components.
    """

    subject, session = 'M001', '1'
    session_dir = f'sub-{subject}/ses-{session}'
    anat_dir = f'{session_dir}/anat'
    func_dir = f'{session_dir}/func'
    fmap_dir = f'{session_dir}/fmap'
    funcscans = glob.glob(f'{func_dir}/*restingState*run-1*part-mag_bold.nii')
    assert len(funcscans) == 1
    funcscan = funcscans[0]

    print(f'{datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")} | '
          f'NORDIC preprocessing | Subject: {subject} | Session: {session} | '
          f'Scan: {funcscan}')

    """
    Rename the measured files, then create the calculated files. BIDS 
    doesn't mind a lack of run number in the filename as long as the 
    acquisition parameter distinguishes the runs.
    """
    for cpnt in ['mag', 'phase']:
        src = funcscan.replace('part-mag', f'part-{cpnt}')
        dst = src.replace('run-1', f'acq-meas')
        if op.isfile(src) and not op.isfile(dst):
            os.rename(src, dst)


    # Calculated versions of the magnitude and phase components
    funcscan = funcscan.split('.nii')[0]  # remove extension, let FSL handle it
    mag_calc = funcscan.replace('run-1', f'acq-calc')
    phase_calc = mag_calc.replace('part-mag', 'part-phase')
    if not op.isfile(mag_calc+'.nii.gz') or not op.isfile(phase_calc+'.nii.gz'):

        print('calculating complex from real and imaginary...')
        real = funcscan.replace('part-mag', 'part-real')
        imag = funcscan.replace('part-mag', 'part-imag')
        complex = funcscan.replace('part-mag', 'part-complex')
        os.system(f'fslcomplex -complex {real} {imag} {complex}')

        # magnitude
        if not op.isfile(mag_calc):
            print('calculating magnitude from complex...')
            os.system(f'fslcomplex -realabs {complex} {mag_calc}')
            # retain the original geometry header info
            os.system(f'fslcpgeom {imag} {mag_calc}')

        # phase
        if not op.isfile(phase_calc):
            print('calculating phase from complex...')
            os.system(f'fslcomplex -realphase {complex} {phase_calc}')
            # retain the original geometry header info
            os.system(f'fslcpgeom {imag} {phase_calc}')

        # delete complex
        [os.remove(complex) for complex in glob.glob(f'{complex}*')]

    # run NORDIC preprocessing
    for mag_type, phase_type, noise_type in itp(
            ['meas', 'calc'], ['meas', 'calc'], ['vol', 'est']):

        nordic = f'NORDIC_mag-{mag_type}_phase-{phase_type}_noise-{noise_type}'
        out_dir = f'derivatives/{nordic}/{func_dir}'
        mag_cor = (f'{out_dir}/sub-{subject}_ses-{session}_task-restingState_'
                   f'part-mag_bold')
        if not op.isfile(mag_cor + '.nii'):

            print('running NORDIC preprocessing...')
            os.makedirs(out_dir, exist_ok=True)

            # copy mag image to output directory, remove noise volume if
            # necessary
            mag_srcs = glob.glob(
                f'{func_dir}/*acq-{mag_type}*part-mag_bold.nii*')
            assert len(mag_srcs) == 1, 'multiple/no candidates for mag image'
            mag_src = mag_srcs[0]
            mag_dst = f'{out_dir}/{os.path.basename(mag_src)}'
            if not op.isfile(mag_dst):
                shutil.copy(mag_src, mag_dst)
                if noise_type == 'est':
                    os.system(f'fslroi {mag_dst} {mag_dst} 0 -1')

            # copy phase image to output directory, remove noise volume if
            # necessary
            phase_srcs = glob.glob(
                f'{func_dir}/*acq-{phase_type}*part-phase_bold.nii*')
            assert len(phase_srcs) == 1, 'multiple/no candidates for phase image'
            phase_src = phase_srcs[0]
            phase_dst = f'{out_dir}/{os.path.basename(phase_src)}'
            if not op.isfile(phase_dst):
                shutil.copy(phase_src, phase_dst)
                if noise_type == 'est':
                    os.system(f'fslroi {phase_dst} {phase_dst} 0 30')

            arg = {'phase_filter_width': 10.}  # float. Default = 10.
            if noise_type == 'vol':
                arg['noise_volume_last'] = 1  # 1 = last, 0 = no noise
                arg['use_magn_for_gfactor'] = 1  # remove key to disable
            else:
                arg['noise_volume_last'] = 0
            eng = matlab.engine.start_matlab()
            eng.addpath('/home/tonglab/david/repos/NORDIC_Raw')
            eng.NIFTI_NORDIC(mag_dst, phase_dst, mag_cor, arg, nargout=0)
            eng.quit()

        # trim mag and NORDIC data and change TR in header
        num_func_vols = int(os.popen(f'fslnvols {mag_cor}').read()[0:-1])
        if num_func_vols == 31:
            print(f'trimming noise volume from preprocessed timeseries...')
            os.system(f'fslroi {mag_cor} {mag_cor} 0 30')

            # delete original nifti
            os.remove(mag_cor + '.nii')

            # change TR in header (creates gzipped nifti)
            os.system(f'fslmerge -tr {mag_cor} {mag_cor} 4.217')

            # unzip the new nifti
            with gzip.open(mag_cor + '.nii.gz', 'rb') as f_in:
                with open(mag_cor + '.nii', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # delete the gzipped nifti and original mag + phase images
            os.remove(mag_cor + '.nii.gz')
            [os.remove(i) for i in glob.glob(op.join(out_dir, '*_acq-*'))]

        # copy json files
        json_srcs = glob.glob(f'{session_dir}/func/'
                              f'*restingState*part-mag_bold.json')
        for json_src in json_srcs:
            json_dst = f'derivatives/{nordic}/{json_src.replace("_run-1", "")}'
            if not op.isfile(json_dst):
                shutil.copy(json_src, json_dst)

        # make links to anat and fmap data
        anat_dst = f'{op.dirname(out_dir)}/anat'
        if not op.isdir(anat_dst):
            os.system(f'ln -s {op.abspath(anat_dir)} {anat_dst}')
        fmap_dst = f'{op.dirname(out_dir)}/fmap'
        if not op.isdir(fmap_dst):
            os.system(f'ln -s {op.abspath(fmap_dir)} {fmap_dst}')

        # copy other files to statisfy bids requirements
        for src in ['dataset_description.json', 'participants.json', 'README']:
            if not op.isfile(f'derivatives/{nordic}/{src}'):
                shutil.copy(src, f'derivatives/{nordic}/{src}')

        # delete imaginary, real, and phase images
        for cpnt in ['real', 'imag', 'phase']:
            for path in glob.glob(f'{func_dir}/*part-{cpnt}*'):
                os.remove(path)


if __name__ == "__main__":
    test_NORDIC('M001')