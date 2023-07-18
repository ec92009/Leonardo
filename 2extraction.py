# !pip install traceback        # https://docs.python.org/3/library/traceback.html
import datetime
import os
import subprocess
import traceback
# !pip install requests         # https://docs.python-requests.org/en/master/
import requests
# !pip install json             # https://docs.python.org/3/library/json.html
import json
# !pip install python-dotenv    # https://pypi.org/project/python-dotenv/
from dotenv import dotenv_values
# !pip install urllib           # https://docs.python.org/3/library/urllib.html
import urllib.request
# !pip install iptcinfo3        # https://pypi.org/project/iptcinfo3/
from iptcinfo3 import IPTCInfo
# !pip install sqlite3          # https://docs.python.org/3/library/sqlite3.html
import sqlite3
# !pip install argparse         # https://docs.python.org/3/library/argparse.html
import argparse

import shutil
from PIL import Image
import numpy as np

from EC_utils import detect_faces, add_iptc_metadata_to_image, get_iptc_data_from_image, create_db

MAX_SIZE = 45_000_000


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
            ratioMP = MAX_SIZE / (width * height)
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


def add_model(conn, modelId):

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    # find out if model is already in database
    cursor.execute('''SELECT * FROM models WHERE id=?''', (modelId,))

    rows = cursor.fetchall()

    if len(rows) > 0:
        name = rows[0][2]
        # print(f'model {modelId} already in database -> {name}')

    else:

        # acquire model info from Leonardo
        url = f"https://cloud.leonardo.ai/api/rest/v1/models/{modelId}"
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {bearer}"
        }
        response = requests.get(url, headers=headers)
        try:
            var0 = json.loads(response.text)
            # print(f'---->var0: {var0}')
            var = var0["custom_models_by_pk"]
            # print(f'---->var: {var}')
        except Exception as e:
            # traceback.print_exc()
            return

        id = var["id"]
        description = var["description"]
        name = var["name"]
        modelWidth = var["modelWidth"]
        modelHeight = var["modelHeight"]
        status = var["status"]
        type = var["type"]
        updatedAt = var["updatedAt"]
        createdAt = var["createdAt"]
        sdVersion = var["sdVersion"]
        isPublic = var["public"]
        instancePrompt = var["instancePrompt"]

        try:
            # Insert the variant into the 'variants' table
            cursor.execute('''INSERT INTO models (id, description, name, modelWidth, modelHeight, status, type, updatedAt, createdAt, sdVersion, isPublic, instancePrompt)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (id,  description, name, modelWidth, modelHeight, status, type, updatedAt, createdAt, sdVersion, isPublic, instancePrompt))
            # print(f'added model to database: {name}')
        except Exception as e:
            # traceback.print_exc()
            pass

    # Commit the changes and close the connection
    conn.commit()


def add_variant(conn, photo_id, variant_id, variant_type, url):

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    try:
        # Insert the variant into the 'variants' table
        cursor.execute('''INSERT INTO variants (id, photo_id, variant_type, url)
                      VALUES (?, ?, ?, ?)''', (variant_id, photo_id, variant_type, url))
        # print(f'added variant {variant_type} to database: {variant_id}')
    except Exception as e:
        # print(f'Exception 101 {e} error adding variant {variant_id}')
        pass

    # Commit the changes and close the connection
    conn.commit()


def add_photo(conn, photo_id, generation_id, url, nsfw, likeCount):

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    try:
        # Insert the photo into the 'photos' table
        sql = f'''INSERT OR REPLACE INTO photos (id, generation_id, url, nsfw, likeCount)
                      VALUES (?, ?, ?, ?, ?)'''
        cursor.execute(sql, (photo_id, generation_id, url, nsfw, likeCount))
        # print(f'added/updated photo to database: {photo_id}')

    except Exception as e:
        print(f'Exception {e} error adding photo {photo_id}')
        pass

    # Commit the changes and close the connection
    conn.commit()


def add_generation(conn, generation_id, prompt, modelId, negativePrompt, imageHeight, imageWidth, inferenceSteps, seed, public, scheduler, sdVersion, status, presetStyle, initStrength, guidanceScale, createdAt):
    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    try:
        # Insert the generation into the 'generations' table
        cursor.execute('''INSERT INTO generations (id, prompt, modelId, negativePrompt, imageHeight, imageWidth, inferenceSteps, seed, public, scheduler, sdVersion, status, presetStyle, initStrength, guidanceScale, createdAt)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (generation_id, prompt, modelId, negativePrompt, imageHeight, imageWidth, inferenceSteps, seed, public, scheduler, sdVersion, status, presetStyle, initStrength, guidanceScale, createdAt))
        # print(f'added generation to database: {generation_id}')

    except Exception as e:
        # traceback.print_exc()
        # print(f'Exception 138 {e} error adding generation {generation_id}')
        pass

    # Commit the changes
    conn.commit()


def keywordsFromPrompt(prompt):
    # remove punctuation
    prompt = prompt.replace(',', ' ').replace(';', ' ').replace(
        '[', ' ').replace(']', ' ').replace('  ', ' ')
    # print(f'-->prompt: {prompt}')
    # split the prompt into words
    words = prompt.split()
    # print(f'-->words: {words}')
    # remove duplicates
    dedupes = list(dict.fromkeys(words))
    # print(f'-->dedupes: {dedupes}')
    # remove words that are too short
    longWords = [word for word in dedupes if len(word) > 2]
    # print(f'-->longWords: {longWords}')
    return longWords


def order_variant(bearer, photoId):
    import requests

    url = "https://cloud.leonardo.ai/api/rest/v1/variations/upscale"

    payload = {"id": photoId}
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {bearer}"
    }

    response = requests.post(url, json=payload, headers=headers)

    # print(response.text)


def get_generations_by_user_id(userid, offset, limit, bearer, conn, all_leonardo_dir, variants=False):
    global total_images
    url = f"https://cloud.leonardo.ai/api/rest/v1/generations/user/{userid}?offset={offset}&limit={limit}"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {bearer}"
    }
    response = requests.get(url, headers=headers)
    # print(f'---->response.text: {response.text}')
    var1 = json.loads(response.text)["generations"]
    # if var1 is empty, let the exception be raised

    # print(f'---->var1: {var1}')
    prompt = var1[0]["prompt"]
    prompt = prompt.replace('\"', '').replace(':', '-').replace('\\', '')
    modelId = var1[0]["modelId"]
    negativePrompt = var1[0]["negativePrompt"]
    imageHeight = var1[0]["imageHeight"]
    imageWidth = var1[0]["imageWidth"]
    inferenceSteps = var1[0]["inferenceSteps"]
    seed = var1[0]["seed"]
    public = var1[0]["public"]
    scheduler = var1[0]["scheduler"]
    sdVersion = var1[0]["sdVersion"]
    status = var1[0]["status"]
    presetStyle = var1[0]["presetStyle"]
    initStrength = var1[0]["initStrength"]
    guidanceScale = var1[0]["guidanceScale"]
    createdAt = var1[0]["createdAt"]
    # print(f'-->created At: {createdAt}')
    createdDate = createdAt.split('T')[0]
    createdSplit = createdDate.replace('-', '/')
    generation_id = var1[0]["id"]
    add_generation(conn, generation_id, prompt, modelId, negativePrompt, imageHeight, imageWidth, inferenceSteps,
                   seed, public, scheduler, sdVersion, status, presetStyle, initStrength, guidanceScale, createdAt)
    if modelId != None:
        add_model(conn, modelId)

    generated_images = var1[0]["generated_images"]
    # print(f'-->generated_images: {generated_images}')
    for img_index in range(100):
        try:
            url = generated_images[img_index]["url"]
            photoId = generated_images[img_index]["id"]
            variant = generated_images[img_index]["generated_image_variation_generics"]
            nsfw = generated_images[img_index]["nsfw"]
            likeCount = generated_images[img_index]["likeCount"]

            try:
                add_photo(conn, photoId, generation_id,
                          url, nsfw, likeCount)
                # download image to folder 'from leonardo'
                filename = f"{prompt[:60]}-{img_index}-{photoId}.jpg"
                title = prompt
                keywords = keywordsFromPrompt(prompt)

                download_photo(all_leonardo_dir, url,
                               createdSplit, filename, title, keywords)

            except Exception as e:
                traceback
                pass

            for type_index in range(1000):
                try:
                    var_url = variant[type_index]["url"]
                    var_id = variant[type_index]["id"]
                    var_type = variant[type_index]["transformType"]
                    # print(f'-->var_type: {var_type}')

                    try:
                        add_variant(conn, photoId, var_id, var_type, url)
                        filename = f"{prompt[:60]}-{img_index}-{var_type}_{var_id}.jpg"
                        title = prompt
                        keywords = keywordsFromPrompt(prompt)

                        download_photo(all_leonardo_dir, var_url,
                                       createdSplit, filename, title, keywords)
                    except Exception as e:
                        traceback
                        pass

                except:
                    if type_index == 0:
                        if variants:
                            print(
                                f"-->No variants for image {img_index}, let's order one for {photoId}")
                            order_variant(bearer, photoId)
                    break

        except:
            break

    return prompt, createdDate


def download_photo(all_leonardo_dir, url, createdSplit, filename, title, keywords):
    outfolder = f"{all_leonardo_dir}/{createdSplit}"
    os.makedirs(outfolder, exist_ok=True)

    outfile = f"{outfolder}/{filename}"
    # if outfile does not already exist, download it
    if not os.path.exists(outfile):
        urllib.request.urlretrieve(url, outfile)
        add_iptc_metadata_to_image(outfile, title, keywords)
        total_images += 1

    if upscales:
        upscale_one_picture(outfile)


def extract(num_days, all_leonardo_dir, skip=0, variants=False):
    global total_images
    today = datetime.date.today()
    # convert today to a string in the format YYYY-MM-DD
    today_str = today.strftime("%Y-%m-%d")
    if num_days == 0:
        first_day = datetime.date(2000, 1, 1)
    else:
        first_day = today - datetime.timedelta(days=num_days)
    # convert first_day to a string in the format YYYY-MM-DD
    first_day_str = first_day.strftime("%Y-%m-%d")

    subject = ""
    iteration = skip
    created = today_str

    # Create the database is database.sqlite3 does not exist
    db_path = f'{all_leonardo_dir}/database.sqlite3'
    if not os.path.exists(db_path):
        create_db(db_path)

    conn = sqlite3.connect(db_path)

    while created > first_day_str:
        try:
            subject, created = get_generations_by_user_id(
                userid, iteration, 1, bearer, conn, all_leonardo_dir, variants)
            iteration += 1
            print(
                f'-->created: {created}, subject({iteration}): {subject[:80]}...')
        except Exception as e:
            print(f'done... {total_images} images downloaded')
            exit()

    conn.close()


def get_userid_from_bearer(bearer):
    url = "https://cloud.leonardo.ai/api/rest/v1/me"

    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {bearer}"
    }

    response = requests.get(url, headers=headers)

    inter1 = json.loads(response.text)["user_details"][0]["user"]
    userid = inter1["id"]
    username = inter1["username"]
    return userid, username


try:
    config = dotenv_values(".env")
    bearer = config["LEO_KEY"]
    print(f'using bearer key: from .env file')
except Exception as e:
    pass

total_images = 0

if __name__ == "__main__":
    # Create an argument parser
    parser = argparse.ArgumentParser(
        description='Download the Leonardo images from the last N days')

    # Add an optional argument with a default value
    parser.add_argument('-k', '--key', type=str, default="",
                        help='Leonardo API key')
    # Add an optional argument with a default value
    parser.add_argument('-d', '--days', type=int, default=1,
                        help='Number of days to download - 0 for unlimited')
    # Add an optional argument with a default value
    parser.add_argument('-s', '--skip', type=int, default=0,
                        help='Number of generations to skip')
    # Add an optional argument to generate variants if not found
    parser.add_argument('-v', '--variants', type=bool, default=True,
                        help='Generate variants if not found (default: True))')
    # Add an optional argument to upscale images
    parser.add_argument('-u', '--upscale', type=bool, default=True,
                        help='Upscale pictures upon download, default: True')
    # Add an optional argument with a default value
    parser.add_argument('-l', '--leonardo_dir', type=str, default="/Users/ecohen/Documents/LR/_All Leonardo",
                        help='Where to download')

    # Parse the arguments
    args = parser.parse_args()

    # Access the value
    num_days = args.days
    all_leonardo_dir = args.leonardo_dir
    skip = args.skip
    variants = args.variants
    upscales = args.upscale

    if args.key != "":
        bearer = args.key
        print(f'using bearer key: from command line')

    userid, username = get_userid_from_bearer(bearer)
    print(f'userid: {userid}, username: {username}')

    if num_days == 0:
        print(f'extracting all days to {all_leonardo_dir}')
    else:
        print(f'extracting {num_days} days to {all_leonardo_dir}')

    extract(num_days, all_leonardo_dir, skip, variants)
