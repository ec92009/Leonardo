import os
import traceback
from iptcinfo3 import IPTCInfo
from sklearn.cluster import KMeans
from psd_tools import PSDImage
import sqlite3


def create_db(db_path):
    # Create a database file
    if not os.path.exists(db_path):
        open(db_path, 'w').close()

    # Create a connection to the database
    conn = sqlite3.connect(db_path)

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    # Create the 'generations' table
    cursor.execute('''CREATE TABLE IF NOT EXISTS generations (
                        id TEXT PRIMARY KEY,
                        modelId TEXT,
                        prompt TEXT,
                        negativePrompt TEXT,
                        imageHeight TEXT,
                        imageWidth TEXT,
                        inferenceSteps TEXT,
                        seed TEXT,
                        public TEXT,
                        scheduler TEXT,
                        sdVersion TEXT,
                        status TEXT,
                        presetStyle TEXT,
                        initStrength TEXT,
                        guidanceScale TEXT,
                        createdAt TEXT
                    )''')

    # Create the 'photos' table
    cursor.execute('''CREATE TABLE IF NOT EXISTS photos (
                        id TEXT PRIMARY KEY,
                        generation_id TEXT,
                        url TEXT,
                        nsfw TEXT,
                        likeCount TEXT,
                        FOREIGN KEY (generation_id) REFERENCES generations(id)
                    )''')

    # Create the 'variants' table
    cursor.execute('''CREATE TABLE IF NOT EXISTS variants (
                        id TEXT PRIMARY KEY,
                        photo_id TEXT,
                        variant_type TEXT,
                        url TEXT,
                        FOREIGN KEY (photo_id) REFERENCES photos(id)
                    )''')

    # create the 'models' table
    cursor.execute('''CREATE TABLE IF NOT EXISTS models (
            id TEXT PRIMARY KEY,
        description TEXT,
        name TEXT,
        modelWidth INTEGER,
        modelHeight INTEGER,
        status TEXT,
        type TEXT,
        updatedAt TEXT,
        createdAt TEXT,
        sdVersion TEXT,
        isPublic INTEGER,
        instancePrompt TEXT
    )''')

    # Commit the changes and close the connection
    conn.commit()
    conn.close()


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
        traceback.print_exc()
        pass


def get_iptc_data_from_image(image_path):
    # Open the image file
    info = IPTCInfo(image_path)  # https://pypi.org/project/iptcinfo3/
    # Get the title
    title = info['object name']
    # Get the keywords
    keywords = info['keywords']
    return title, keywords
