import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

REPORT_PATH = './data/video_data/report.json'

def load_video_data(data):

    video_stream = next(s for s in data["metadata"]['streams'] if s['codec_type'] == 'video')
    audio_stream = next(s for s in data["metadata"]['streams'] if s['codec_type'] == 'audio')

    format_data = data['metadata']['format']

    return {
        "filename": format_data["filename"].strip(),
        "duration_sec": float(format_data["duration"]),
        "bitrate": int(format_data["bit_rate"]),
        "video_codec": video_stream["codec_name"],
        "width": video_stream["width"],
        "height": video_stream["height"],
        "frame_rate": eval(video_stream["r_frame_rate"]),
        "video_bitrate": int(video_stream["bit_rate"]),
        "audio_bitrate": int(audio_stream["bit_rate"]),
        "views" : int(data["other_info"]["video_views"]),
        "channel_name" : data["other_info"]["channel_name"],
        "title" : data["other_info"]["video_title"],
        "avg_rating" : data["other_info"]["avg_rating"]

    }

def load_report_data():

    with open(REPORT_PATH) as f:
        data = json.load(f)
    
    formatted_data = {}

    for video in data:
        formatted_data[video] = load_video_data(data[video])

    return formatted_data

all_data = load_report_data()
df = pd.DataFrame.from_dict(all_data, orient="index").reset_index(names="video_id")

print(df)

## derive some metrics on our own B)

df["pixels"] = df["width"] * df["height"]
df["bitrate_per_pixel"] = df["video_bitrate"] / df["pixels"]
df["bitrate_per_second"] = df["video_bitrate"] / df["duration_sec"]


## BITRATE PER PIXEL VS. VIDEO VIEWS
sns.scatterplot(data = df, x="views", y="bitrate_per_pixel")
plt.xscale("log")
plt.title("Bitrate per Pixel vs. Views")
plt.xlabel("Video Views (log scale)")
plt.ylabel("Bitrate per Pixel")
plt.show()

## AVERAGE VIEWS BY CODEC

avg_views = df.groupby("video_codec")["views"].mean().sort_values(ascending=False)

avg_views.plot(kind="bar")
plt.yscale("log")
plt.title("Average views By Codec Type")
plt.xlabel("Video Codec")
plt.ylabel("Average # views (log scale)")
plt.show()