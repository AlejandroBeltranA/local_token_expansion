#!/usr/bin/env python3
"""
Download MLX‑formatted models from Hugging Face and place them in mlx_models.

Non‑technical summary:
1) Ask MLX to download each model (if not already cached).
2) Put a link (or copy) into your local mlx_models folder.
3) This keeps your experiments organized and avoids re‑downloading.
"""
import argparse
import os
import shutil
from pathlib import Path

from mlx_lm.utils import _download

DEFAULT_MODELS = [
    "mlx-community/Meta-Llama-3.1-8B-Instruct-3bit",
    "mlx-community/Phi-3-mini-4k-instruct-4bit",
    "mlx-community/SmolLM-1.7B-Instruct-4bit",
    "mlx-community/Phi-4-mini-instruct-8bit",
]


def safe_link(src: Path, dst: Path) -> None:
    if dst.exists():
        print(f"exists, skipping: {dst}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(src, dst, target_is_directory=True)
        print(f"linked: {dst} -> {src}")
    except OSError:
        # Fall back to copy if symlink fails
        shutil.copytree(src, dst)
        print(f"copied: {dst} -> {src}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download MLX models from Hugging Face and place them in mlx_models.")
    parser.add_argument("--dest", default="mlx_models", help="Destination directory for downloaded models")
    parser.add_argument("--copy", action="store_true", help="Copy files instead of symlink")
    parser.add_argument("--models", nargs="*", default=None, help="Override model list")
    args = parser.parse_args()

    dest_root = Path(args.dest).expanduser().resolve()
    dest_root.mkdir(parents=True, exist_ok=True)

    models = args.models if args.models else DEFAULT_MODELS

    for repo in models:
        print(f"downloading: {repo}")
        model_path = _download(repo)
        model_dir = repo.split("/")[-1]
        dest_path = dest_root / model_dir

        if args.copy:
            if dest_path.exists():
                print(f"exists, skipping: {dest_path}")
                continue
            shutil.copytree(model_path, dest_path)
            print(f"copied: {dest_path}")
        else:
            safe_link(model_path, dest_path)


if __name__ == "__main__":
    main()
