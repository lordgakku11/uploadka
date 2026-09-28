import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests


def build_headers() -> dict:
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "Referer": "https://www.erome.com/",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Range": "bytes=0-",
    }


def sanitize_folder_name(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
    return cleaned or "untitled_album"


def download_file(url: str, output_path: str | Path, chunk_size: int = 1024 * 1024) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    response = None
    for _ in range(2):
        try:
            response = requests.get(url, headers=build_headers(), stream=True, timeout=60)
            if response.status_code in (200, 206):
                break
            response.close()
        except requests.RequestException:
            if response is not None:
                response.close()
            response = None
            raise
    if response is None:
        raise requests.RequestException("Failed to establish a readable connection to the media URL")

    try:
        response.raise_for_status()
        content_range = response.headers.get("Content-Range", "")
        if content_range and "/" in content_range:
            total_size = int(content_range.split("/")[-1])
        else:
            total_size = int(response.headers.get("Content-Length", 0) or 0)

        downloaded = 0
        with output.open("wb") as file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if not chunk:
                    continue
                file.write(chunk)
                downloaded += len(chunk)

                if total_size:
                    percent = (downloaded / total_size) * 100
                    print(f"Downloading... {downloaded}/{total_size} bytes ({percent:.1f}%)", end="\r", flush=True)

        print("\nDownload complete.")
        return output
    finally:
        response.close()


def get_album_links(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    html = response.text

    # Find divs containing class="album"
    album_pattern = re.compile(
        r'<div[^>]*class=["\'][^"\']*\balbum\b[^"\']*["\'][^>]*>.*?</div>',
        re.IGNORECASE | re.DOTALL
    )

    albums = album_pattern.findall(html)

    print(f"Found {len(albums)} album elements\n")

    album_links = []
    count = 0

    for album in albums:
        # Find href inside the album div
        match = re.search(
            r'<a[^>]+href=["\']([^"\']+)["\']',
            album,
            re.IGNORECASE
        )

        if match:
            href = match.group(1)

            # Convert relative URL to full URL
            full_url = urljoin(url, href)

            print(full_url)
            album_links.append(full_url)

            count += 1

            if count >= 10:
                break

    return album_links


url = input("Enter URL: ").strip()

album_links = get_album_links(url)

for album_url in album_links:
    album_response = requests.get(album_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    album_response.raise_for_status()
    album_html = album_response.text

    title_match = re.search(
        r'<h1[^>]*class=["\'][^"\']*\balbum-title-page\b[^"\']*["\'][^>]*>(.*?)</h1>',
        album_html,
        re.IGNORECASE | re.DOTALL,
    )
    album_title = re.sub(r'<.*?>', '', title_match.group(1)).strip() if title_match else "No title found"

    image_links = []
    for match in re.finditer(
        r'<div[^>]*class=["\'][^"\']*\bimg-box\b[^"\']*["\'][^>]*>.*?<img[^>]*src=["\']([^"\']+)["\']',
        album_html,
        re.IGNORECASE | re.DOTALL,
    ):
        image_links.append(urljoin(album_url, match.group(1)))

    mp4_links = []
    for match in re.finditer(
        r'<source[^>]*src=["\']([^"\']+\.mp4[^"\']*)["\']',
        album_html,
        re.IGNORECASE,
    ):
        mp4_links.append(urljoin(album_url, match.group(1)))

    print(f"\nAlbum: {album_url}")
    print(f"Title: {album_title}")

    folder_name = sanitize_folder_name(album_title)
    album_folder = Path("erome_videos") / folder_name
    album_folder.mkdir(parents=True, exist_ok=True)
    print(f"Folder: {album_folder}")

    all_links = list(dict.fromkeys(image_links + mp4_links))
    for index, media_url in enumerate(all_links, 1):
        parsed = urlparse(media_url)
        filename = Path(parsed.path).name or f"media_{index}"
        output_path = album_folder / filename
        try:
            download_file(media_url, output_path)
            print(f"Saved: {output_path}")
        except (requests.RequestException, OSError, ValueError) as error:
            print(f"Failed to download {media_url}: {error}")

    if image_links:
        print("Image links:")
        for link in image_links:
            print(link)
    else:
        print("No image links found")

    if mp4_links:
        print("MP4 links:")
        for link in mp4_links:
            print(link)
    else:
        print("No MP4 links found")