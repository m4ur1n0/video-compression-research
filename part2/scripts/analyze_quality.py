import os
import json
import csv
import subprocess
import argparse

def ffprobe_metadata(path):
    # get dict of codec_name, width, height, bitrate, duration, filesize

    cmd = [
        'ffprobe', '-v', 'error',
        '-print_format', 'json',
        '-show_streams', '-show_format',
        path
    ]

    p = subprocess.run(cmd, capture_output=True, text=True, check=True)

    info = json.loads(p.stdout)

    fmt = info.get('format', {})
    video_streams = [s for s in info.get('streams', []) if s['codec_type'] == 'video']
    vs = video_streams[0] if video_streams else {}

    return {
        'codec' : vs.get('codec_name'),
        'width' : vs.get('width'),
        'height' : vs.get('height'),
        'bit_rate' : int(fmt.get('bit_rate', 0)),
        'duration' : float(fmt.get('duration', 0)),
        'filesize' : os.path.getsize(path)
    }


def compute_vmaf_ssim(ref, dist, vmaf_model, tmp_log):
    # run ffmpeg libvmaf+ssim filer, capture metrics
    # ref = reference video
    # dist = distorted download video
    # vmaf_model = vmaf model
    # tmp_log = path to where output should be temporarilly logged

    cmd = [
        'ffmpeg', '-hide_banner', '-y',
        '-i', ref, '-i', dist,
        '-lavfi',
        "[0:v]scale=iw:ih[ref];"
        "[1:v]scale=iw:ih[dist];"
        f"[ref][dist]libvmaf=model_path={vmaf_model}:log_path={tmp_log}:log_fmt=json,ssim=ssim.log",
        "-f", "null", "-"
    ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    with open(tmp_log, 'r') as f:
        # go through the output
        data = json.load(f)

    # single frame aggregated score
    vm = data.get('pooled_metrics', {})

    ssim = {}
    if os.path.exists('ssim.log'):
        with open('ssim.log', 'r') as f:
            # parse
            last = f.readlines()[-1].strip().split()
            ssim = {kv.split(":")[0] : float(kv.split(":")[1]) for kv in last.split()}

    # just return the high end of the confidence interval?
    return {
        'VMAF_score' : vm.get('vmaf', None),
        'VMAF_confidence' : vm.get('ci_high', None),
        'SSIM_all' : ssim.get('All'),
    }


def main(args):

    # args takes in name of originals directory (orig_dir), name of downloads directory (dl_dir), path to csv output file (out_csv), vmaf model (vmaf_model)

    originals = {os.path.splitext(f)[0] : os.path.join(args.orig_dir, f)
                 for f in os.listdir(args.orig_dir)
                 if f.lower().endswith(('.mp4', '.mkv', '.mov'))
                 }
    
    # for csv
    fieldnames = [
        'video_id', 'timepoint', 
        'orig_codec', 'orig_width', 'orig_height', 'orig_bitrate', 'orig_duration', 'orig_filesize', 
        'dl_codec', 'dl_width', 'dl_height', 'dl_bitrate', 'dl_duration', 'dl_filesize',
        'VMAF_score', 'VMAF_confidence', 'SSIM_all'
    ]

    with open(args.out_csv, 'w', newline='') as csvf:
        writer = csv.DictWriter(csvf, fieldnames=fieldnames)
        writer.writeheader()

        for fname in os.listdir(args.dl_dir):
            if not fname.lower().endswith(('.mp4', '.mkv', '.mov')):
                continue

            vidid, tp = os.path.splitext(fname)[0].rsplit('_', 1)
            orig_path = originals.get(vidid)
            dl_path = os.path.join(args.dl_dir, fname)

            if not orig_path:
                print(f"ERROR : No original for {vidid}, skipping")
                continue

            # read metadata
            orig_m = ffprobe_metadata(orig_path)
            dwn_m = ffprobe_metadata(dl_path)

            # quality
            tmp_log = f"vmaf_{vidid}_{tp}.json"
            qm = compute_vmaf_ssim(orig_path, dl_path, args.vmaf_model, tmp_log)

            row = {
                'video_id': vidid,
                'timepoint': tp,
                # original meta
                'orig_codec': orig_m['codec'],
                'orig_width': orig_m['width'],
                'orig_height': orig_m['height'],
                'orig_bitrate': orig_m['bit_rate'],
                'orig_duration': orig_m['duration'],
                'orig_filesize': orig_m['filesize'],
                # downloaded meta
                'dl_codec': dwn_m['codec'],
                'dl_width': dwn_m['width'],
                'dl_height': dwn_m['height'],
                'dl_bitrate': dwn_m['bit_rate'],
                'dl_duration': dwn_m['duration'],
                'dl_filesize': dwn_m['filesize'],
                # quality
                **qm
            }

            writer.writerow(row)

            os.remove(tmp_log)
            if os.path.exists('ssim.log'):
                os.remove('ssim.log')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description="Controlled-upload SSIM/VMAF analysis")
    p.add_argument('--orig_dir', default='originals', help="Directory of original files")
    p.add_argument('--dl_dir',   default='downloads', help="Directory of YouTube downloads")
    p.add_argument('--vmaf_model', default='vmaf_v0.6.1.json',
                   help="Path to VMAF model JSON")
    p.add_argument('--out_csv', default='quality_results.csv',
                   help="Where to write CSV results")
    args = p.parse_args()
    main(args)