#!/usr/bin/env python3
"""
Download Hugging Face model repos into the project's `models/` folder so TTS can run offline.

Usage:
    python scripts/download_models.py --model <repo_id> [--model <repo_id> ...] [--dest ./models] [--token <HUGGINGFACE_TOKEN>]

Examples:
    python scripts/download_models.py --model tts_models/multilingual/multi-dataset/xtts_v2
    python scripts/download_models.py --model suno/bark --dest ./models

This script uses `huggingface_hub.snapshot_download` and places each repo under `dest/<repo_name>`.
"""
from __future__ import annotations
import argparse
import logging
from pathlib import Path
from huggingface_hub import snapshot_download

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("download_models")


def repo_folder_name(repo_id: str) -> str:
    # normalize repo id to filesystem-friendly folder name
    return repo_id.replace("/", "_")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", "-m", action="append", required=True, help="Hugging Face repo id (e.g. 'tts_models/...')")
    p.add_argument("--dest", "-d", default="models", help="Destination folder (default: ./models)")
    p.add_argument("--token", "-t", default=None, help="HuggingFace access token (if required)")
    args = p.parse_args()

    dest = Path(args.dest).resolve()
    dest.mkdir(parents=True, exist_ok=True)

    for repo in args.model:
        folder = dest / repo_folder_name(repo)
        logger.info(f"Downloading {repo} -> {folder}")
        # Basic validation: HF repo ids are usually 'namespace/repo_name'
        if repo.count("/") != 1:
            logger.warning(
                f"Repo id '{repo}' does not look like a standard HF repo id (namespace/repo). "
                "If you passed a library model string (e.g. 'tts_models/...') this may not map to a HF repo."
            )

        # Try snapshot_download with the common kw names for token for compatibility
        try:
            out = snapshot_download(repo_id=repo, cache_dir=str(dest), repo_type="model", use_auth_token=args.token)
            logger.info(f"Downloaded to {out}")
        except TypeError as te:
            # Some versions of huggingface_hub expect 'token' instead of 'use_auth_token'
            try:
                out = snapshot_download(repo_id=repo, cache_dir=str(dest), repo_type="model", token=args.token)
                logger.info(f"Downloaded to {out}")
            except Exception as e:
                logger.error(f"Failed to download {repo}: {e}")
        except Exception as e:
            logger.error(f"Failed to download {repo}: {e}")


if __name__ == "__main__":
    main()
