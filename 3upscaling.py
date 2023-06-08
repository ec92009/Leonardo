import argparse
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
from EC_utils import add_iptc_metadata_to_image, get_iptc_data_from_image


def one_pass():
    total_files = 0
    resized_files = 0
    untouched_files = 0

    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    # Loop through all files in the current folder in alphabetical order
    for filename in sorted(os.listdir(src_dir)):
        if filename.endswith('.jpg') or filename.endswith('.jpeg') or filename.endswith('.png') or filename.endswith('.webp'):
            total_files += 1
            src_name = os.path.join(src_dir, filename)
            # collect title and keywords from the image
            iptc_title, iptc_keywords = get_iptc_data_from_image(src_name)
            basename, _ = os.path.splitext(filename)
            print(f"{total_files} -> {filename}")
            try:
                # Open the image
                with Image.open(src_name) as img:
                    # Calculate the new size
                    width, height = img.size

                    if width > height:
                        ratio = max_size / width
                    else:
                        ratio = max_size / height

                    # print(f'ratio = {ratio}')
                    ratio = int(min(4, ratio))
                    # for multiple passes, the best ratio is as follows:
                    # 12+ -> 4 x 3
                    if ratio >= 12:
                        ratio = 4
                    # 11 -> 3 x 3
                    elif ratio == 11:
                        ratio = 3
                    # 10 -> 3 x 3
                    elif ratio == 10:
                        ratio = 3
                    # 9 -> 3 x 3
                    elif ratio == 9:
                        ratio = 3
                    # 8 -> 4 x 2
                    elif ratio == 8:
                        ratio = 4
                    # 7 -> 3 x 2
                    elif ratio == 7:
                        ratio = 3
                    # 6 -> 3 x 2
                    elif ratio == 6:
                        ratio = 3
                    # 5 -> 4
                    elif ratio == 5:
                        ratio = 4

                    resized_filename = os.path.join(
                        dst_dir, f"{basename}x{ratio}.jpg")
                    # print(f'ratio = {ratio}')
                    if ratio >= 2:
                        ratio = max(2, ratio)

                        # print(f'ratio = {ratio}')
                        print(
                            f"scaling {ratio}x from {width}x{height} to {width*ratio}x{height*ratio}")

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

            except:
                traceback.print_exc()
                exit()

    print(
        f'Total files: {total_files}, processed: {resized_files}, untouched: {untouched_files}')
    return resized_files


max_size = 7000
src_dir = './1-From-Leonardo'
dst_dir = './2-Scaled'

if __name__ == "__main__":
    # Create an argument parser
    parser = argparse.ArgumentParser(
        description='Upscales images from one folder to another')

    # Add an optional argument with a default value
    parser.add_argument('-in', '--inFolder', type=str, default='./1-From-Leonardo',
                        help='input folder')
    parser.add_argument('-out', '--outFolder', type=str, default='./2-Scaled',
                        help='output folder')
    parser.add_argument('-s', '--maxSize', type=int, default=7000,
                        help='max picture size - on the long side')

    # Parse the arguments
    args = parser.parse_args()

    # Access the value
    src_dir = args.inFolder
    dst_dir = args.outFolder
    max_size = args.maxSize

    print(f'scaling from {src_dir} to {dst_dir} with max size {max_size}')

    one_pass()
