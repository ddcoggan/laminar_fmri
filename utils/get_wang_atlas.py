import os
import os.path as op
import glob
import json

def get_wang_atlas(subject):

    """
    Obtain the probabilistic atlas of retinotopic regions from Wang et al.
    2015 using Noah Benson's neuropythy package. It will also convert the
    atlas to individual surface labels and volumetric ROIs in the original
    anatomical space. This function requires docker, configured to run
    without super-user permissions, as installing neuropythy natively causes
    dependency conflicts with other scripts. Before running, ensure docker
    has permissions to write to their freesurfer subjects directory. The
    surest/easiest way to do this is to change permissions of the freesurfer
    subjects directory to allow all users to read and write, including
    sub-files/folders.
    """

    fs_dir = os.getenv('SUBJECTS_DIR')
    neuropythy_params = {"freesurfer_subject_paths": fs_dir,
                         "data_cache_root": "~/Temp/npythy_cache",
                         "hcp_subject_paths": "/Volumes/server/Projects/HCP/subjects",
                         "hcp_auto_download": True,
                         "hcp_credentials": "~/.hcp-passwd"}
    npythyrc_path = f'{fs_dir}/.npythyrc'
    if not op.isfile(npythyrc_path):
        json.dump(neuropythy_params, open(npythyrc_path, 'w+'))

    roiname_array = (
    "V1v", "V1d", "V2v", "V2d", "V3v", "V3d", "hV4", "VO1", "VO2",
    "PHC1", "PHC2", "TO2", "TO1", "LO2", "LO1", "V3B", "V3A",
    "IPS0", "IPS1", "IPS2", "IPS3", "IPS4", "IPS5", "SPL1", "FEF")

    # Get atlas as mgz
    if len(glob.glob(f"{fs_dir}/{subject}/surf/??.wang15_mplbl.mgz")) < 2:
        os.system(f'docker run --rm '
                  f'--mount type=bind,src={fs_dir},dst=/subjects '
                  f'--env "NPYTHYRC=/subjects/.npythyrc" '
                  f'nben/neuropythy '
                  f'atlas --verbose {subject}')

    for hemi in ['lh', 'rh']:

        # label for all regions combined
        mgz = f"{fs_dir}/{subject}/surf/{hemi}.wang15_mplbl.mgz"
        label = f"{fs_dir}/{subject}/label/{hemi}.wang15_mplbl.label"
        if not op.isfile(label):
            os.system(f"mri_cor2label "
                      f"--i {mgz} "
                      f"--stat "
                      f"--l {label} "
                      f"--surf {subject} {hemi}")

        # separate files for each region
        for r, roiname in enumerate(roiname_array):

            # label
            label = f"{fs_dir}/{subject}/label/{hemi}.wang15_mplbl.{roiname}.label"
            if not op.isfile(label):
                os.system(
                    f"mri_cor2label "
                    f"--i {mgz} "
                    f"--id {r + 1} "
                    f"--l {label} "
                    f"--surf {subject} {hemi}")

            # nifti with filled cortical ribbon
            nifti = (f"{fs_dir}/{subject}/mri/{hemi}.wang15_mplbl."
                     f"{roiname}.nii.gz")
            if not op.isfile(nifti):
                os.system(
                    f"mri_label2vol "
                    f"--label {label} "
                    f"--temp {fs_dir}/{subject}/mri/orig.mgz "
                    f"--o {nifti} "
                    f"--fill-ribbon "
                    f"--regheader {fs_dir}/{subject}/mri/orig.mgz "
                    f"--subject {subject} "
                    f"--hemi {hemi}")

if __name__ == "__main__":
    get_wang_atlas(f'sub-F019_mprage')
