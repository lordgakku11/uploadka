import os
from pathlib import Path
import requests
import time


# =========================================================
# CONFIGURATION
# =========================================================

BOT_TOKEN = "8631752643:AAHiI0W_wHqABteDpCWjFvGL06w5TC4ElE8"
CHAT_ID = "@kanda_factory_1n"

VIDEOS_FOLDER = Path("videos")

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".mkv",
    ".webm"
}


# =========================================================
# TELEGRAM UPLOAD FUNCTION
# =========================================================

def upload_video(video_path):
    """
    Upload one local video file to Telegram.
    Filename without extension is used as caption.
    """

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"

    # Example:
    # my_video.mp4 -> "my_video"
    caption = video_path.stem

    print("\n" + "=" * 60)
    print(f"Uploading: {video_path.name}")
    print(f"Caption:   {caption}")
    print("=" * 60)

    try:
        with open(video_path, "rb") as video_file:

            files = {
                "video": (
                    video_path.name,
                    video_file,
                    "video/mp4"
                )
            }

            data = {
                "chat_id": CHAT_ID,
                "caption": caption,
                "supports_streaming": True
            }

            response = requests.post(
                url,
                data=data,
                files=files,
                timeout=1200
            )

        if response.status_code == 200:

            result = response.json()

            if result.get("ok"):
                print("SUCCESS:", video_path.name)
                return True

            print("Telegram error:")
            print(result)
            return False

        else:
            print("HTTP ERROR:", response.status_code)
            print(response.text)
            return False

    except FileNotFoundError:
        print("File not found:", video_path)
        return False

    except requests.exceptions.Timeout:
        print("Upload timed out:", video_path.name)
        return False

    except requests.exceptions.ConnectionError as e:
        print("Connection error:", e)
        return False

    except Exception as e:
        print("Unexpected error:", e)
        return False


# =========================================================
# FIND ALL VIDEOS
# =========================================================

def get_videos():

    if not VIDEOS_FOLDER.exists():
        print("ERROR: videos folder not found!")
        print("Expected location:")
        print(VIDEOS_FOLDER.resolve())
        return []

    videos = []

    # rglob() searches inside all subfolders
    for file in VIDEOS_FOLDER.rglob("*"):

        if file.is_file() and file.suffix.lower() in VIDEO_EXTENSIONS:
            videos.append(file)

    # Keep predictable order
    videos.sort()

    return videos


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 60)
    print("Telegram Video Uploader")
    print("=" * 60)

    videos = get_videos()

    if not videos:
        print("No videos found.")
        return

    print(f"\nFound {len(videos)} video(s):\n")

    for index, video in enumerate(videos, start=1):
        print(f"{index}. {video}")

    print("\nStarting upload...\n")

    successful = 0
    failed = 0

    for index, video_path in enumerate(videos, start=1):

        print(f"\n[{index}/{len(videos)}]")

        success = upload_video(video_path)

        if success:
            successful += 1
        else:
            failed += 1

        # Small delay between uploads
        if index < len(videos):
            print("Waiting 2 seconds...")
            time.sleep(2)

    # =====================================================
    # SUMMARY
    # =====================================================

    print("\n")
    print("=" * 60)
    print("UPLOAD FINISHED")
    print("=" * 60)

    print(f"Total videos : {len(videos)}")
    print(f"Successful   : {successful}")
    print(f"Failed       : {failed}")

    print("=" * 60)


if __name__ == "__main__":
    main()