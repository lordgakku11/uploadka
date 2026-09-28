import re
from pathlib import Path

import requests
from html.parser import HTMLParser
from urllib.parse import urljoin

videos_directory = Path("videos")
videos_directory.mkdir(exist_ok=True)


class VideoCardParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cards = []
        self._card = None
        self._card_depth = 0
        self._capture = None
        self._text = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        classes = set(attributes.get("class", "").split())

        if tag == "div" and "video-card" in classes:
            self._card = {"href": "", "image": "", "title": "", "duration": "", "views": ""}
            self._card_depth = 1
        elif self._card is not None and tag == "a" and "video-card-link" in classes:
            self._card["href"] = attributes.get("href", "")
        elif self._card is not None and tag == "img":
            self._card["image"] = attributes.get("src", "")
            self._card["title"] = attributes.get("alt", "")
        elif self._card is not None and tag == "div" and classes & {"video-duration", "video-views"}:
            field = next(iter(classes & {"video-duration", "video-views"}))
            self._capture = field.removeprefix("video-")
            self._text = []

        if self._card is not None and tag == "div" and "video-card" not in classes:
            self._card_depth += 1

    def handle_data(self, data):
        if self._capture:
            self._text.append(data)

    def handle_endtag(self, tag):
        if self._card is not None and tag == "div":
            if self._capture:
                self._card[self._capture] = " ".join("".join(self._text).split())
                self._capture = None
                self._text = []
            self._card_depth -= 1
        if self._card is not None and self._card_depth == 0:
            if self._card["href"] or self._card["image"] or self._card["title"]:
                self.cards.append(self._card)
            self._card = None


class VideoSourceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sources = []

    def handle_starttag(self, tag, attrs):
        if tag != "source":
            return

        source = dict(attrs).get("src", "")
        if source:
            self.sources.append(source)


def safe_filename(title, fallback):
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", title).strip(" .")
    return filename or fallback


url = "https://nepaliporn.video/videos/sort/most_views"

response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
response.raise_for_status()
html = response.text

parser = VideoCardParser()
parser.feed(html)

cards = parser.cards[:10]

if cards:
    for i, card in enumerate(cards, 1):
        print(f"\nCard {i}")
        print("Title:", card["title"] or "(none)")
        print("Link:", card["href"] or "(none)")
        print("Image:", card["image"] or "(none)")
        print("Duration:", card["duration"] or "(none)")
        print("Views:", card["views"] or "(none)")
else:
    print("No video cards found in the page source.")

mp4_urls = []
for index, card in enumerate(cards, 1):
    card_url = urljoin(url, card["href"])
    if not card["href"]:
        print(f"Card {index}: missing detail link")
        mp4_urls.append("")
        continue

    try:
        card_response = requests.get(card_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        card_response.raise_for_status()
        source_parser = VideoSourceParser()
        source_parser.feed(card_response.text)
        mp4_url = next(
            (urljoin(card_url, source) for source in source_parser.sources if ".mp4" in source.lower()),
            "",
        )
    except requests.RequestException as error:
        print(f"Card {index}: request failed ({error})")
        mp4_url = ""

    mp4_urls.append(mp4_url)
    print(f"Card {index} MP4:", mp4_url or "not found")

with open("mp4_urls.txt", "w", encoding="utf-8") as output_file:
    for mp4_url in mp4_urls:
        if mp4_url:
            output_file.write(mp4_url + "\n")

print(f"Saved {len([url for url in mp4_urls if url])} MP4 URL(s) to mp4_urls.txt")


downloaded_urls = set()
used_filenames = set()
downloaded_count = 0
skipped_count = 0

for index, (card, mp4_url) in enumerate(zip(cards, mp4_urls), 1):
    if not mp4_url or mp4_url in downloaded_urls:
        skipped_count += 1
        continue

    downloaded_urls.add(mp4_url)
    title = safe_filename(card["title"], f"video_{index}")
    filename = f"{title}.mp4"
    suffix = 2
    while filename in used_filenames:
        filename = f"{title} ({suffix}).mp4"
        suffix += 1

    output_path = videos_directory / filename
    used_filenames.add(filename)
    file_was_downloaded = output_path.exists()

    try:
        if not file_was_downloaded:
            with requests.get(mp4_url, headers={"User-Agent": "Mozilla/5.0"}, stream=True, timeout=60) as video_response:
                video_response.raise_for_status()
                with output_path.open("wb") as video_file:
                    for chunk in video_response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            video_file.write(chunk)
            downloaded_count += 1
            print(f"Downloaded: {output_path}")
        else:
            print(f"Already exists: {output_path}")
    except (requests.RequestException, OSError) as error:
        if not file_was_downloaded and output_path.exists():
            output_path.unlink()
        print(f"Card {index}: download failed ({error})")

print(
    f"Downloaded {downloaded_count} video(s); "
    f"skipped {skipped_count} duplicate or missing URL(s)."
)