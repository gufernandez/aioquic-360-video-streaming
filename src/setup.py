import argparse
import os

def main(video_url: str):
    os.system("rm -rf ../data/video_encoding")
    os.system("rm -rf ../data/segments")

    os.system("mkdir ../data/video_encoding")
    os.system("mkdir ../data/segments")

    # Video download
    os.system("youtube-dl -o \"../data/video_encoding/downloaded.mp4\" -f best "+video_url)

    # Trim video
    os.system("ffmpeg -ss 00:00:00 -i \"../data/video_encoding/downloaded.mp4\" -t 00:01:00 -c copy \"../data/video_encoding/trimmed.mp4\"")

    # Video conversion to YUV format
    os.system("ffmpeg -i \"../data/video_encoding/trimmed.mp4\" \"../data/video_encoding/input.yuv\"")

    # Tile encoding 1Mbps
    os.system("kvazaar -i \"../data/video_encoding/input.yuv\" --input-res 3840x2160 -o \"../data/video_encoding/output.hvc\" "
              "--tiles 10x20 --slices tiles --mv-constraint frametilemargin --bitrate 1Mbps --period 30 --input-fps 30")

    # Tile encoding 2Mbps
    os.system(
        "kvazaar -i \"../data/video_encoding/input.yuv\" --input-res 3840x2160 -o \"../data/video_encoding/output2.hvc\" "
        "--tiles 10x20 --slices tiles --mv-constraint frametilemargin --bitrate 2Mbps --period 30 --input-fps 30")

    # Tile encoding 5Mbps
    os.system(
        "kvazaar -i \"../data/video_encoding/input.yuv\" --input-res 3840x2160 -o \"../data/video_encoding/output5.hvc\" "
        "--tiles 10x20 --slices tiles --mv-constraint frametilemargin --bitrate 5Mbps --period 30 --input-fps 30")

    # Tile packer
    os.system("MP4Box -add \"../data/video_encoding/output.hvc\":split_tiles -new \"../data/video_encoding/video_tiled_1.mp4\"")

    # Tile packer
    os.system("MP4Box -add \"../data/video_encoding/output2.hvc\":split_tiles -new \"../data/video_encoding/video_tiled_2.mp4\"")

    # Tile packer
    os.system("MP4Box -add \"../data/video_encoding/output5.hvc\":split_tiles -new \"../data/video_encoding/video_tiled_5.mp4\"")

    # Split tiles
    os.system("MP4Box -dash 1000 -rap -frag-rap -profile live -out \"../data/segments/dash_tiled_1.mpd\""
              " \"../data/video_encoding/video_tiled_1.mp4\"")

    # Split tiles
    os.system("MP4Box -dash 1000 -rap -frag-rap -profile live -out \"../data/segments/dash_tiled_2.mpd\""
              " \"../data/video_encoding/video_tiled_2.mp4\"")

    # Split tiles
    os.system("MP4Box -dash 1000 -rap -frag-rap -profile live -out \"../data/segments/dash_tiled_5.mpd\""
              " \"../data/video_encoding/video_tiled_5.mp4\"")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video encoding setup")
    parser.add_argument(
        "url",
        type=str,
        help="the 360 video URL to be downloaded"
    )
    args = parser.parse_args()

    main(args.url)
