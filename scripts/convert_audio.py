#!/usr/bin/env python3
"""
Convert audio files using ffmpeg. Supports the chain MP4 -> MP3 -> WAV.

Usage examples:
  python scripts/convert_audio.py --in outputs/bark_sample.mp4
  python scripts/convert_audio.py --in inputs/foo.mp4 --outdir outputs

If the input is not MP4, the script will attempt to convert to MP4 first.
"""
import argparse
import shutil
import subprocess
from pathlib import Path
import sys


def check_ffmpeg(cli_path: str | None = None):
    # If user supplied a path, prefer it
    if cli_path:
        p = Path(cli_path)
        if p.exists():
            return str(p)
        else:
            print('Provided ffmpeg path does not exist:', cli_path)
            sys.exit(2)

    # Try PATH
    ff = shutil.which('ffmpeg')
    if ff:
        return ff

    # Common Windows install locations to try
    candidates = [
        Path('C:/ffmpeg/bin/ffmpeg.exe'),
        Path('C:/Program Files/ffmpeg/bin/ffmpeg.exe'),
        Path(str(Path.home() / 'miniconda3' / 'pkgs' / 'ffmpeg' / 'Library' / 'bin' / 'ffmpeg.exe')),
        Path('C:/Program Files/Gyan/ffmpeg/bin/ffmpeg.exe'),
        Path(str(Path.home() / 'Downloads' / 'ffmpeg' / 'bin' / 'ffmpeg.exe')),
    ]
    for c in candidates:
        if c.exists():
            return str(c)

    print('ffmpeg not found on PATH or in common locations. Please install ffmpeg or pass --ffmpeg PATH')
    sys.exit(2)


def run(cmd):
    print('RUN:', ' '.join(cmd))
    res = subprocess.run(cmd, shell=False)
    if res.returncode != 0:
        raise RuntimeError(f'ffmpeg command failed: {cmd}')


def to_mp4(ffmpeg, src: Path, dst: Path):
    # Encode to AAC in MP4 container
    run([ffmpeg, '-y', '-i', str(src), '-c:a', 'aac', '-b:a', '192k', str(dst)])


def mp4_to_mp3(ffmpeg, src: Path, dst: Path):
    run([ffmpeg, '-y', '-i', str(src), '-vn', '-c:a', 'libmp3lame', '-b:a', '192k', str(dst)])


def mp3_to_wav(ffmpeg, src: Path, dst: Path):
    run([ffmpeg, '-y', '-i', str(src), '-ar', '44100', '-ac', '2', str(dst)])


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--in', dest='infile', required=True, help='Input audio path')
    p.add_argument('--outdir', dest='outdir', default='outputs', help='Output directory')
    p.add_argument('--ffmpeg', dest='ffmpeg', default=None, help='Optional ffmpeg.exe full path')
    args = p.parse_args()

    infile = Path(args.infile)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    ffmpeg = check_ffmpeg(args.ffmpeg)

    # Ensure we have an MP4 input
    if infile.suffix.lower() != '.mp4':
        mp4_path = outdir / (infile.stem + '.mp4')
        print(f'Input is not MP4, converting {infile} -> {mp4_path}')
        to_mp4(ffmpeg, infile, mp4_path)
    else:
        mp4_path = infile

    mp3_path = outdir / (mp4_path.stem + '.mp3')
    wav_path = outdir / (mp4_path.stem + '.from_mp3.wav')

    print(f'Converting MP4 -> MP3: {mp4_path} -> {mp3_path}')
    mp4_to_mp3(ffmpeg, mp4_path, mp3_path)

    print(f'Converting MP3 -> WAV: {mp3_path} -> {wav_path}')
    mp3_to_wav(ffmpeg, mp3_path, wav_path)

    print('Done. Outputs:')
    print(' MP4:', mp4_path)
    print(' MP3:', mp3_path)
    print(' WAV:', wav_path)


if __name__ == '__main__':
    main()
