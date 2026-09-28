import json
import time
from pathlib import Path

import requests




BOT_TOKEN = "8631752643:AAHiI0W_wHqABteDpCWjFvGL06w5TC4ElE8"
CHAT_ID = "@kanda_factory_1n"



ROOT_FOLDER = Path("erome_videos")

# Telegram media group max = 10
BATCH_SIZE = 100

# Delay between albums
DELAY_BETWEEN_GROUPS = 2

# Delay between folders
DELAY_BETWEEN_FOLDERS = 3


# ==========================================
# SUPPORTED FILE TYPES
# ==========================================

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


# ==========================================
# SEND MEDIA GROUP
# ==========================================

def send_media_group(media_files, folder_name):

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

            # --------------------------
            # IMAGE
            # --------------------------

            if extension in IMAGE_EXTENSIONS:

                media_type = "photo"

                if extension == ".png":
                    mime_type = "image/png"

                elif extension == ".webp":
                    mime_type = "image/webp"

                else:
                    mime_type = "image/jpeg"

            # --------------------------
            # VIDEO
            # --------------------------

            else:

                media_type = "video"
                mime_type = "video/mp4"

            # --------------------------------
            # FOLDER NAME AS CAPTION
            # --------------------------------

            media_item = {
                "type": media_type,
                "media": f"attach://{field_name}",
                "caption": folder_name
            }

            if media_type == "video":

                media_item["supports_streaming"] = True

            media.append(media_item)

            files[field_name] = (
                file_path.name,
                file_handle,
                mime_type
            )

        # --------------------------------
        # REQUEST
        # --------------------------------

        data = {
            "chat_id": CHAT_ID,
            "media": json.dumps(media)
        }

        print()
        print(f"📤 Sending folder: {folder_name}")

        for file_path in media_files:
            print("   →", file_path.name)

        response = requests.post(
            url,
            data=data,
            files=files,
            timeout=1800
        )

        result = response.json()

        if result.get("ok"):

            print(f"✅ Folder sent: {folder_name}")

            return True

        else:

            print("❌ Telegram error:")
            print(result)

            return False

    except Exception as e:

        print("❌ Error:", e)

        return False

    finally:

        for file_handle in opened_files:

            file_handle.close()


# ==========================================
# SEND SINGLE MEDIA
# ==========================================

def send_single_media(file_path, folder_name):

    extension = file_path.suffix.lower()

    if extension in IMAGE_EXTENSIONS:

        endpoint = "sendPhoto"

        if extension == ".png":
            mime_type = "image/png"

        elif extension == ".webp":
            mime_type = "image/webp"

        else:
            mime_type = "image/jpeg"

        field_name = "photo"

    else:

        endpoint = "sendVideo"
        mime_type = "video/mp4"
        field_name = "video"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{endpoint}"

    try:

        with open(file_path, "rb") as file:

            response = requests.post(
                url,
                data={
                    "chat_id": CHAT_ID,
                    "caption": folder_name
                },
                files={
                    field_name: (
                        file_path.name,
                        file,
                        mime_type
                    )
                },
                timeout=1800
            )

        result = response.json()

        if result.get("ok"):

            print(f"✅ Sent: {file_path.name}")

            return True

        print("❌ Telegram error:")
        print(result)

        return False

    except Exception as e:

        print("❌ Error:", e)

        return False


# ==========================================
# GET MEDIA FROM ONE FOLDER
# ==========================================

def get_folder_media(folder):

    media = []

    for file_path in folder.iterdir():

        if not file_path.is_file():
            continue

        extension = file_path.suffix.lower()

        if (
            extension in IMAGE_EXTENSIONS
            or
            extension in VIDEO_EXTENSIONS
        ):

            media.append(file_path)

    # Keep filename order
    media.sort(key=lambda x: x.name.lower())

    return media


# ==========================================
# MAIN
# ==========================================

def main():

    if not ROOT_FOLDER.exists():

        print(f"❌ Folder not found: {ROOT_FOLDER}")

        return

    # --------------------------------------
    # GET ONLY DIRECT SUBFOLDERS
    # --------------------------------------

    folders = [
        folder
        for folder in ROOT_FOLDER.iterdir()
        if folder.is_dir()
    ]

    folders.sort(key=lambda x: x.name.lower())

    if not folders:

        print("❌ No subfolders found.")

        return

    print(f"📁 Found {len(folders)} folders")

    print("=" * 60)

    # ======================================
    # PROCESS EACH FOLDER
    # ======================================

    for folder in folders:

        folder_name = folder.name

        media_files = get_folder_media(folder)

        if not media_files:

            print()
            print(f"⚠️ Skipping empty folder: {folder_name}")

            continue

        print()
        print("=" * 60)
        print(f"📁 FOLDER: {folder_name}")
        print(f"📦 MEDIA: {len(media_files)}")

        # ----------------------------------
        # Split folder into groups of 10
        # ----------------------------------

        for start in range(
            0,
            len(media_files),
            BATCH_SIZE
        ):

            batch = media_files[
                start:start + BATCH_SIZE
            ]

            group_number = (
                start // BATCH_SIZE
            ) + 1

            print()
            print(
                f"📦 {folder_name} "
                f"→ Group {group_number} "
                f"({len(batch)} files)"
            )

            # --------------------------------
            # 2+ FILES
            # --------------------------------

            if len(batch) >= 2:

                success = send_media_group(
                    batch,
                    folder_name
                )

                if not success:

                    print(
                        f"❌ Failed folder: "
                        f"{folder_name}"
                    )

                    break

            # --------------------------------
            # ONLY 1 FILE
            # --------------------------------

            else:

                send_single_media(
                    batch[0],
                    folder_name
                )

            # Wait before next album

            if start + BATCH_SIZE < len(media_files):

                time.sleep(
                    DELAY_BETWEEN_GROUPS
                )

        # ----------------------------------
        # Folder finished
        # ----------------------------------

        print()
        print(
            f"✅ Finished folder: "
            f"{folder_name}"
        )

        time.sleep(
            DELAY_BETWEEN_FOLDERS
        )

    print()
    print("=" * 60)
    print("🎉 ALL FOLDERS FINISHED")
    print("=" * 60)


# ==========================================
# RUN
# ==========================================

if __name__ == "__main__":
    main()
