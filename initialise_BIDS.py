# /usr/bin/python
# Created by David Coggan on 2022 11 02
"""
prepares directory structure and extracts/copies raw data from sourcedata
For future projects, try to use dcm2bids (https://andysbrainbook.readthedocs.io/en/latest/OpenScience/OS/BIDS_Overview.html)
"""

import os
import os.path as op
import sys
import glob
import shutil
import json
import time
from .seconds_to_text import seconds_to_text
from .philips_slice_timing import philips_slice_timing
from .make_anat_slices import make_anat_slices


def initialise_BIDS():

    print(f"Initializing BIDS...")
    subjects = json.load(open("participants.json", "r+"))
    
    for subject in subjects:

        for s, session in enumerate(subjects[subject]):

            filetypes = ["nii","json"] # do not include other filetypes that may cause BIDS errors
            sourcedir = f"sourcedata/sub-{subject}/ses-{s+1}/raw_data"
            sessID = subjects[subject][session]["sessID"]

            # detect DICOM or NIFTI format for raw data
            if len(glob.glob(f"{sourcedir}/*.DCM")): # if DICOM format
                os.system(f"dcm2niix {op.abspath(sourcedir)}") # convert to nifti, json etc
                copy_or_move = shutil.move # move files, don't copy
            else: # if NIFTI format
                copy_or_move = shutil.copy # copy files, don't move


            ### ANAT ###

            anatscan = subjects[subject][session]["anat"]
            if anatscan is not None:

                anat_ses = s+1
                anatdir = f"sub-{subject}/ses-{anat_ses}/anat"
                os.makedirs(anatdir, exist_ok=True)

                # json file
                files = glob.glob(f"{sourcedir}/*{sessID}.{anatscan:02}*.json")
                assert len(files) == 1
                inpath = files[0]
                outpath = f"{anatdir}/sub-{subject}_ses-{s+1}_T1w.json"
                if not op.isfile(outpath):
                    copy_or_move(inpath, outpath)

                # nii file
                files = glob.glob(f"{sourcedir}/*{sessID}.{anatscan:02}*.nii")
                assert len(files) == 1
                inpath = files[0]

                # deidentify anatomical image
                outpath = f"{anatdir}/sub-{subject}_ses-{anat_ses}_T1w.nii"
                if not op.isfile(outpath):
                    os.system(f'mideface --i {inpath} --o {outpath}')

            # make T1 images for subject
            slice_dir = op.expanduser(
                f'~/david/subjects/for_subjects/sub-{subject}/2D')
            if not op.isdir(slice_dir):
                make_anat_slices(f'sub-{subject}', inpath, slice_dir)


            ### FUNC ###

            funcdir = f"sub-{subject}/ses-{s + 1}/func"
            os.makedirs(funcdir, exist_ok=True)
            fmapdir = f"sub-{subject}/ses-{s + 1}/fmap"
            os.makedirs(fmapdir, exist_ok=True)
            for funcscan, runs in subjects[subject][session]["func"].items():
                for run, scan_num in enumerate(runs):

                    # copy/move over nii and json files from sourcedata
                    for cpnt, cpnt_label in zip(
                            ['01', '01_real', '01_imaginary', '01_ph'],
                            ['mag', 'real', 'imag', 'phase']):
                        for filetype in filetypes:
                            files = glob.glob(f"{sourcedir}/*{sessID}."
                                          f"{scan_num:02}*{cpnt}.{filetype}")
                            if len(files):
                                inpath = files[0]
                                outpath = (f"{funcdir}/sub-{subject}_ses-" \
                                           f"{s + 1}_task-{funcscan}_run-" \
                                           f"{run + 1}_part-{cpnt_label}_bold"
                                           f".{filetype}")
                                if not op.isfile(outpath):
                                    copy_or_move(inpath, outpath)


                        # add required meta data to mag json file
                        jsonpath = (
                            f"{funcdir}/sub-{subject}_ses-{s + 1}"
                            f"_task-{funcscan}_run-{run + 1}_part-{cpnt_label}"
                            f"_bold.json")
                        scandata = json.load(open(jsonpath, "r+"))
                        if "TaskName" not in scandata:
                            scandata["TaskName"] = funcscan
                        #if "PhaseEncodingDirection" not in scandata:
                        #    scandata["PhaseEncodingDirection"] = "j-" #
                        if "SliceTiming" not in scandata:
                            scandata["SliceTiming"] = philips_slice_timing(jsonpath)
                        if "TotalReadoutTime" not in scandata:
                            scandata["TotalReadoutTime"] = scandata["EstimatedTotalReadoutTime"]
                        json.dump(scandata, open(jsonpath, "w+"),
                                  sort_keys=True, indent=4)


            ### FMAP ###

            # b0
            for c, component in enumerate(["magnitude", "fieldmap"]):

                # b0
                for c, component in enumerate(["magnitude", "fieldmap"]):
                    for filetype in filetypes:
                        files = glob.glob(
                            f"{sourcedir}/*{sessID}.{subjects[subject][session]['fmap']['b0']:02}*B0_shimmed*e{c + 1}*.{filetype}")
                        assert len(files) == 1
                        inpath = files[0]
                        outpath = f"{fmapdir}/sub-{subject}_ses-{s + 1}_acq-b0_{component}.{filetype}"
                        if not op.isfile(outpath):
                            copy_or_move(inpath, outpath)

                # add required meta data to json file
                jsonpath = f"{fmapdir}/sub-{subject}_ses-" \
                           f"{s + 1}_acq-b0_{component}.json"
                scandata = json.load(open(jsonpath, "r+"))
                if "IntendedFor" not in scandata:
                    intendedscans = glob.glob(f"sub-{subject}/ses-{s+1}/"
                                              f"anat/*.nii")
                    intendedscans += glob.glob(f"sub-{subject}/ses-{s+1}/"
                                               f"func/*part-mag_bold.nii")
                    scandata["IntendedFor"] = sorted([x[9:] for x in intendedscans])
                if component == "fieldmap" and "Units" not in scandata:
                    scandata["Units"] = "Hz"
                json.dump(scandata, open(jsonpath, "w+"), sort_keys=True, indent=4)




if __name__ == "__main__":

    start = time.time()
    initialise_BIDS()
    finish = time.time()
    print(f'analysis took {seconds_to_text(finish - start)} to complete')


