import sqlite3


def create_db():
    # Create a connection to the database
    conn = sqlite3.connect('database.sqlite3')

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


if __name__ == '__main__':
    create_db()
