import datetime
import os
import subprocess
import traceback
import requests
import json
from dotenv import dotenv_values
# import urllib.request
import sqlite3
import argparse     # https://docs.python.org/3/library/argparse.html
import shutil
from PIL import Image   # pip install Pillow
import numpy as np  # pip install numpy
import matplotlib.pyplot as plt  # pip install matplotlib
# https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.html
import matplotlib.image as mpimg
import time  # https://docs.python.org/3/library/time.html
import threading    # https://docs.python.org/3/library/threading.html
import multiprocessing as mp  # https://docs.python.org/3/library/multiprocessing.html
# https://docs.python.org/3/library/concurrent.futures.html
import concurrent.futures as cf


from EC_iptcinfo3 import IPTCInfo
from EC_utils import detect_faces, create_db


def stats(downloaded=0, ordered=0, upscaled=0, generations=0, originals=0, variants=0):
    EC_EXTRACTION_STATS['downloaded'] += downloaded
    EC_EXTRACTION_STATS['ordered'] += ordered
    EC_EXTRACTION_STATS['upscaled'] += upscaled
    EC_EXTRACTION_STATS['generations'] += generations
    EC_EXTRACTION_STATS['originals'] += originals
    EC_EXTRACTION_STATS['variants'] += variants
    return EC_EXTRACTION_STATS


def add_iptc_metadata_to_image(image_path, title, keywords):
    # Open the image file    # https://pypi.org/project/iptcinfo3/
    try:
        info = IPTCInfo(image_path, force=True)
        # Set the title
        info['object name'] = title[:120]
        # Set the keywords
        info['keywords'] = keywords
        # Save the changes
        info.save()
        tildaPath = f'{image_path}~'
        # delete the backup file
        if os.path.exists(tildaPath):
            os.remove(tildaPath)

    except:
        print(f"Error writing IPTC data to {image_path}")
        # traceback.print_exc()
        pass


def get_iptc_data_from_image(image_path):
    # Open the image file
    # https://pypi.org/project/iptcinfo3/
    # info = IPTCInfo(image_path, inp_charset='utf-8', out_charset='utf-8')
    info = IPTCInfo(image_path)
    # Get the title
    title = info['object name']
    # Get the keywords
    keywords = info['keywords']
    return title, keywords


def display_image(image_path):
    # Read the image using matplotlib's imread function
    img = mpimg.imread(image_path)

    # Display the image using imshow
    plt.imshow(img)
    plt.axis('off')  # Turn off axis ticks and labels for a cleaner display
    plt.show()


def file_with_string_exists(folder_path, search_string):
    # Get a list of files in the folder
    files_in_folder = os.listdir(folder_path)

    # Iterate through the list of files
    for filename in files_in_folder:
        # Check if the search_string is present in the filename
        if search_string in filename:
            return True

    # If the search_string was not found in any filenames, return False
    return False


def upscale_one_picture(src_path, pic_Id, iter):

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

    # print(f'id: {pic_Id}')

    # if a file exists with pic_Id in the name
    if file_with_string_exists(dst_dir, pic_Id):
        # print(f'Upscaled version already exists in {dst_dir}, skipping')
        return
    if file_with_string_exists(face_dir, pic_Id):
        # print(f'Upscaled version already exists in {face_dir}, skipping')
        return

    # Open the image
    with Image.open(src_path) as img:
        width, height = img.size
        ratioMP = EC_EXTRACTION_MAX_SIZE / (width * height)
        ratio = int(np.sqrt(ratioMP))
        ratio = int(min(4, ratio))
        face_found = False

        if ratio >= 2:
            # print(f'ratio = {ratio}')
            dest_path = os.path.join(dst_dir, f"{basename}x{ratio}.jpg")
            face_path = os.path.join(face_dir, f"{basename}x{ratio}.jpg")

            # if the destination file does not exists, skip it
            if not os.path.exists(dest_path) and not os.path.exists(face_path):
                print(
                    f"{iter} scaling {ratio}x from {width}x{height} to {width*ratio}x{height*ratio} ie. {width*ratio*height*ratio/1_000_000} Mpixels")
                command = f'./realesrgan-ncnn-vulkan -i "{src_path}" -o "{dest_path}" -s {ratio}'
                _ = subprocess.run(command, shell=True,
                                   capture_output=True, text=True)
                add_iptc_metadata_to_image(
                    dest_path, iptc_title, iptc_keywords)

                stats(upscaled=1)

                face_found = detect_faces(
                    dest_path) if EC_EXTRACTION_FACES else False
            else:
                print(f'Upscaled version already exists, skipping')
                if os.path.exists(dest_path):
                    face_found = detect_faces(
                        dest_path) if EC_EXTRACTION_FACES else False
                else:
                    face_found = detect_faces(
                        face_path) if EC_EXTRACTION_FACES else False

        else:
            # if the file is too large to resize, say so and take it out of the way
            print(
                f'current size: {width}x{height} too big to upscale')
            dest_path = os.path.join(
                dst_dir, f"{basename}.jpg")

            shutil.copyfile(src_path, dest_path)
            face_found = detect_faces(
                dest_path) if EC_EXTRACTION_FACES else False

        if face_found:
            face_path = os.path.join(face_dir, os.path.basename(dest_path))
            if os.path.exists(dest_path):
                os.replace(dest_path, face_path)

    # except:
    #     traceback.print_exc()
    #     exit()


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
            "authorization": f"Bearer {EC_EXTRACTION_KEY}"
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

        if var == None:
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
            sql = f'''INSERT INTO models (id, description, name, modelWidth, modelHeight, status, type, updatedAt, createdAt, sdVersion, isPublic, instancePrompt)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
            # Insert the variant into the 'variants' table
            cursor.execute(sql, (id,  description, name, modelWidth, modelHeight,
                           status, type, updatedAt, createdAt, sdVersion, isPublic, instancePrompt))
            # print(f'added model to database: {name}')
        except Exception as e:
            # traceback.print_exc()
            exit()

    # Commit the changes and close the connection
    conn.commit()


def add_variant(conn, photo_id, variant_id, variant_type, url):

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    try:
        # Insert the variant into the 'variants' table
        sql = f'''INSERT OR REPLACE INTO variants (id, photo_id, variant_type, url)
                      VALUES (?, ?, ?, ?)'''
        cursor.execute(sql, (variant_id, photo_id, variant_type, url))
        # print(f'added variant {variant_type} to database: {variant_id}')
    except Exception as e:
        # traceback.print_exc()
        exit()

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
        # traceback.print_exc()
        exit()

    # Commit the changes and close the connection
    conn.commit()


def add_generation(conn, generation_id, prompt, modelId, negativePrompt, imageHeight, imageWidth, inferenceSteps, seed, public, scheduler, sdVersion, status, presetStyle, initStrength, guidanceScale, createdAt):
    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    try:
        # Insert the generation into the 'generations' table
        sql = f'''INSERT OR REPLACE INTO generations (id, prompt, modelId, negativePrompt, imageHeight, imageWidth, inferenceSteps, seed, public, scheduler, sdVersion, status, presetStyle, initStrength, guidanceScale, createdAt)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
        cursor.execute(sql, (generation_id, prompt, modelId, negativePrompt, imageHeight, imageWidth, inferenceSteps,
                       seed, public, scheduler, sdVersion, status, presetStyle, initStrength, guidanceScale, createdAt))
        # print(f'added generation to database: {generation_id}')

    except Exception as e:
        # traceback.print_exc()
        exit()

    # Commit the changes
    conn.commit()


def keywordsFromPrompt(prompt):
    # remove punctuation
    prompt = prompt.replace(',', ' ').replace(';', ' ').replace(
        '[', ' ').replace(']', ' ').replace('  ', ' ').replace('(', '').replace(')', '')
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
    black_list = ['a', 'the', 'down', 'with', 'very', 'their', 'his', 'her', 'and', 'for', 'from', 'that', 'this', 'these', 'those', 'which', 'what', 'where', 'when', 'how', 'why', 'who', 'whom', 'whose', 'will', 'would', 'should', 'could', 'can', 'may', 'might', 'must', 'shall', 'is', 'are', 'was', 'were', 'be', 'been',
                  'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'an', 'of', 'in', 'on', 'at', 'to', 'by', 'as', 'or', 'not', 'no', 'yes', 'if', 'then', 'else', 'than', 'so', 'such', 'like', 'unlike', 'but', 'however', 'yet', 'though', 'although', 'even', 'though', 'whether', 'either']
    # set white_words to be the longWords minus the black_list
    white_words = [word for word in longWords if word not in black_list]

    # print(f'-->white_words: {white_words}')

    return white_words


def send_order(url, payload, headers):
    response = requests.post(url, json=payload, headers=headers)


def order_variant(photoId):
    import requests

    url = "https://cloud.leonardo.ai/api/rest/v1/variations/upscale"

    payload = {"id": photoId}
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {EC_EXTRACTION_KEY}"
    }

    t = threading.Thread(target=send_order, args=(url, payload, headers))
    EC_EXTRACTION_threads.append(t)
    t.start()

    # print(response.text)


def get_generations_by_user_id(userid, offset, limit, conn, all_leonardo_dir, first_day_str, executor):

    url = f"https://cloud.leonardo.ai/api/rest/v1/generations/user/{userid}?offset={offset}&limit={limit}"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {EC_EXTRACTION_KEY}"
    }

    attempts = 10
    while attempts > 0:
        try:
            response = requests.get(url, headers=headers, timeout=2)
        except requests.exceptions.Timeout:
            attempts -= 1
            print(f'timeout - attempts left: {attempts} / 10')
            if attempts == 0:
                print(f'Failed after 10 attempts')
                return "", datetime.date.today().strftime("%Y-%m-%d")
            else:
                continue
        except Exception as e:
            print(f'Error: {e}')
            continue

        if response.status_code == 200:
            break
        else:
            attempts -= 1
            print(
                f'status code: {response.status_code} - attempts left: {attempts} / 10')
            # print(f'Error: {json.loads(response.content)["error"]}')
            # traceback.print_exc()
            if attempts == 0:
                print(f'Failed after 10 attempts')
                return "", datetime.date.today().strftime("%Y-%m-%d")

    # print(f'---->response.text: {response.text}')
    try:
        var1 = json.loads(response.text)["generations"]
    except Exception as e:
        print(f'Error: {json.loads(response.content)["error"]}')
        print(f'response.text: {response.text}')
        # traceback.print_exc()
        return "", datetime.date.today().strftime("%Y-%m-%d")
    # if var1 is empty, let the exception be raised

    if len(var1) == 0:
        return "...", datetime.date.today().strftime("%Y-%m-%d")

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
    createdSlashed = createdDate.replace('-', '/')
    generation_id = var1[0]["id"]

    if createdDate <= first_day_str:
        return prompt, createdDate

    print(f'{createdDate}({offset}):{prompt[:100]}')

    add_generation(conn, generation_id, prompt, modelId, negativePrompt, imageHeight, imageWidth, inferenceSteps,
                   seed, public, scheduler, sdVersion, status, presetStyle, initStrength, guidanceScale, createdAt)
    stats(generations=1)

    if modelId != None:
        add_model(conn, modelId)

    generated_images = var1[0]["generated_images"]
    stats(originals=len(generated_images))

    for img_index in range(len(generated_images)):
        url = generated_images[img_index]["url"]
        photoId = generated_images[img_index]["id"]
        variant = generated_images[img_index]["generated_image_variation_generics"]
        nsfw = generated_images[img_index]["nsfw"]
        likeCount = generated_images[img_index]["likeCount"]

        add_photo(conn, photoId, generation_id,
                  url, nsfw, likeCount)
        # download image to folder 'from leonardo'
        filename = f"{prompt[:60]}-{img_index}-{photoId}.jpg"
        title = prompt
        keywords = keywordsFromPrompt(prompt)

        if EC_EXTRACTION_ORIGINALS:
            download_photo(all_leonardo_dir, url,
                           createdSlashed, filename,
                           title, keywords, photoId, 'ORIGINAL',
                           f'->{createdDate}({offset}-{img_index})', executor)

        # VARIANTS (UPSCALES AND CROPS)
        stats(variants=len(variant))

        if len(variant) == 0:
            if EC_EXTRACTION_VARIANTS:
                print(
                    f"-->No variants for image {img_index}, ordering one")
                order_variant(photoId)
                stats(ordered=1)

        # DOWNLOAD VARIANTS
        for type_index in range(len(variant)):
            var_url = variant[type_index]["url"]
            if var_url == None:
                break
            var_id = variant[type_index]["id"]
            var_type = variant[type_index]["transformType"]
            # print(f'-->var_type: {var_type}')

            add_variant(conn, photoId, var_id, var_type, url)
            filename = f"{prompt[:60]}-{img_index}-{var_type}_{var_id}.jpg"
            title = prompt
            keywords = keywordsFromPrompt(prompt)

            download_photo(all_leonardo_dir, var_url,
                           createdSlashed, filename, title, keywords, var_id, var_type, f'->{createdDate}({offset}-{img_index}-{type_index})', executor)

    return prompt, createdDate


def download_file(url, save_path, title, keywords):
    # Send an HTTP GET request to the URL
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Open the file in binary write mode and save the content
        with open(save_path, 'wb') as f:
            f.write(response.content)
        # print(f"File saved successfully to: {save_path}")
        # display_image(save_path)

        add_iptc_metadata_to_image(save_path, title, keywords)
        stats(downloaded=1)

    else:
        print(
            f"Failed to download the file. Status code: {response.status_code}")


def download_photo(target_dir, url, created, filename, title, keywords, pic_Id, variant_type, iter, executor):

    outfolder = f"{target_dir}/{created}/{variant_type}"
    os.makedirs(outfolder, exist_ok=True)

    outfile = f"{outfolder}/{filename}"
    # if outfile does not already exist, download it
    if not os.path.exists(outfile):
        try:
            t = threading.Thread(target=download_file,
                                 args=(url, outfile, title, keywords))
            EC_EXTRACTION_threads.append(t)
            t.start()

        except Exception as e:
            print(f'Error downloading: {e}')
            pass

    if EC_EXTRACTION_UPSCALES:
        try:
            t.join()
            EC_EXTRACTION_threads.remove(t)
        except:
            pass
        # upscale the image

        _ = executor.submit(
            upscale_one_picture, outfile, pic_Id, iter)

        # p = multiprocessing.Process(
        #     target=upscale_one_picture, args=(outfile, pic_Id))
        # p.start()
        # processes.append(p)

        # upscale_one_picture(outfile, pic_Id)


def extract(num_days, all_leonardo_dir, skip, executor):

    userid, username = get_userid_from_bearer()
    print(f'userid: {userid}, username: {username}')

    today = datetime.date.today()
    # convert today to a string in the format YYYY-MM-DD
    today_str = today.strftime("%Y-%m-%d")
    if num_days == 0:
        first_day = datetime.date(2000, 1, 1)
    else:
        first_day = today - datetime.timedelta(days=num_days)
    # convert first_day to a string in the format YYYY-MM-DD
    first_day_str = first_day.strftime("%Y-%m-%d")
    print(f'Will start at {today_str}, and stop at {first_day_str}, excluded')

    prompt = ""
    iteration = skip
    date_created = today_str

    # Create the database is database.sqlite3 does not exist
    db_path = f'{all_leonardo_dir}/database.sqlite3'
    if not os.path.exists(db_path):
        create_db(db_path)

    conn = sqlite3.connect(db_path)

    while date_created > first_day_str and prompt != "...":
        try:
            prompt, date_created = get_generations_by_user_id(
                userid, iteration, 1, conn, all_leonardo_dir, first_day_str, executor)
            if date_created <= first_day_str:
                break
            iteration += 1
            # print(
            #     f'{date_created}({iteration}):{prompt[:100]}')
        except KeyboardInterrupt:
            print('Interrupted by user action')
            break
        except Exception as e:
            print(f'Error: {e}')
            traceback.print_exc()
            break

    conn.close()
    return EC_EXTRACTION_STATS


def get_userid_from_bearer():

    global EC_EXTRACTION_KEY

    if EC_EXTRACTION_KEY == "":
        try:
            config = dotenv_values(".env")
            EC_EXTRACTION_KEY = config["LEO_KEY"]
            # print(f'using bearer key: from .env file')
        except Exception as e:
            pass
    if EC_EXTRACTION_KEY == "":
        print("Leonardo API key not found, exiting")
        return

    url = "https://cloud.leonardo.ai/api/rest/v1/me"

    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {EC_EXTRACTION_KEY}"
    }

    response = requests.get(url, headers=headers)

    inter1 = json.loads(response.text)["user_details"][0]["user"]
    userid = inter1["id"]
    username = inter1["username"]
    return userid, username


def EC_extraction_main():
    global EC_EXTRACTION_ORIGINALS
    global EC_EXTRACTION_VARIANTS
    global EC_EXTRACTION_UPSCALES

    # https://docs.python.org/3/library/time.html#time.perf_counter
    start = time.perf_counter()

    # Create an argument parser
    parser = argparse.ArgumentParser(
        description='Download the Leonardo images from the last N days')

    # Add an optional argument for the Leonardo API Key
    parser.add_argument('-k', '--key', type=str, default="",
                        help='Leonardo API key')
    # Add an optional argument for how many days to download
    parser.add_argument('-d', '--days', type=int, default=2,
                        help='Number of days to download - 0 for unlimited (default: 2)')
    # Add an optional argument to skip the most recent generations
    parser.add_argument('-s', '--skip', type=int, default=0,
                        help='Number of generations to skip (default: 0)')
    # Add an optional argument to download original pictures
    parser.add_argument('-o', '--originals', action="store_true",
                        help='Download originals (default: False)')
    # Add an optional argument to generate variants if not found
    parser.add_argument('-v', '--variants', action="store_true",
                        help='Orders generation of variants if not found - could be expensive (default: False)')
    # Add an optional argument to upscale images
    parser.add_argument('-u', '--upscale', action="store_true",
                        help='Upscale pictures upon download, (default: False)')
    # Add an optional argument to detect faces
    parser.add_argument('-f', '--faces', type=bool, default=False,
                        help='Detect if scaled pictures include a face, and sort them in a different folder, (default: False)')
    # Add an optional argument for the download folder
    parser.add_argument('-l', '--leonardo_dir', type=str, default="/Users/ecohen/Documents/LR/_All Leonardo",
                        help='Where to download')

    # Parse the arguments
    args = parser.parse_args()

    # Access the value
    days = args.days
    leonardo_dir = args.leonardo_dir
    # if the folder does not exist, create it
    if not os.path.exists(leonardo_dir):
        os.makedirs(leonardo_dir)
    skip = args.skip
    EC_EXTRACTION_VARIANTS = args.variants
    EC_EXTRACTION_UPSCALES = args.upscale
    faces = args.faces
    EC_EXTRACTION_ORIGINALS = args.originals

    if args.key != "":
        EC_EXTRACTION_KEY = args.key
        print(f'using bearer key: from command line')

    print(f'Will extract all days to {leonardo_dir}') if days == 0 else print(
        f'Will extract the last {days} days to {leonardo_dir}')
    print(f'Will skip the first: {skip} generations') if skip > 0 else print(
        'Will NOT skip any generations')
    print('will download originals') if EC_EXTRACTION_ORIGINALS else print(
        'will NOT download originals')
    print('will order generation of UPSCALE variants (could consume lots of tokens - 5 per order)') if EC_EXTRACTION_VARIANTS else print(
        'will NOT generate variants')
    print(f'will upscale images 2x, 3x, or 4x, limited to {EC_EXTRACTION_MAX_SIZE/1_000_000} MPixels') if EC_EXTRACTION_UPSCALES else print(
        'will NOT upscale images')
    print('will detect faces') if faces else print(
        'will NOT detect faces')

    with cf.ProcessPoolExecutor() as executor:
        extract(days, leonardo_dir, skip, executor)
        print(
            "Finished extracting generations ... Waiting for upscalinsubprocesses to finish")

    # wait for all threads to finish
    for thread in EC_EXTRACTION_threads:
        thread.join()

    print(f'Done...{stats()}')
    finish = time.perf_counter()
    print(f'Finished in {round(finish-start, 2)} second(s)')


EC_EXTRACTION_STATS = {'downloaded': 0, 'ordered': 0, 'upscaled': 0,
                       'generations': 0, 'originals': 0, 'variants': 0}


EC_EXTRACTION_MAX_SIZE = 45_000_000
EC_EXTRACTION_threads = []
EC_EXTRACTION_ORIGINALS = False
EC_EXTRACTION_VARIANTS = False
EC_EXTRACTION_UPSCALES = False
EC_EXTRACTION_FACES = False
EC_EXTRACTION_KEY = ""


if __name__ == "__main__":
    EC_extraction_main()
