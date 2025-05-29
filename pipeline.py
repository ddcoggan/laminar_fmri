#!/usr/bin/python
"""
controller script for running the analysis pipeline
"""

import os
import os.path as op
import time
import sys
import glob
from utils import (
    seconds_to_text,
    initialise_BIDS,
    preprocess,
    registration,
    make_ROIs,
    measure_TSNR)

# get master scripts
for script in [
    'seconds_to_text', 'plot_utils', 'get_wang_atlas', 'run_NORDIC',
    'apply_topup', 'philips_slice_timing', 'make_anat_slices', 'make_3D_brain']:
    dst = f'utils/{script}.py'
    if not op.exists(dst):
        srcs = glob.glob(op.expanduser(f'~/david/master_scripts/*/{script}.py'))
        assert len(srcs) == 1
        src = srcs[0]
        os.system(f'ln -s {src} {dst}')


if __name__ == "__main__":

    os.chdir('../data/v10')
    #time.sleep(10000)
    n_procs = 8
    start = time.time()
    """
    initialise_BIDS()

    preprocess(n_procs)

    registration(overwrite=[])

    make_ROIs(overwrite=False)
    """
    measure_TSNR(overwrite=False)

    finish = time.time()
    print(f'analysis took {seconds_to_text(finish - start)} to complete')

