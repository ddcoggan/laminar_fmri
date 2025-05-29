#!/usr/bin/python
# Created by David Coggan on 2022 10 11

import numpy as np
import nibabel as nib
import os
import matplotlib.pyplot as plt
import pandas as pd
from tabulate import tabulate
import datetime
import sys
import os.path as op
import glob
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

sys.path.append(op.expanduser('~/david/master_scripts/misc'))
from plot_utils import export_legend, custom_defaults
plt.rcParams.update(custom_defaults)

def measure_TSNR(overwrite):
    

    subject = 'M001'
    roi_dir = f'derivatives/ROIs/sub-{subject}'
    os.makedirs(roi_dir, exist_ok=True)
    tsnr_dir = f'derivatives/tSNR'
    preproc_dirs = ['sub-M001/ses-1/func'] * 2
    preproc_dirs += [d for d in sorted(glob.glob('derivatives/**/ses-1/func',
                                    recursive=True)) if 'mriqc' not in d]


    tsnr_path = f'{tsnr_dir}/tSNR_V1.csv'
    if not op.isfile(tsnr_path) or overwrite:
        df = pd.DataFrame()
        preprocs = []
        for pp, preproc_dir in enumerate(preproc_dirs):

            if pp == 0:
                preproc = 'raw_data_meas'
                timeseries_orig = glob.glob(
                    f'{preproc_dir}/*restingState*acq-meas*part-mag_bold.nii')
            elif pp == 1:
                preproc = 'raw_data_calc'
                timeseries_orig = glob.glob(
                    f'{preproc_dir}/*restingState*acq-calc*part-mag_bold.nii*')
            else:
                preproc = preproc_dir.split('/')[1]
                timeseries_orig = glob.glob(f'{preproc_dir}/*restingState*bold.nii')
            assert(len(timeseries_orig) == 1)
            timeseries_orig = timeseries_orig[0]
            preprocs.append(preproc)

            out_dir = f'{tsnr_dir}/{preproc}'
            os.makedirs(out_dir, exist_ok=True)

            # link to raw data
            if not os.path.exists(f'{out_dir}/{op.basename(timeseries_orig)}'):
                os.system(f'ln -s {op.abspath(timeseries_orig)} {out_dir}')
            timeseries = f'{out_dir}/{op.basename(timeseries_orig)}'

            # other preprocessing: motion correction
            timeseries_mc = (f'{timeseries.split(".")[0]}_motcor.nii.gz')
            if not os.path.exists(timeseries_mc) or overwrite:
                os.system(f'mcflirt -in {timeseries} -out {timeseries_mc}')

            # other preprocessing: linear trend removal aka temporal filtering in this case
            timeseries_mc_ltr = f'{timeseries_mc.split(".")[0]}_ltr.nii.gz'
            if not os.path.exists(timeseries_mc_ltr) or overwrite:
                # get Tmean so it can be added back afterward
                timeseries_mc_Tmean = f'{timeseries_mc[:-7]}_Tmean.nii.gz'
                os.system(
                    f'fslmaths {timeseries_mc} -Tmean {timeseries_mc_Tmean}')

                os.system(
                    f'fslmaths {timeseries_mc} -bptf 15 -1 '
                    f'-add {timeseries_mc_Tmean} {timeseries_mc_ltr}')


            for p, (postproc, ts) in enumerate(zip(
                    ['no further processing',
                     'after motion correction',
                     'after motion correction and linear trend removal'],
                    [timeseries, timeseries_mc, timeseries_mc_ltr])):

                # calculate tSNR if not done already
                pathTmean = f"{ts.split('.nii')[0]}_Tmean.nii.gz"
                pathTstd = f"{ts.split('.nii')[0]}_Tstd.nii.gz"
                pathTSNR = f"{ts.split('.nii')[0]}_tSNR.nii.gz"
                if not os.path.exists(pathTmean) or overwrite:
                    print('Creating mean of timeseries...')
                    os.system(f'fslmaths {ts} -Tmean {pathTmean}')
                if not os.path.exists(pathTstd) or overwrite:
                    print('Creating std of timeseries...')
                    os.system(f'fslmaths {ts} -Tstd {pathTstd}')
                if not os.path.exists(pathTSNR) or overwrite:
                    print('Calculating tSNR map...')
                    os.system(f'fslmaths {pathTmean} -div {pathTstd} {pathTSNR}')


                # get tSNR values
                mask = f'{roi_dir}/V1_cortex.nii.gz'
                tSNR_mean = float(os.popen(f'fslstats {pathTSNR} -k {mask} -m').read())
                tSNR_std = float(os.popen(f'fslstats {pathTSNR} -k {mask} -s').read())

                # store data
                df = pd.concat([df, pd.DataFrame({
                    'preproc': [preproc],
                    'postproc': [postproc],
                    'mean': [tSNR_mean],
                    'std': [tSNR_std]})])

        df.to_csv(f'{tsnr_dir}/tSNR_V1.csv', index=False)
    else:
        df = pd.read_csv(tsnr_path)
        preprocs = df.preproc.unique()

    # plots across scans and preprocessing
    fig, axes = plt.subplots(3, 1, figsize=(7, 7), sharex=True)
    for a, (pp, postproc) in enumerate(zip(
            ['none', 'mc', 'mc_ltr'],
            ['no further processing',
             'after motion correction',
             'after motion correction and linear trend removal'])):

        ax = axes[a]
        colors = list(mcolors.TABLEAU_COLORS)
        for p, preproc in enumerate(df.preproc.unique()):
            value = df['mean'][
                (df['postproc'] == postproc) &
                (df['preproc'] == preproc)]
            error = df['std'][
                (df['postproc'] == postproc) &
                (df['preproc'] == preproc)]
            ax.bar(p, value, yerr=error, color=colors[p])
        if a == 2:
            ax.set_xticks(range(len(preprocs)),
                       labels=preprocs,
                       ha="right", rotation=25)
        ax.set_ylim((0, 64))
        if a == 1:
            ax.set_ylabel('tSNR')
        ax.set_title(postproc)
    plt.tight_layout()
    plt.savefig(f'{tsnr_dir}/tSNR_V1.pdf')
    plt.show()
    plt.close()

    # legend
    outpath = f'{tsnr_dir}/legend.pdf'
    if not os.path.isfile(outpath) or overwrite:
        f = lambda m, c: \
            plt.plot([], [], marker=m, color=c, linestyle="None")[0]
        handles = [f('s', color) for color in colors]
        legend = plt.legend(handles, preprocs, loc=3)
        export_legend(legend, filename=outpath)

    # viewable text version of table
    txt_path = os.path.join(tsnr_dir, 'tSNR_V1.txt')
    with open(txt_path, 'w+') as c:
        c.write(tabulate(df))

        """
        # make histogram of tSNR values in cortical mask
        pathTSNR = f'{tsnr_dir}/tSNR.nii.gz'
        corticalMask = f'{reg_dir}/masks/cortex.nii.gz'
        max = float(os.popen(f'fslstats {pathTSNR} -k {corticalMask} -p 32').read())
        min = float(os.popen(f'fslstats {pathTSNR} -k {corticalMask} -p 0').read())
        histData = [float(x) for x in os.popen(f'fslstats {pathTSNR} -k {corticalMask} -H 32 {min} {max}').read().split()]
        x_pos = np.linspace(min, max, 32)
        fig, ax = plt.subplots(figsize=(4,4))
        ax.bar(x_pos, histData)#, width=(max-min)/32)
        #plt.xlim(tSNRlims)
        #plt.ylim(8000)
        ax.set_title(f'tSNR in cortex')
        plt.xlabel('tSNR')
        plt.ylabel('voxel count')
        ax.yaxis.grid(True)
        plt.tight_layout()
        plt.savefig(f'{plot_dir}/tSNR_hist.pdf')
        plt.show()
        plt.close()
    
        # make histogram of mean MR intensity values in cortical mask
        pathTmean = os.path.join(tsnr_dir, 'Tmean.nii.gz')
        max = float(os.popen(f'fslstats {pathTmean} -k {corticalMask} -p 32').read())
        min = float(os.popen(f'fslstats {pathTmean} -k {corticalMask} -p 0').read())
        histData = [float(x) for x in os.popen(f'fslstats {pathTmean} -k {corticalMask} -H 32 {min} {max}').read().split()]
        x_pos = np.linspace(min, max, 32)
        fig, ax = plt.subplots(figsize=(4,4))
        ax.bar(x_pos, histData)#, width=(max-min)/32)
        ax.set_title(f'MR intensity in cortex\n(preprocessing: {preproc})')
        plt.xlabel('MR intensity')
        plt.ylabel('voxel count')
        ax.yaxis.grid(True)
        #plt.xlim(MRlims)
        #plt.ylim(8000)
        plt.tight_layout()
        plt.savefig(f'{plot_dir}/MRintensity_hist.pdf')
        plt.show()
        plt.close()
    
        # make scatterplot of tSNR values and signal intensity values in cortical mask
    
        # apply cortical mask
        pathTSNRcortex = os.path.join(tsnr_dir, 'tSNR_cortex.nii.gz')
        pathTmeanCortex = f'{tsnr_dir}/Tmean_cortex.nii.gz'
        os.system(f'fslmaths {pathTSNR} -mul {corticalMask} {pathTSNRcortex}')
        os.system(f'fslmaths {pathTmean} -mul {corticalMask} {pathTmeanCortex}')
    
        # load masked data
        dataTmean = nib.load(pathTmeanCortex).get_fdata().flatten()
        dataTmean = np.ma.masked_where(dataTmean == 0 , dataTmean)
        dataTSNR = nib.load(pathTSNRcortex).get_fdata().flatten()
        dataTSNR = np.ma.masked_where(dataTmean == 0, dataTSNR)
        rVal = np.corrcoef(dataTSNR, dataTmean)[0,1]
    
        # plot
        fig, ax = plt.subplots(figsize=(4,4))
        ax.scatter(dataTmean, dataTSNR, s=.01)
        ax.set_title(f'tSNR v MRintensity, R = {rVal:.2f}')
        plt.xlabel('MR intensity')
        plt.ylabel('tSNR')
        #plt.xlim(MRlims)
        #plt.ylim(tSNRlims)
        plt.tight_layout()
        plt.savefig(f'{plot_dir}/tSNR_v_MRint.pdf')
        plt.show()
        plt.close()
        """

if __name__ == "__main__":

    overwrite = True
    measure_TSNR(overwrite)

