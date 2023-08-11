from dotenv import dotenv_values
from instabot import Bot  # pip install instabot


def post_photo_to_instagram(photo_path, caption):

    config = dotenv_values(".env")
    EC_INSTA_USER = config["INSTA_USER"]
    EC_INSTA_PWD = config["INSTA_PWD"]

    bot = Bot()
    bot.login(username=EC_INSTA_USER, password=EC_INSTA_PWD)
    bot.upload_photo("path_to_your_photo", caption="your_caption")


if __name__ == "__main__":
    post_photo_to_instagram(
        "Screenshot 2023-07-21 at 16.13.27.png", "AI generated test")
