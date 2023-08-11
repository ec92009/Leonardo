import requests
from dotenv import dotenv_values
from requests_oauthlib import OAuth1


def post_photo_to_twitter(photo_path, caption):

    config = dotenv_values(".env")

    # Authenticate to Twitter
    auth = OAuth1(
        config["X_API_key"],
        config["X_API_key_secret"],
        config["X_Access_token"],
        config["X_Access_token_secret"])

    # # Upload image
    # media_url = "https://upload.twitter.com/1.1/media/upload.json"
    # media_data = open(photo_path, "rb").read()
    # media_response = requests.post(media_url, data=media_data, auth=auth)
    # media_id = media_response.json()["media_id"]

    # Create a tweet with an image
    status_url = "https://api.twitter.com/1.1/statuses/update.json"
    status_params = {
        "status": caption
        # ,"media_ids": media_id
    }
    status_response = requests.post(
        status_url, params=status_params, auth=auth)
    print(f'Tweet posted: {status_response.json()["text"]}')


if __name__ == "__main__":
    post_photo_to_twitter(
        "Screenshot 2023-07-21 at 16.13.27.png", "AI generated test")
