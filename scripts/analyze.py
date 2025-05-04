import json
import math
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

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
        "avg_rating" : data["other_info"]["avg_rating"],
        "channel_size" : data["channel_echelon"]

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

with open("./data/logs/dataframe.txt", "w") as f:
    f.write(df.to_string(index=False, na_rep="-"))

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

## BITRATE PER PIXEL PER FRAME VS. VIDEO VIEWS
df["bitrate_per_pixel_per_frame"] = df["bitrate_per_pixel"] / (df["frame_rate"] * df["duration_sec"])
df["log_views"] = np.log10(df["views"])
# print (f"CALC : \n { df['bitrate_per_pixel_per_frame'] } \n{df['bitrate_per_pixel']} \n/\n {df['frame_rate']} ")

sns.regplot(data=df, x="log_views", y="bitrate_per_pixel_per_frame")
# plt.xscale("log")
plt.title("Bitrate Per Pixel Per Frame vs. Video Popularity")
plt.xlabel("Log10(Video Views)")
plt.ylabel("Bitrate per pixel per frame")
plt.show()

## BITRATE VS VIDEO LENGTH
# df["log_bitrate"] = np.log10(df["bitrate"])

# filter out top 5% values
duration_threshold = df["duration_sec"].quantile(0.95)
bitrate_threshold = df["bitrate"].quantile(0.95)

filtered_df = df[(df["duration_sec"] < duration_threshold) & (df["bitrate"] < bitrate_threshold)]

sns.regplot(data=filtered_df, x="duration_sec", y="bitrate")
plt.title("Video Bitrate vs. Video Length")
plt.xscale("linear")
plt.xlabel("Video Length (Seconds)")
plt.ylabel("Video Bitrate")
plt.show()


## CHANNEL SIZE TO CODEC USED ANALYSIS

fig, axes = plt.subplots(1, 3, figsize=(18,5), sharey=True)

channel_sizes = ['small', 'medium', 'large']

for ax, size in zip(axes, channel_sizes):
    subset=df[df["channel_size"] == size]
    codec_counts = subset["video_codec"].value_counts()

    sns.barplot(x=codec_counts.index, y=codec_counts.values, ax=ax)
    ax.set_title(f"{size.capitalize()} Channels")
    ax.set_ylabel("Count")
    ax.set_xlabel("Codec" if size == "small" else "") ## only need the one y label


fig.suptitle("Most Common Codecs by Channel Size", fontsize=16)
plt.tight_layout(rect=[0, 0, 1, 0.95])
    
plt.show()

## AVERAGE VIEWS BY CODEC

avg_views = df.groupby("video_codec")["views"].mean().sort_values(ascending=False)

avg_views.plot(kind="bar")
plt.yscale("log")
plt.title("Average Views By Codec Type")
plt.xlabel("Video Codec")
plt.ylabel("Average # views (log scale)")
plt.show()


## VIEWS VS FRAMERATE -- avg views by framerate
# this one goes a bit backwards, but it could be interesting to see if higher-framerate viedeos tend to get more engagement.

df["rounded_frames"] = df["frame_rate"].apply(math.ceil)
avg_views_frmrt = df.groupby("rounded_frames")["views"].mean().sort_values(ascending=False)

avg_views_frmrt.plot(kind="bar")
plt.yscale("log")
plt.title("Average Views by Frame Rate of Video")
plt.xlabel("Frames Per Second")
plt.ylabel("Average Number of Views")
plt.show()


## BITRATE PER FRAME BY VIDEO VIEWS

df["bitrate_per_frame"] = df["video_bitrate"] / (df["frame_rate"] * df["duration_sec"])

sns.regplot(data=df, x="log_views", y="bitrate_per_frame")
plt.xlabel("Log10(Views)")
plt.ylabel("Bitrate Per Frame")
plt.title("Bitrate Per Frame vs. Video Popularity")
plt.show()
