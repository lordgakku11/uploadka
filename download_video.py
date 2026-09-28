import argparse
from pathlib import Path
from urllib.parse import urlparse

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
        raise requests.RequestException("Failed to establish a readable connection to the video URL")

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


def main() -> None:
    parser = argparse.ArgumentParser(description="Download a video from a direct MP4 URL.")
    parser.add_argument("url", nargs="?", default="https://v50.erome.com/9088/z5H2NxNY/re371skW_720p.mp4", help="Video URL to download")
    parser.add_argument("-o", "--output", default=None, help="Output filename or path")
    args = parser.parse_args()

    url = args.url
    if args.output:
        output_path = args.output
    else:
        parsed = urlparse(url)
        filename = Path(parsed.path).name or "downloaded_video.mp4"
        output_path = filename

    print(f"Downloading: {url}")
    print(f"Saving to: {output_path}")
    download_file(url, output_path)


if __name__ == "__main__":
    main()
