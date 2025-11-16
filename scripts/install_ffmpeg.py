#!/usr/bin/env python3
"""Install FFmpeg into the repository under `third_party/ffmpeg/bin`.

Usage:
  python scripts/install_ffmpeg.py [--url URL] [--dest DEST_DIR]

The script downloads a platform-appropriate static build (Windows/Linux/macOS),
extracts it and places the `ffmpeg` (or `ffmpeg.exe`) binary into
`third_party/ffmpeg/bin` inside the repository.

You can override the download URL with `--url` if you prefer a specific build.
"""
from __future__ import annotations

import argparse
import os
import shutil
import stat
import sys
import tempfile
import urllib.request
import zipfile
import tarfile


def default_url_for_platform() -> str | None:
    plat = sys.platform
    if plat.startswith("win"):
        # Gyan.dev essentials build (stable, 64-bit)
        return "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    if plat.startswith("linux"):
        # John Van Sickle static build for x86_64
        return "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
    if plat.startswith("darwin"):
        # Evermeet builds provide macOS binaries via a simple url (may redirect)
        return "https://evermeet.cx/ffmpeg/getrelease/ffmpeg/zip"
    return None


def download(url: str, dst_path: str) -> None:
    print(f"Downloading: {url}")
    with urllib.request.urlopen(url) as resp, open(dst_path, "wb") as out:
        shutil.copyfileobj(resp, out)


def extract_archive(archive_path: str, extract_to: str) -> None:
    if zipfile.is_zipfile(archive_path):
        with zipfile.ZipFile(archive_path, "r") as z:
            z.extractall(extract_to)
        return
    if tarfile.is_tarfile(archive_path):
        with tarfile.open(archive_path, "r:*") as t:
            t.extractall(extract_to)
        return
    raise RuntimeError("Unknown archive format for: %s" % archive_path)


def find_ffmpeg(extracted_root: str) -> str | None:
    for root, _dirs, files in os.walk(extracted_root):
        for f in files:
            if f.lower() in ("ffmpeg", "ffmpeg.exe"):
                return os.path.join(root, f)
    return None


def make_executable(path: str) -> None:
    try:
        st = os.stat(path)
        os.chmod(path, st.st_mode | stat.S_IEXEC)
    except Exception:
        pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", help="Override download URL for ffmpeg (optional)")
    parser.add_argument("--dest", help="Destination directory (defaults to third_party/ffmpeg)")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary download/extract dir for debugging")
    args = parser.parse_args()

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    dest_dir = args.dest or os.path.join(repo_root, "third_party", "ffmpeg")
    bin_dir = os.path.join(dest_dir, "bin")
    os.makedirs(bin_dir, exist_ok=True)

    # build list of candidate URLs (user-specified first, then platform defaults and common mirrors)
    candidates: list[str] = []
    if args.url:
        candidates.append(args.url)

    default = default_url_for_platform()
    if default:
        candidates.append(default)

    # common alternate mirrors (only add those that make sense for platform)
    plat = sys.platform
    if plat.startswith("win"):
        candidates.extend([
            "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
            "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.zip",
        ])
    if plat.startswith("linux"):
        candidates.extend([
            "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz",
            "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-64bit-static.tar.xz",
        ])
    if plat.startswith("darwin"):
        candidates.extend([
            "https://evermeet.cx/ffmpeg/getrelease/ffmpeg/zip",
        ])

    # remove duplicates while preserving order
    seen = set()
    urls: list[str] = []
    for u in candidates:
        if u and u not in seen:
            urls.append(u)
            seen.add(u)

    if not urls:
        print("No candidate ffmpeg URLs available for this platform. Provide --url.")
        return 2

    tmpdir = tempfile.mkdtemp(prefix="pf_ffmpeg_")
    last_err: Exception | None = None
    try:
        archive_path = os.path.join(tmpdir, "ffmpeg_download")
        extract_dir = os.path.join(tmpdir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)

        found = None
        for u in urls:
            try:
                print(f"Attempting download from: {u}")
                download(u, archive_path)
                try:
                    extract_archive(archive_path, extract_dir)
                except Exception as ex:
                    print(f"Failed to extract archive from {u}: {ex}")
                    last_err = ex
                    # clean extract dir and try next URL
                    shutil.rmtree(extract_dir, ignore_errors=True)
                    os.makedirs(extract_dir, exist_ok=True)
                    continue

                found = find_ffmpeg(extract_dir)
                if found:
                    print(f"Found ffmpeg binary in archive from: {u}")
                    break
                else:
                    print(f"No ffmpeg binary found inside archive from: {u}")
                    last_err = RuntimeError("ffmpeg binary not found in archive")
                    shutil.rmtree(extract_dir, ignore_errors=True)
                    os.makedirs(extract_dir, exist_ok=True)
                    continue
            except Exception as e:
                print(f"Download or extraction failed for {u}: {e}")
                last_err = e
                # try next URL
                continue

        if not found:
            print("Could not download and extract a valid ffmpeg binary from any candidate URL.")
            if last_err:
                print("Last error:", last_err)
            print("Temporary files are at:", tmpdir)
            return 3

        dest_ffmpeg = os.path.join(bin_dir, os.path.basename(found))
        print(f"Installing ffmpeg binary to: {dest_ffmpeg}")
        shutil.copy(found, dest_ffmpeg)
        make_executable(dest_ffmpeg)

        print("\nFFmpeg installed successfully.")
        if sys.platform.startswith("win"):
            print(f"Add to PATH for current PowerShell session:\n  $env:PATH = \"$env:PATH;{os.path.abspath(bin_dir)}\"")
            print(f"Or add {os.path.abspath(bin_dir)} to your system PATH via Settings -> Environment Variables.")
        else:
            print(f"Add to PATH for current shell:\n  export PATH=\"$PATH:{os.path.abspath(bin_dir)}\"")

        print("You can verify by running:\n  ffmpeg -version")

        if args.keep_temp:
            print(f"Temporary files kept at: {tmpdir}")
        else:
            shutil.rmtree(tmpdir, ignore_errors=True)

        return 0
    finally:
        # If keep_temp was not requested, ensure tmpdir was removed above; otherwise leave it
        if args.keep_temp:
            print(f"Temporary files available at: {tmpdir}")


if __name__ == "__main__":
    raise SystemExit(main())
