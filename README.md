# Leonardo

A few quick apps to interface with Leonardo AI

EC_extraction.py: extracts (downloads) images generated in Leonardo, and creates/populates a slqite3 database. Options include number of days to download, number of generations to skip, a flag to download originals (as opposed to variants only), a flag to order variants if not found (could be expensive, 5 tokens by order), a flag to upscale downloaded photos, 2, 3, or 4x up to 45 Mpixels.

EC_leoCompanion.py: provides a rough UI for EC_extraction above

0createDB: create a local sqlite3 database.

11generation: generates images in Leonardo.

4lastPic: gives quick access to the last picture created in Leonardo.

5promt_generation: leverages OpenAI to generate prompts.
