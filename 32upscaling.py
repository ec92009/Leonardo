import argparse  # https://docs.python.org/3/library/argparse.html

import os           # https://docs.python.org/3/library/os.html
# pip install opencv-python
import shutil   # https://docs.python.org/3/library/shutil.html
# pip install opencv-python
import subprocess   # https://docs.python.org/3/library/subprocess.html
# pip install opencv-python
from PIL import Image   # https://pillow.readthedocs.io/en/stable/
# pip install Pillow
import numpy as np    # https://numpy.org/
# pip   install numpy
# https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html
from sklearn.cluster import KMeans
# pip install -U scikit-learn
from psd_tools import PSDImage      # https://psd-tools.readthedocs.io/en/latest/
# https://pypi.org/project/psd-tools/
# pip install psd-tools
import traceback  # https://docs.python.org/3/library/traceback.html


from iptcinfo3 import IPTCInfo
from sklearn.cluster import KMeans
from psd_tools import PSDImage      # https://psd-tools.readthedocs.io/en/latest/
from EC_utils import add_iptc_metadata_to_image, get_iptc_data_from_image, detect_faces


def one_pass():
    total_files = 0

    # Loop through all files in the current folder in alphabetical order
    for basename in sorted(os.listdir(src_dir)):
        if basename.endswith(('.jpg', '.jpeg', '.png', '.webp')):
            total_files += 1
            src_path = os.path.join(src_dir, basename)
            upscale_one_picture(src_path)

    print(f'Total files: {total_files}')


def upscale_one_picture(src_path):
    basename = os.path.basename(src_path)
    src_dir = os.path.dirname(src_path)
    dst_dir = f'{src_dir}/Scaled'
    face_dir = f'{src_dir}/Faces'
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    if not os.path.exists(face_dir):
        os.makedirs(face_dir)
    # collect title and keywords from the image
    iptc_title, iptc_keywords = get_iptc_data_from_image(src_path)

    try:
        # Open the image
        with Image.open(src_path) as img:
            width, height = img.size
            ratioMP = max_size / (width * height)
            ratio = int(np.sqrt(ratioMP))
            ratio = int(min(4, ratio))

            if ratio >= 2:
                # print(f'ratio = {ratio}')
                dest_path = os.path.join(dst_dir, f"{basename}x{ratio}.jpg")
                face_path = os.path.join(face_dir, f"{basename}x{ratio}.jpg")

                # if the destination file does not exists, skip it
                if not os.path.exists(dest_path) and not os.path.exists(face_path):
                    print(
                        f"scaling {ratio}x from {width}x{height} to {width*ratio}x{height*ratio} ie. {width*ratio*height*ratio/1_000_000} Mpixels")
                    command = f'./realesrgan-ncnn-vulkan -i "{src_path}" -o "{dest_path}" -s {ratio}'
                    _ = subprocess.run(command, shell=True,
                                       capture_output=True, text=True)
                    add_iptc_metadata_to_image(
                        dest_path, iptc_title, iptc_keywords)
                    face_found = detect_faces(dest_path)
                else:
                    print(f'Upscaled version already exists, skipping')
                    if os.path.exists(dest_path):
                        face_found = detect_faces(dest_path)
                    else:
                        face_found = detect_faces(face_path)

            else:
                # if the file is too large to resize, say so and take it out of the way
                print(
                    f'current size: {width}x{height} too big to resize')
                dest_path = os.path.join(
                    dst_dir, f"{basename}.jpg")

                shutil.copyfile(src_path, dest_path)
                face_found = detect_faces(dest_path)

            if face_found:
                face_path = os.path.join(face_dir, os.path.basename(dest_path))
                if os.path.exists(dest_path):
                    os.replace(dest_path, face_path)

    except:
        traceback.print_exc()
        exit()


max_size = 25_000_000
src_dir = './1-From-Leonardo'

if __name__ == "__main__":
    # Create an argument parser
    parser = argparse.ArgumentParser(
        description='Upscales images from one folder to another, optionally separating images with faces')

    # Add an optional argument with a default value
    parser.add_argument('-i', '--inFolder', type=str, default=src_dir,
                        help=f'input folder, default: {src_dir}')
    parser.add_argument('-s', '--maxSize', type=int, default=max_size,
                        help=f'max picture size in pixels (height x width), default: {max_size} (ie. {int(max_size/1_000_000)} Mpixels)')

    # Parse the arguments
    args = parser.parse_args()

    # Access the value
    src_dir = args.inFolder
    max_size = args.maxSize

    print(f'scaling from {src_dir} with max size {max_size}')

    one_pass()
