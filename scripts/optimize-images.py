#!/usr/bin/env python3
"""
scripts/optimize-images.py
Automated responsive image optimization pipeline for De Witte Raaf Dierenartsen.
Generates multi-format (AVIF, WebP, original) and multi-width assets for LCP/FCP optimization.
"""

import os
import sys
import json
import hashlib
import subprocess
import shutil
from pathlib import Path
from PIL import Image

SOURCE_DIR = Path("assets/images/source")
OUTPUT_DIR = Path("assets/images/generated")
TARGET_WIDTHS = [400, 800, 1200, 1600]
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

def get_file_hash(filepath):
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def ensure_dir(path):
    path.mkdir(parents=True, exist_ok=True)

def has_magick():
    return shutil.which("magick") is not None

def optimize_single_image(src_path, output_dir, use_magick=True):
    stem = src_path.stem
    ext = src_path.suffix.lower()
    
    try:
        with Image.open(src_path) as im:
            orig_w, orig_h = im.size
            aspect_ratio = orig_w / orig_h
    except Exception as e:
        print(f"[WARN] Cannot open {src_path}: {e}")
        return None

    widths = [w for w in TARGET_WIDTHS if w <= orig_w]
    if not widths:
        widths = [orig_w]
    if orig_w not in widths and orig_w < 2000:
        widths.append(orig_w)
    widths = sorted(list(set(widths)))

    results = {
        "original": str(src_path),
        "width": orig_w,
        "height": orig_h,
        "aspect_ratio": round(aspect_ratio, 4),
        "variants": {}
    }

    for w in widths:
        h = int(w / aspect_ratio)
        variant_stem = f"{stem}-{w}"
        
        # 1. Fallback (JPG/PNG)
        fallback_ext = ".jpg" if ext in [".jpg", ".jpeg"] else ".png"
        fallback_out = output_dir / f"{variant_stem}{fallback_ext}"
        if not fallback_out.exists():
            with Image.open(src_path) as im:
                im_rgb = im.convert("RGB") if fallback_ext == ".jpg" and im.mode in ("RGBA", "P") else im
                resized = im_rgb.resize((w, h), Image.Resampling.LANCZOS)
                if fallback_ext == ".jpg":
                    resized.save(fallback_out, "JPEG", quality=82, optimize=True)
                else:
                    resized.save(fallback_out, "PNG", optimize=True)

        # 2. WebP
        webp_out = output_dir / f"{variant_stem}.webp"
        if not webp_out.exists():
            with Image.open(src_path) as im:
                resized = im.resize((w, h), Image.Resampling.LANCZOS)
                resized.save(webp_out, "WEBP", quality=80, method=6)

        # 3. AVIF (if magick available)
        avif_out = output_dir / f"{variant_stem}.avif"
        if use_magick and not avif_out.exists():
            try:
                subprocess.run(
                    ["magick", str(fallback_out), "-quality", "75", str(avif_out)],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except Exception:
                pass

        results["variants"][w] = {
            "fallback": str(fallback_out.relative_to(".")),
            "webp": str(webp_out.relative_to(".")),
            "avif": str(avif_out.relative_to(".")) if avif_out.exists() else None,
            "width": w,
            "height": h
        }

    # Also make a standard un-suffixed webp fallback in output_dir
    default_webp = output_dir / f"{stem}.webp"
    if not default_webp.exists() and (stem + f"-{widths[-1]}.webp") in [v["webp"].split("/")[-1] for v in results["variants"].values()]:
        shutil.copyfile(output_dir / f"{stem}-{widths[-1]}.webp", default_webp)

    return results

def main():
    if not SOURCE_DIR.exists():
        print(f"Source directory {SOURCE_DIR} does not exist.")
        return

    ensure_dir(OUTPUT_DIR)
    manifest_path = OUTPUT_DIR / "manifest.json"
    cache_path = OUTPUT_DIR / ".cache.json"

    cache = {}
    if cache_path.exists():
        try:
            with open(cache_path, "r") as f:
                cache = json.load(f)
        except Exception:
            cache = {}

    manifest = {}
    use_mag = has_magick()
    print(f"Starting image optimization (ImageMagick: {use_mag})...")

    updated_count = 0
    for file in sorted(SOURCE_DIR.iterdir()):
        if file.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        file_hash = get_file_hash(file)
        if file.name in cache and cache[file.name].get("hash") == file_hash and (OUTPUT_DIR / f"{file.stem}.webp").exists():
            manifest[file.stem] = cache[file.name]["data"]
            continue

        print(f"Processing {file.name} ({file.stat().st_size // 1024} KB)...")
        res = optimize_single_image(file, OUTPUT_DIR, use_magick=use_mag)
        if res:
            manifest[file.stem] = res
            cache[file.name] = {"hash": file_hash, "data": res}
            updated_count += 1

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2)

    print(f"Optimization complete! {updated_count} images updated. Manifest saved to {manifest_path}")

if __name__ == "__main__":
    main()
