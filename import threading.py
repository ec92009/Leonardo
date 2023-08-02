import threading
import requests


def download_picture(url, filename):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(filename, 'wb') as file:
                file.write(response.content)
            return len(response.content)
        else:
            print(f"Failed to download: {url}")
            return None
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None


def main():
    picture_urls = [
        "https://example.com/picture1.jpg",
        "https://example.com/picture2.jpg",
        "https://example.com/picture3.jpg",
        "https://example.com/picture4.jpg",
        "https://example.com/picture5.jpg",
    ]

    results = {}
    threads = []
    for i, url in enumerate(picture_urls):
        thread = threading.Thread(target=lambda: results.update(
            {url: download_picture(url, f"picture{i + 1}.jpg")}))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Print the results
    for url, size in results.items():
        if size is not None:
            print(f"Downloaded: {url}, Size: {size} bytes")
        else:
            print(f"Failed to download: {url}")


if __name__ == "__main__":
    main()
