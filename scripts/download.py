import os
from yt_dlp import YoutubeDL
from pathlib import Path
import json
import subprocess
import glob

urls_path = "./data/urls/video_urls.json"
video_out_path = Path("./data/downloads")
metadata_path = "./data/video_data"

result = {}

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

    return metadata
    
def get_video_id(url : str):
    id = url.split("v=")[-1].split("&")[0]
    return id

def get_video_info_other(video_url):
    with YoutubeDL({'quiet' : True}) as ydl:
        info = ydl.extract_info(video_url, download=False)
        return {
            'video_views': info.get('view_count'),
            'channel_name' : info.get('uploader'),
            'video_title' : info.get('title'),
            'avg_rating' : info.get('average_rating')
        }

def main():
    urls = []

    # assumes each url on its own line
    with open(urls_path, 'r') as f:
        data = json.load(f)

        count = 0
        for i in data:
            url = i["url"]
            urls.append(url)
            id = get_video_id(url)
            result[id] = i
            count += 1

    
    # with open(f"{metadata_path}/report.json", "w") as f:
    #     json.dump(result, f, indent=4)

    # mds = {}

    for url in urls:
        try:
            video_id = get_video_id(url)

            print(f"Processing video : {video_id}")

            download_video(url, video_id)
            md = extract_metadata(video_id)
            # mds[video_id] = md
            other_data = get_video_info_other(url)

            # result stores curr report
            result[video_id]["metadata"] = md
            result[video_id]["other_info"] = other_data

            matching_files = glob.glob(f"{video_out_path}/{video_id}.*")
            for file_path in matching_files:
                os.remove(file_path)

        except Exception as e:
            print(f"Encountered an error in downloading or parsing:\n{e}\n")
    
    with open(f"{metadata_path}/report.json", "w") as f:
        json.dump(result, f, indent=4)

    ## ACKNOWLEDGING HOW STUPID AND INEFFICIENT IT IS TO BASICALLY STORE A DICTIONARY IN A FILE TEMPORARILY -- NOT INTERESTED....
    # curr = {}
    # with open(f"{metadata_path}/report.json", "r") as f:
    #     curr = json.load(f)

    # for url in urls:
    #     id = get_video_id(url)
    #     other_info = get_video_info_other(url)

    #     curr[id]["metadata"] = mds[id]
    #     curr[id]["other_info"] = other_info
    
    # with open(f"{metadata_path}/report.json", "w") as f:
    #     json.dump(curr, f, indent=4)

        


if __name__ == "__main__":
    main()



