# /usr/bin/python
# Created by David Coggan on 2022 10 11

import os
import sys
import os.path as op
import glob
import datetime
import pandas as pd
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt

sys.path.append(f'{os.path.expanduser("~")}/david/masterScripts/fMRI')
from makeFloodFillMasks import makeFloodFillMasks

def ROIsFloodFill(experiment, regions, sizes, Zthr, overwrite):

    dataDir = experiment['general']['dataDir']
    MNI2mm = '/usr/local/fsl/data/standard/MNI152_2mm.nii.gz'
    outData = f"{dataDir}/group/maskStatsFloodFill.pkl"
    data = pd.DataFrame({'subject': [],
                         'session': [],
                         'region': [],
                         'regType': [],
                         'peakX': [],
                         'peakY': [],
                         'peakZ': [],
                         'sizeTarget': [],
                         'sizeFinal': [],
                         'minZ': []})

    for subject in experiment['sessInfo']:

        fsDir = sorted(glob.glob(f'{os.path.expanduser("~")}/david/freesurferSubjects/{subject}*'))[-1]
        subjectFS = os.path.basename(fsDir)
        T1hr = f"{fsDir}/mri/orig/T1HighRes1mm.nii"

        for session in experiment['sessInfo'][subject]:

            sessDir = f'{dataDir}/individual/{subject}/{session}'
            xformDir = f'{sessDir}/reg/transforms'
            regDirs = glob.glob(f"{sessDir}/reg/func*")

            actScan = "figureGround_v5_loc"
            actContrast = 1
            actPreproc = experiment['design'][actScan]['params']['preproc']
            actRegType = experiment['design'][actScan]['params']['regType']
            actRegDir = f"{sessDir}/reg/{actRegType}"
            actMapOrig = f"{sessDir}/functional/{actScan}/allRuns/magnitude_{actPreproc}/secondLevel.gfeat/cope{actContrast}.feat/stats/zstat1.nii.gz"

            # make localiser activation map in each reg dir then floodfill each ROI
            for regDir in regDirs:

                regType = os.path.basename(regDir)
                refFunc = f"{regDir}/refFunc.nii.gz"
                floodFillDir = f"{regDir}/masks/floodfill/{actScan}"
                os.makedirs(floodFillDir, exist_ok=True)
                plotDir = f"{floodFillDir}/plots"
                os.makedirs(plotDir, exist_ok=True)

                # if same reg, make link to activation map
                if regType == actRegType:
                    os.system(f"ln -s {actMapOrig} {actMap}")  # make link
                else:

                    # ensure a transformation exists
                    regFile = glob.glob(f"{xformDir}/{actRegType}_to_{regType}.lta")
                    if not op.exists(regFile) or overwrite:
                        refFunc = f"{regDir}/refFunc.nii.gz"
                        actRefFunc = f"{actRegDir}/refFunc.nii.gz"
                        os.system(f'bbregister --s {subjectFS} --mov {actRefFunc} --targ {refFunc} --reg {regFile} --bold')

                    # transform activation map to func space or make link if same space
                    actMap = f"{floodFillDir}/activationMap.nii.gz"
                    if not op.isfile(actMap) or overwrite:
                        os.system(f'mri_vol2vol --lta {regFile} --mov {actMapOrig} --targ {refFunc} --o {actMap} --trilinear')

                # floodfill masks
                for region in regions:

                    maskFuncCortex = f'{regDir}/masks/{region}_cortex.nii.gz' # created by ROIsTransformVols.py

                    # get location of peak activation
                    coords = os.popen(f'fslstats {actMap} -k {maskFuncCortex} -x')
                    coords = coords.read()[:-2]

                    print(f'{datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")} | Making FloodFilled ROIs | '
                          f'Subject: {subject} | Session: {session} | RegType: {regType} | Region: {region} |')
                    actualNvoxs, actualVols, xopts = makeFloodFillMasks(actMap, sizes, coords, Zthr, region, refFunc, floodFillDir, maskFuncCortex)

                    data = pd.concat([data, pd.DataFrame({'subject': [subject] * len(sizes),
                                                          'session': [session] * len(sizes),
                                                          'region': [region] * len(sizes),
                                                          'regType': [regType] * len(sizes),
                                                          'peakX': [coords[0]] * len(sizes),
                                                          'peakY': [coords[1]] * len(sizes),
                                                          'peakZ': [coords[2]] * len(sizes),
                                                          'volTarget': [sizes],
                                                          'volAttained': [actualVols],
                                                          'nVoxFinal': [actualNvoxs],
                                                          'minZ': [xopts]})])

if __name__ == "__main__":
    from v7.analysis.scripts.experiment import experiment
    regions = ['V1_lh', 'V1_rh']
    sizes = [32,128,512] # in mm3
    Zthr = 3.1
    overwrite=False
    ROIsFloodFill(experiment, regions, sizes, Zthr, overwrite)



