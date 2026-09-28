import json
import time
from pathlib import Path

import requests
BOT_TOKEN = "8631752643:AAHiI0W_wHqABteDpCWjFvGL06w5TC4ElE8"
CHAT_ID = "@kanda_factory_1n"

# =========================
# CONFIG
# =========================

BOT_TOKEN = "YOUR_NEW_BOT_TOKEN"
CHAT_ID = "@your_channel_or_group"

ROOT_FOLDER = Path("erome_videos")

BATCH_SIZE = 10
DELAY_BETWEEN_GROUPS = 2


# =========================
# SUPPORTED FILES
# =========================

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
}

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov"
}


# =========================
# FIND ALL MEDIA
# =========================

def get_all_media():

    media_files = []

    # recursively find everything inside folder1
    for path in ROOT_FOLDER.rglob("*"):

        if not path.is_file():
            continue

        extension = path.suffix.lower()

        if extension in IMAGE_EXTENSIONS or extension in VIDEO_EXTENSIONS:
            media_files.append(path)

    # sort by path so folder order stays predictable
    media_files.sort(key=lambda x: str(x).lower())

    return media_files


# =========================
# SEND MEDIA GROUP
# =========================

def send_media_group(media_files):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMediaGroup"

    media = []
    files = {}
    opened_files = []

    try:

        for index, file_path in enumerate(media_files):

            field_name = f"file{index}"

            file_handle = open(file_path, "rb")
            opened_files.append(file_handle)

            extension = file_path.suffix.lower()

            # Determine Telegram media type
            if extension in IMAGE_EXTENSIONS:
                media_type = "photo"
                mime_type = "image/jpeg"

                if extension == ".png":
                    mime_type = "image/png"
                elif extension == ".webp":
                    mime_type = "image/webp"

            else:
                media_type = "video"
                mime_type = "video/mp4"

            # Filename without extension as caption
            caption = file_path.stem

            media_item = {
                "type": media_type,
                "media": f"attach://{field_name}",
                "caption": caption
            }

            if media_type == "video":
                media_item["supports_streaming"] = True

            media.append(media_item)

            files[field_name] = (
                file_path.name,
                file_handle,
                mime_type
            )

        data = {
            "chat_id": CHAT_ID,
            "media": json.dumps(media)
        }

        print()
        print("Sending:")
        
        for file_path in media_files:
            print("  →", file_path)

        response = requests.post(
            url,
            data=data,
            files=files,
            timeout=1800
        )

        result = response.json()

        if result.get("ok"):
            print("✅ Media group sent successfully")
            return True

        print("❌ Telegram error:")
        print(result)

        return False

    except Exception as e:

        print("❌ Error:", e)
        return False

    finally:

        for file_handle in opened_files:
            file_handle.close()


# =========================
# MAIN
# =========================

def main():

    if not ROOT_FOLDER.exists():
        print(f"❌ Folder not found: {ROOT_FOLDER}")
        return

    print("Scanning folders...")

    all_media = get_all_media()

    if not all_media:
        print("❌ No images/videos found.")
        return

    print()
    print(f"Found {len(all_media)} media files.")

    print()
    print("Files found:")

    for file_path in all_media:
        print("  ", file_path)

    print()
    print("=" * 50)

    # Telegram allows max 10 items in one media group
    for start in range(0, len(all_media), BATCH_SIZE):

        batch = all_media[start:start + BATCH_SIZE]

        group_number = (start // BATCH_SIZE) + 1

        print()
        print(f"📦 Sending group {group_number}")
        print(f"   Files: {len(batch)}")

        # sendMediaGroup needs at least 2 media
        if len(batch) >= 2:

            success = send_media_group(batch)

            if not success:
                print("Stopping because sending failed.")
                break

        else:

            print("⚠️ Only 1 file left.")
            print("Use sendPhoto/sendVideo for a single file.")

        # Wait before next group
        if start + BATCH_SIZE < len(all_media):

            print(f"Waiting {DELAY_BETWEEN_GROUPS} seconds...")
            time.sleep(DELAY_BETWEEN_GROUPS)

    print()
    print("=" * 50)
    print("✅ Finished")


if __name__ == "__main__":
    main()