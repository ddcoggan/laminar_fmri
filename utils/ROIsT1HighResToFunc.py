# /usr/bin/python
# Created by David Coggan on 2022 10 11

import os
import sys
import os.path as op
import glob
import datetime
import pandas as pd

def ROIsT1HighResToFunc(experiment, plotRegions, overwrite):

    dataDir = experiment['general']['dataDir']

    for subject in experiment['sessInfo']:

        fsSubjDir = os.popen('echo $SUBJECTS_DIR').read()[:-1]
        fsDir = sorted(glob.glob(f'{fsSubjDir}/{subject}*'))[-1]
        T1hr = f"{fsDir}/mri/T1HighRes.nii"

        for session in experiment['sessInfo'][subject]:

            sessDir = f'{dataDir}/individual/{subject}/{session}'
            xformDir = f'{sessDir}/reg/transforms'
            maskDirT1hr = f'{sessDir}/reg/T1HighRes/masks'

            # convert from high res into each reg type
            regDirs = glob.glob(f"{sessDir}/reg/funcHighRes*")

            for regDir in regDirs:

                regType = os.path.basename(regDir)
                maskDirFunc = f'{regDir}/masks'
                os.makedirs(maskDirFunc, exist_ok=True)
                refFunc = f"{regDir}/refFunc.nii.gz"

                for maskT1HighRes in glob.glob(f"{maskDirT1hr}/*.nii*"):

                    maskName = os.path.basename(maskT1HighRes)
                    print(f'{datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")} | Making ROIs T1HighRes | '
                          f'Subject: {subject} | Session: {session} | RegType: {regType} | Mask: {maskName}')

                    regFile = f"{xformDir}/{regType}_to_T1HighRes.lta"
                    maskFunc = f'{maskDirFunc}/{maskName}'

                    if not op.isfile(maskFunc) or overwrite:
                        os.system(f'mri_vol2vol --lta {regFile} --mov {refFunc} --targ {maskT1HighRes} --o {maskFunc} --nearest --inv')

                # convert localizer too
                actMapOrig = f"{sessDir}/functional/figureGround_v5_loc/allRuns/magnitude_topup.gfeat/cope1.feat/stats/zstat1.nii.gz"
                actMap = f"{regDir}/localizerActivationMap.nii.gz"
                regFile = f"{xformDir}/MNI2mm_to_{regType}.lta"
                if not os.path.isfile(actMap) or overwrite:
                    os.system(f'mri_vol2vol --lta {regFile} --mov {actMapOrig} --targ {refFunc} --o {actMap} --trilin')

                for region in plotRegions:
                    # make plot using FSLeyes
                    Zthr = 3.1
                    plotDir = f"{maskDirFunc}/plots"
                    os.makedirs(plotDir, exist_ok=True)
                    plotFile = f'{plotDir}/{region}.pdf'
                    cortex = f'{regDir}/masks/cortex.nii.gz'
                    cortexRegLoc = f'{regDir}/masks/{region}_cortex_thr{Zthr}.nii.gz'
                    superficial = f'{regDir}/masks/{region}_cortex_superficial_thr{Zthr}.nii.gz'
                    middle = f'{regDir}/masks/{region}_cortex_middle_thr{Zthr}.nii.gz'
                    deep = f'{regDir}/masks/{region}_cortex_deep_thr{Zthr}.nii.gz'
                    maxAct = float(os.popen(f'fslstats {actMap} -R').read().split()[1])
                    maxBrain = float(os.popen(f'fslstats {refFunc} -R').read().split()[1])
                    coords = os.popen(f'fslstats {actMap} -k {cortexRegLoc} -x').read()[:-2]
                    fsleyesCommand = f'fsleyes render --outfile {plotFile} --size 1600 600 --scene ortho ' \
                                     f'-vl {coords} -xz 2500 -yz 2500 -zz 2500 ' \
                                     f'{refFunc} -dr 0 {maxBrain} -cm greyscale ' \
                                     f'{actMap} -dr {Zthr} {maxAct} -cm red-yellow ' \
                                     f'{cortex} -dr 0 1 -a 50 -cm greens ' \
                                     f'{deep} -dr 0 8 -cm blue-lightblue ' \
                                     f'{middle} -dr 0 2 -cm blue-lightblue ' \
                                     f'{superficial} -dr 0 1 -cm blue-lightblue'
                    os.system(fsleyesCommand)


if __name__ == "__main__":
    from v7.analysis.scripts.experiment import experiment
    plotRegions = ['V1_lh', 'V1_rh']
    overwrite = True
    ROIsT1HighResToFunc(experiment, plotRegions, overwrite)



