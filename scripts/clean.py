import json

dic = {}

with open("./data/video_data/report.json", "r") as f:
    dic = json.load(f)

with open("./data/video_data/report.json", "w") as f:
    json.dump(dic, f, indent=4 )