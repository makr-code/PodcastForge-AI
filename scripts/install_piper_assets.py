#!/usr/bin/env python3
"""
Download Piper voice assets (single voice or all) from the public voices.json / Hugging Face repo.

Usage examples:
  # download one voice into models/piper/<voice_key>/
  python scripts/install_piper_assets.py --voices de_DE-thorsten-high --out-dir models/piper

  # download all voices (huge) into voices/ (ask for confirmation first)
  python scripts/install_piper_assets.py --voices all --out-dir voices

The script will fetch `voices.json` from the DrewThomasson repo and download files
from the rhasspy/piper-voices Hugging Face repo `resolve/main` path.
Supports env var `HF_TOKEN` if you need authenticated downloads.
"""
import argparse
import json
import os
import sys
from urllib.parse import urljoin

try:
    import requests
    from tqdm import tqdm
except Exception:
    print("Missing dependencies: please run 'python -m pip install requests tqdm' and retry.")
    raise

VOICES_JSON_RAW = "https://raw.githubusercontent.com/DrewThomasson/ebook2audiobookpiper-tts/main/voices.json"
BASE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/"


def fetch_voices_json(local_copy=None):
    if local_copy and os.path.exists(local_copy):
        with open(local_copy, 'r', encoding='utf-8') as f:
            return json.load(f)
    print(f"Fetching voices.json from {VOICES_JSON_RAW}")
    r = requests.get(VOICES_JSON_RAW, timeout=30)
    r.raise_for_status()
    return r.json()


def download_file(url, out_path, hf_token=None, chunk_size=1024 * 32):
    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        print(f"Skipping existing: {out_path}")
        return True
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    headers = {}
    if hf_token:
        headers['Authorization'] = f"Bearer {hf_token}"
    with requests.get(url, headers=headers, stream=True, timeout=60) as r:
        if r.status_code != 200:
            print(f"Failed to download {url} -> status {r.status_code}")
            return False
        total = int(r.headers.get('content-length') or 0)
        with open(out_path + '.part', 'wb') as f, tqdm(total=total, unit='B', unit_scale=True, desc=os.path.basename(out_path)) as pbar:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if not chunk:
                    continue
                f.write(chunk)
                pbar.update(len(chunk))
    os.replace(out_path + '.part', out_path)
    return True


def download_voice(voice_key, voice_info, out_dir, hf_token=None, preserve_paths=False):
    files = voice_info.get('files', {})
    if not files:
        print(f"No files listed for {voice_key}")
        return
    print(f"Downloading {len(files)} files for {voice_key} into {out_dir}")
    for file_path, file_info in files.items():
        url = urljoin(BASE_URL, file_path)
        if preserve_paths:
            target_path = os.path.join(out_dir, file_path.replace('/', os.sep))
        else:
            # place everything under out_dir/<voice_key>/<basename>
            target_path = os.path.join(out_dir, voice_key, os.path.basename(file_path))
        ok = download_file(url, target_path, hf_token=hf_token)
        if not ok:
            print(f"WARN: failed to download {url}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--voices', required=True, help="Comma separated voice keys, or 'all'")
    ap.add_argument('--out-dir', default=None, help="Output dir. Default: 'models/piper' for single voices, 'voices' for all")
    ap.add_argument('--voices-json', default=None, help="Optional local voices.json to use")
    ap.add_argument('--preserve-paths', action='store_true', help='Preserve original file paths under out-dir (useful for full mirror)')
    ap.add_argument('--no-confirm', action='store_true', help='Do not ask confirmation for large downloads')
    args = ap.parse_args()

    hf_token = os.environ.get('HF_TOKEN')
    voices_data = fetch_voices_json(args.voices_json)

    voices_requested = [v.strip() for v in args.voices.split(',') if v.strip()]
    is_all = len(voices_requested) == 1 and voices_requested[0].lower() == 'all'

    if is_all:
        default_out = 'voices'
    else:
        default_out = os.path.join('models', 'piper')

    out_dir = args.out_dir or default_out

    if is_all:
        # calculate rough size (sum of size_bytes when available)
        total = 0
        for vk, vi in voices_data.items():
            for fp, finfo in vi.get('files', {}).items():
                total += int(finfo.get('size_bytes') or 0)
        if total > 0:
            mb = total / (1024 * 1024)
            print(f"Total download size (approx): {mb:.1f} MB")
        if not args.no_confirm:
            ans = input(f"Download ALL voices into '{out_dir}'? This can be very large. Continue? [y/N] ")
            if ans.lower() != 'y':
                print('Aborted by user')
                sys.exit(1)

        for vk, vi in voices_data.items():
            download_voice(vk, vi, out_dir, hf_token=hf_token, preserve_paths=args.preserve_paths)
    else:
        for vk in voices_requested:
            vi = voices_data.get(vk)
            if vi is None:
                print(f"Voice key '{vk}' not found in voices.json")
                continue
            download_voice(vk, vi, out_dir, hf_token=hf_token, preserve_paths=args.preserve_paths)

    print('Done')


if __name__ == '__main__':
    main()
