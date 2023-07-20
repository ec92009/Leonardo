import requests                     # !pip install requests
import json                         # !pip install json
from dotenv import dotenv_values    # !pip install python-dotenv
import time
import sqlite3


# def order_variant(picId):
#     url = "https://cloud.leonardo.ai/api/rest/v1/variations/upscale"
#     payload = {"id": picId}
#     headers = {
#         "accept": "application/json",
#         "content-type": "application/json",
#         "authorization": f"Bearer {bearer}"
#     }


def getSingleGeneration(genId):
    url = f"https://cloud.leonardo.ai/api/rest/v1/generations/{genId}"

    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {bearer}"
    }

    attempts = 10
    while attempts > 0:
        response = requests.get(url, headers=headers)
        # print(f'-->response.text: {response.text}')
        generations_by_pk = json.loads(response.text)["generations_by_pk"]
        # print(f'--> generations_by_pk: {generations_by_pk}' )
        generations = generations_by_pk["generated_images"]
        # print(f'--> generations: {generations}')
        if len(generations) == 0:
            print(".", end="")
            time.sleep(1)
            attempts -= 1
            continue
        else:
            #     for generation in generations:
            #         print(f'--> generation: {generation}')
            #         id = generation["id"]
            #         print(f'--> id: {id}')
            #         order_variant(id)
            print("")
            return

    print('failed after 10 attempts.')
    return


def generate_one_pic(prompt, modelId, modelName, sd_version, width, height):
    print(f"Generating image for model {modelName}")

    url = "https://cloud.leonardo.ai/api/rest/v1/generations"

    payload = {
        "prompt": prompt,
        "modelId": modelId,
        "negative_prompt": "letter, letters, writing, texts, text, too many clothes, close up, over one head, two faces, two bodies, plastic, Deformed, blurry, bad anatomy, bad eyes, crossed eyes, disfigured, poorly drawn face, mutation, mutated, extra limb, ugly, poorly drawn hands, missing limb, blurry, floating limbs, disconnected limbs, malformed hands, blur, out of focus, long neck, long body, mutated hands and fingers, out of frame, blender, doll, cropped, low-res, poorly-drawn face, out of frame double, two heads, blurred, ugly, disfigured, over five fingers on each hand, deformed, repetitive, black and white, grainy, extra limbs, bad anatomyHigh pass filter, airbrush, portrait, zoomed, soft light, smooth skin, closeup, deformed, extra limbs, extra fingers, mutated hands, bad anatomy, bad proportions, blind, ugly eyes, dead eyes, blur, vignette, out of shot, gaussian, monochrome, grainy, noisy, text, writing, watermark, logo, over saturation, over shadow, bra",
        "width": width,
        "height": height,
        "sd_version": sd_version,
        "num_images": 3,
        "num_inference_steps": None,
        "guidance_scale": 15,
        "scheduler": "LEONARDO",
        "presetStyle": "GENERAL",
        "public": True,
        "promptMagic": True
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {bearer}"
    }

    _ = requests.post(url, json=payload, headers=headers)
    # genId = json.loads(response.text)[
    #     "sdGenerationJob"]["generationId"]
    # getSingleGeneration(genId)

    # attempts = 10

    # while attempts > 0:
    #     response = requests.post(url, json=payload, headers=headers)

    #     # print(f'--> response.text: {response.text}')
    #     try:
    #         genId = json.loads(response.text)[
    #             "sdGenerationJob"]["generationId"]
    #         getSingleGeneration(genId)
    #         return

    #     except Exception as e:
    #         attempts -= 1
    #         if attempts > 0:
    #             print(
    #                 f"Exception: {e} Sleeping 1 second, attempts left: {attempts}...")
    #             time.sleep(1)
    #         else:
    #             print('Failed after 10 attempts.')
    #             exit()


def main():

    prompt = "Tranquil countryside with rolling hills -- countryside, rolling hills, nature, rural, serene, peaceful, picturesque, beauty, landscape, scenic, tranquil, farm, green, outdoors"

    conn = sqlite3.connect(
        "/Users/ecohen/Documents/LR/_All Leonardo/database.sqlite3")

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    # Execute the SQL query
    cursor.execute(
        "SELECT id, name, modelWidth, modelHeight, sdVersion FROM models")

    # Fetch one row at a time
    row = cursor.fetchone()
    count = 0
    while row is not None:
        count += 1
        print(f"Model {count} -> ", end="")
        # Process the row data
        modelId, modelName, modelWidth, modelHeight, sdVersion = row

        generate_one_pic(prompt, modelId, modelName, sdVersion,
                         modelWidth * 2, modelHeight * 2)

        # Fetch the next row
        row = cursor.fetchone()

    # Close the cursor and the connection
    cursor.close()
    conn.close()


# Global variables
config = dotenv_values(".env")
bearer = config["LEO_KEY"]
userid = config["LEO_USERID"]
total_images = 0


if __name__ == "__main__":
    main()
