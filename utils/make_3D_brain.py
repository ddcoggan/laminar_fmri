# /usr/bin/python
# Created by David Coggan on 2022 10 17
import os
from tqdm import tqdm
import argparse
import pymeshlab

parser = argparse.ArgumentParser()
parser.add_argument("subject", type=str,help="subject freesurfer ID")
args = parser.parse_args()
subject = args.subject

fsDir = f'/home/tonglab/david/subjects/freesurfer/{subject}'
outDir = f'/home/tonglab/david/subjects/for_subjects/{subject}/3D'
os.makedirs(outDir)
outFile = f'{outDir}/brain.stl'

os.system(f"mris_convert --combinesurfs {fsDir}/surf/lh.pial {fsDir}/surf/rh.pial {outDir}/cortical.stl")
os.system(f"mri_convert {fsDir}/mri/aseg.mgz {outDir}/subcortical.nii")

# mask excluding non cortical or cerebellar regions
os.system(f"mri_binarize --i {outDir}/subcortical.nii \
             --match 2 3 24 31 41 42 63 72 77 51 52 13 12 43 50 4 11 26 58 49 10 17 18 53 54 44 5 80 14 15 30 62 \
             --inv \
             --o {outDir}/bin.nii")
os.system(f"fslmaths {outDir}/subcortical.nii -mul {outDir}/bin.nii {outDir}/subcortical.nii.gz")

# make copy, unzip
os.system(f"cp {outDir}/subcortical.nii.gz {outDir}/subcortical_tmp.nii.gz")
os.system(f"gunzip -f {outDir}/subcortical_tmp.nii.gz")

# check all areas of interest for holes and fill them out if necessary
for i in [7, 8, 16, 28, 46, 47, 60, 251, 252, 253, 254, 255]:
    os.system(f"mri_pretess {outDir}/subcortical_tmp.nii {i} {fsDir}/mri/norm.mgz {outDir}/subcortical_tmp.nii")

# binarize the whole volume
os.system(f"fslmaths {outDir}/subcortical_tmp.nii -bin {outDir}/subcortical_bin.nii")

# create a surface model of the binarized volume with mri_tessellate
os.system(f"mri_tessellate {outDir}/subcortical_bin.nii.gz 1 {outDir}/subcortical")

# convert binary surface output into stl format
os.system(f"mris_convert {outDir}/subcortical {outDir}/subcortical.stl")

ms = pymeshlab.MeshSet()
ms.load_new_mesh(f"{outDir}/cortical.stl")
ms.load_new_mesh(f"{outDir}/subcortical.stl")
ms.generate_by_merging_visible_meshes(alsounreferenced=False)
ms.meshing_merge_close_vertices(threshold=pymeshlab.Percentage(2.4))
ms.apply_coord_laplacian_smoothing_scale_dependent(stepsmoothnum=100, delta=pymeshlab.Percentage(0.1))
ms.save_current_mesh(outFile)
