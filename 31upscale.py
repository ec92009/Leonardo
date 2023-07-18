# Import required modules
import os
import shutil
from PIL import Image
import numpy as np
import argparse
import traceback

# Import face detection and IPTC modules
from iptcinfo3 import IPTCInfo
from EC_utils import detect_faces, add_iptc_metadata_to_image, get_iptc_data_from_image

# Define constants for folder paths
SRC_DIR = './1-From-Leonardo'
DST_DIR = './2-Scaled'
FACE_FOLDER = './3-Faces'
MAX_SIZE = 45_000_000

# Parse command line arguments
parser = argparse.ArgumentParser(description='Upscale images')
parser.add_argument('-i', '--inFolder', type=str, default=SRC_DIR)
parser.add_argument('-o', '--outFolder', type=str, default=DST_DIR)
parser.add_argument('-f', '--facesFolder', type=str, default=FACE_FOLDER)
parser.add_argument('-s', '--maxSize', type=int, default=MAX_SIZE)
args = parser.parse_args()

# Main function


def upscale_images():

    # Loop through all files
    for filename in sorted(os.listdir(args.inFolder)):

        # Check if image file
        if filename.endswith(('.jpg', '.jpeg', '.png', '.webp')):

            # Build file paths
            src_path = os.path.join(args.inFolder, filename)
            base_name, ext = os.path.splitext(filename)

            # Get IPTC metadata
            iptc_title, iptc_keywords = get_iptc_data_from_image(src_path)

            try:
                # Open image
                with Image.open(src_path) as img:

                    # Get dimensions
                    width, height = img.size

                    # Calculate resize ratio
                    ratioMP = args.maxSize / (width * height)
                    ratio = int(np.sqrt(ratioMP))
                    ratio = int(min(4, ratio))

                    # If big enough to resize
                    if ratio >= 2:

                        # Upscale image
                        dst_path = os.path.join(
                            args.outFolder, f"{base_name}x{ratio}.jpg")
                        print(f"Upscaling {filename} by {ratio}x")
                        # Call super resolution model here

                        # Add IPTC metadata
                        add_iptc_metadata_to_image(
                            dst_path, iptc_title, iptc_keywords)

                        # Delete original
                        os.remove(src_path)

                    # If too small
                    else:
                        print(f"{filename} is too small to upscale")
                        dst_path = os.path.join(args.outFolder, filename)
                        shutil.copyfile(src_path, dst_path)
                        os.remove(src_path)

                # Detect and move faces
                if detect_faces(dst_path):
                    shutil.move(dst_path, args.facesFolder)

            except:
                print(f"Error processing {filename}")
                traceback.print_exc()


if __name__ == '__main__':
    upscale_images()
