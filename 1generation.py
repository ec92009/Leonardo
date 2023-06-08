import requests                     # !pip install requests
import json                         # !pip install json
from dotenv import dotenv_values    # !pip install python-dotenv
import time

# from iptcinfo3 import IPTCInfo  # https://pypi.org/project/iptcinfo3/

# def add_iptc_metadata_to_image(image_path, title, keywords):
#     # Open the image file
#     info = IPTCInfo(image_path)

#     # Set the title
#     info['object name'] = title

#     # Set the keywords
#     keywords_list = keywords.split(',')
#     info['keywords'] = keywords_list

#     # Save the changes
#     info.save(options='overwrite')


def upscale(picId):
    url = "https://cloud.leonardo.ai/api/rest/v1/variations/upscale"
    payload = {"id": picId}
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {bearer}"
    }

    # response = requests.post(url, json=payload, headers=headers)

    # # print(response.text)

    # jobId = json.loads(response.text)["sdUpscaleJob"]["id"]
    # print(f'--> Upscale jobId: {jobId} for picId: {picId}')


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
            print("Sleeping 1 second...")
            time.sleep(1)
            attempts -= 1
            continue
        else:
            for generation in generations:
                print(f'--> generation: {generation}')
                id = generation["id"]
                print(f'--> id: {id}')
                upscale(id)
        return
    exit()


def generate_one_pic_with_upscale_variant(prompt):
    url = "https://cloud.leonardo.ai/api/rest/v1/generations"
    modelId = "b7aa9939-abed-4d4e-96c4-140b8c65dd92"  # DreamShaper v6
    # modelId = "a097c2df-8f0c-4029-ae0f-8fd349055e61"  # RPG
    # "modelId": "291be633-cb24-434f-898f-e662799936ad",
    # "modelId": "78719f8b-8644-410b-818e-1d592abeee10",     # paper art style

    payload = {
        "prompt": prompt,
        "modelId": modelId,
        "negative_prompt": "letter, letters, writing, texts, text, too many clothes, close up, over one head, two faces, two bodies, plastic, Deformed, blurry, bad anatomy, bad eyes, crossed eyes, disfigured, poorly drawn face, mutation, mutated, extra limb, ugly, poorly drawn hands, missing limb, blurry, floating limbs, disconnected limbs, malformed hands, blur, out of focus, long neck, long body, mutated hands and fingers, out of frame, blender, doll, cropped, low-res, poorly-drawn face, out of frame double, two heads, blurred, ugly, disfigured, over five fingers on each hand, deformed, repetitive, black and white, grainy, extra limbs, bad anatomyHigh pass filter, airbrush, portrait, zoomed, soft light, smooth skin, closeup, deformed, extra limbs, extra fingers, mutated hands, bad anatomy, bad proportions, blind, ugly eyes, dead eyes, blur, vignette, out of shot, gaussian, monochrome, grainy, noisy, text, writing, watermark, logo, over saturation, over shadow, bra",
        "width": 768,
        "height": 576,
        "sd_version": "v1_5",
        "num_images": 1,
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

    attempts = 10

    while attempts > 0:
        response = requests.post(url, json=payload, headers=headers)

        # print(f'--> response.text: {response.text}')
        try:
            genId = json.loads(response.text)[
                "sdGenerationJob"]["generationId"]
            getSingleGeneration(genId)
            return

        except Exception as e:
            attempts -= 1
            if attempts > 0:
                print(
                    f"Exception: {e} Sleeping 1 second, attempts left: {attempts}...")
                time.sleep(1)
            else:
                print('Failed after 10 attempts.')
                exit()


def main():
    with open('prompts.txt') as f:
        data = f.readlines()
        index = 0
        for line in data:
            # skip everything to the left of " = "
            try:
                print(f'prompt {index}: {line}')
                generate_one_pic_with_upscale_variant(line)
                index += 1
            except Exception as e:
                print(f'Exception: {e}')
                exit()

    print(f"Generated {index} images and variants!")


# Global variables
config = dotenv_values(".env")
bearer = config["LEO_KEY"]
userid = config["LEO_USERID"]
total_images = 0


if __name__ == "__main__":
    main()
