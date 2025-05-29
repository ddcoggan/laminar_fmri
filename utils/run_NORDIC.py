import os
import os.path as op
import datetime
import matlab.engine
import sys
import glob
import shutil

def run_NORDIC(subjects, noise_vol=True):

    for subject in subjects:
        for s, session in enumerate(subjects[subject]):
            funcdir = f"sub-{subject}/ses-{s + 1}/func"
            funcscans = sorted(glob.glob(f"sub-{subject}/ses-{s + 1}/func/"
                                        f"*part-mag_bold.nii"))

            for funcscan in funcscans:

                print(f'{datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")} | NORDIC preprocessing | '
                      f'Subject: {subject} | Session: {session} | Scan: '
                      f'{funcscan}')

                mag = funcscan.split('.nii')[0]
                phase = mag.replace('part-mag', 'part-phase')
                real = mag.replace('part-mag', 'part-real')
                imag = mag.replace('part-mag', 'part-imag')
                complex = mag.replace('part-mag', 'part-complex')

                # calculate phase
                if not len(glob.glob(f'{phase}*')):
                    # complex
                    print('calculating complex from real and imaginary...')
                    os.system(f'fslcomplex -complex {real} {imag} {complex}')

                    # phase
                    print('calculating phase from complex...')
                    os.system(f'fslcomplex -realphase {complex} {phase}')
                    os.system(f'fslcpgeom {imag} {phase}')  # get the original geometry header info back

                    # delete complex
                    [os.remove(complex) for complex in glob.glob(f'{complex}*')]

                # run NORDIC preprocessing
                outdir = f"derivatives/NORDIC/{funcdir}"
                os.makedirs(outdir, exist_ok=True)
                outpath = f'{outdir}/{os.path.basename(mag)}'
                if not len(glob.glob(f'{outpath}*')):
                    print('running NORDIC preprocessing...')
                    arg = {'phase_filter_width': 10.}  # float. Default = 10.
                    if noise_vol:
                        arg['noise_volume_last'] = 1  # 1 = last, 0 = no noise
                        arg['use_magn_for_gfactor'] = 1  # remove key to disable
                    else:
                        arg['noise_volume_last'] = 0
                    eng = matlab.engine.start_matlab()
                    eng.addpath('/home/tonglab/david/repos/NORDIC_Raw')
                    eng.NIFTI_NORDIC(mag, phase, outpath, arg, nargout=0)
                    eng.quit()

                    # trim mag and NORDIC data and change TR in header
                    num_func_vols = int(os.popen(f'fslnvols {mag}').read()[0:-1])
                    print(f'trimming noise volume from preprocessed timeseries...')
                    os.system(f'fslroi {outpath} {outpath} 0 {num_func_vols - 1}')
                    os.remove(f'{outpath}.nii')
                    os.system(f'fslmerge -tr {outpath} {outpath} 4.217')

            # copy json files
            json_paths = glob.glob(f"sub-{subject}/ses-"
                              f"{s + 1}/func/*part-mag_bold.json")
            for json_path in json_paths:
                if not op.isfile(f"derivatives/NORDIC/{json_path}"):
                    shutil.copy(json_path, f"derivatives/NORDIC/{json_path}")

            # make links to anat and fmap data
            otherdirs = glob.glob(f"sub-{subject}/ses-{s + 1}/anat")
            otherdirs += glob.glob(f"sub-{subject}/ses-{s + 1}/fmap")
            for otherdir in otherdirs:
                outdir = f"derivatives/NORDIC/{otherdir}"
                if not op.exists(outdir):
                    os.system(f"ln -s {op.abspath(otherdir)} {outdir}")

            # copy other files to statisfy bids requirements
            for file_path in [
                'dataset_description.json', 'participants.json', 'README']:
                if not op.isfile(f"derivatives/NORDIC/{file_path}"):
                    shutil.copy(file_path, f"derivatives/NORDIC/{file_path}")


if __name__ == "__main__":
    run_NORDIC('M015')

