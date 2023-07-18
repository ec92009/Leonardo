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
    resized_files = 0
    untouched_files = 0

    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    if not os.path.exists(face_folder):
        os.makedirs(face_folder)
    # Loop through all files in the current folder in alphabetical order
    for filename in sorted(os.listdir(src_dir)):
        if filename.endswith('.jpg') or filename.endswith('.jpeg') or filename.endswith('.png') or filename.endswith('.webp'):
            total_files += 1
            upscale_one_picture(total_files, resized_files,
                                untouched_files, filename)

    print(
        f'Total files: {total_files}, processed: {resized_files}, untouched: {untouched_files}')


def upscale_one_picture(total_files, resized_files, untouched_files, filename):
    src_name = os.path.join(src_dir, filename)
    # collect title and keywords from the image
    iptc_title, iptc_keywords = get_iptc_data_from_image(src_name)
    basename, _ = os.path.splitext(filename)

    try:
        # Open the image
        with Image.open(src_name) as img:
            width, height = img.size

            # ratioMP is the ratio of the image in megapixels
            ratioMP = max_size / (width * height)
            # ratio is the square root of the ratioMP
            ratio = int(np.sqrt(ratioMP))
            # ratio is between 2 and 4
            ratio = int(min(4, ratio))

            if ratio >= 2:
                # print(f'ratio = {ratio}')
                resized_filename = os.path.join(
                    dst_dir, f"{basename}x{ratio}.jpg")

                # print(f'ratio = {ratio}')
                print(
                    f"{total_files} -> scaling {ratio}x from {width}x{height} to {width*ratio}x{height*ratio} ie. {width*ratio*height*ratio/1_000_000} Mpixels")

                command = f'./realesrgan-ncnn-vulkan -i "{src_name}" -o "{resized_filename}" -s {ratio}'
                # print(f'command = {command}')
                completed_process = subprocess.run(
                    command, shell=True, capture_output=True, text=True)
                resized_files += 1
                os.remove(src_name)
                add_iptc_metadata_to_image(
                    resized_filename, iptc_title, iptc_keywords)

            else:
                # if the file is too large to resize, say so and take it out of the way
                resized_filename = os.path.join(
                    dst_dir, f"{basename}.jpg")
                print(
                    f'current size: {width}x{height} too big to resize')
                untouched_files += 1
                shutil.copyfile(src_name, resized_filename)
                try:
                    shutil.move(src_name, dst_dir)
                except:
                    # delete the file if it can't be moved
                    os.remove(src_name)
                    pass

            face_found = detect_faces(resized_filename)
            if face_found:
                shutil.move(resized_filename, face_folder)

    except:
        traceback.print_exc()
        exit()


max_size = 45_000_000
src_dir = './1-From-Leonardo'
dst_dir = './2-Scaled'
face_folder = './3-Faces'

if __name__ == "__main__":
    # Create an argument parser
    parser = argparse.ArgumentParser(
        description='Upscales images from one folder to another, optionally separating images with faces')

    # Add an optional argument with a default value
    parser.add_argument('-i', '--inFolder', type=str, default='./1-From-Leonardo',
                        help='input folder, default: ./1-From-Leonardo')
    parser.add_argument('-o', '--outFolder', type=str, default='./2-Scaled',
                        help='output folder, default: ./2-Scaled')
    parser.add_argument('-f', '--facesFolder', type=str, default='./3-Faces',
                        help='output folder for images containing faces, default: ./3-Faces')
    parser.add_argument('-s', '--maxSize', type=int, default=45_000_000,
                        help='max picture size in pixels (height x width), default: 45_000_000 (ie. 45 Mpixels)')

    # Parse the arguments
    args = parser.parse_args()

    # Access the value
    src_dir = args.inFolder
    dst_dir = args.outFolder
    face_folder = args.facesFolder
    max_size = args.maxSize

    print(f'scaling from {src_dir} to {dst_dir} with max size {max_size}')

    one_pass()
