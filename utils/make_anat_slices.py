import nibabel as nib
import os
from tqdm import tqdm

def make_anat_slices(subject, T1, outdir=None, slice_interval=4):

    print(f'creating anatomical images for subject {subject}')
    if outdir is None:
        outdir = f'/home/tonglab/david/subjects/for_subjects/{subject}/2D'
    os.makedirs(outdir, exist_ok=True)

    # get dimensions of image
    T1info = os.popen(f"fslinfo {T1}").readlines()[1:4]
    T1Shape = [int(x.split('\t')[2]) for x in T1info]

    print(f'getting sagittal slices\n')
    for x in tqdm(range(T1Shape[0])):
        if x % slice_interval == 0:
            os.system(f'slicer {T1} -x -{x} {outdir}/X_{x}.png')

    print(f'\ngetting coronal slices\n')
    for y in tqdm(range(T1Shape[1])):
        if y % slice_interval == 0:
            os.system(f'slicer {T1} -y -{y} {outdir}/Y_{y}.png')

    print(f'\ngetting axial slices\n')
    for z in tqdm(range(T1Shape[2])):
        if z % slice_interval == 0:
            os.system(f'slicer {T1} -z -{z} {outdir}/Z_{z}.png')

