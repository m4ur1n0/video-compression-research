import os
from yt_dlp import YoutubeDL
from pathlib import Path
import json
import subprocess

urls_path = "./data/urls/most_popular_urls.txt"
video_out_path = Path("./data/downloads")
metadata_path = "./data/video_data"

def download_video(url : str, video_id : str) :
    ydl_options = {
        "outtmpl": str(f'{video_out_path}/{video_id}.%(ext)s'),
        "format" : "bestvideo+bestaudio/best",
        "merge_output_format" : "mp4",
        "quiet" : True
    }

    with YoutubeDL(ydl_options) as ydl:
        ydl.download(url)


def extract_metadata(video_id: str):
    video_path = next(video_out_path.glob(f"{video_id}.*"))
    cmd = [
        'ffprobe',
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        str(video_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    metadata = json.loads(result.stdout)

    with open(f"{metadata_path}/{video_id}_metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)
    
def get_video_id(url : str):
    id = url.split("v=")[-1].split("&")[0]
    return id

def main():
    urls = []

    # assumes each url on its own line
    with open(urls_path, 'r') as f:
        urls = [url for url in f.readlines()]


    for url in urls:
        try:
            video_id = get_video_id(url)

            print(f"Processing video : {video_id}")

            download_video(url, video_id)
            extract_metadata(video_id)
        except Exception as e:
            print(f"Encountered an error in downloading or parsing:\n{e}\n")

if __name__ == "__main__":
    main()



