#!/usr/bin/env python3
"""Build optimized web images + manifest for the Lathika Arts portfolio site.

Reads the original photo folders at the repo root (Backgrounds/, Panels/,
Vases/, Profile Pictures/), curates them (skips duplicate shots and detail
crops), and writes:

  assets/works/<category>/<slug>.jpg         (max 1600px, quality 82)
  assets/works/<category>/thumbs/<slug>.jpg  (max 640px,  quality 78)
  assets/site/*.jpg                          (hero / portrait images)
  js/works-data.js                           (gallery + shop manifest)

Titles and shop entries live in CURATED_TITLES / SHOP_ITEMS below — edit
those and re-run:  python3 tools/build_images.py
"""
import os
import re
import json
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CATEGORIES = {
    "panels": {
        "label": "Wall Panels",
        "src": os.path.join(ROOT, "Panels"),
        "blurb": "Framed floral reliefs, each petal and leaf sculpted by hand.",
    },
    "vases": {
        "label": "Vases & Vessels",
        "src": os.path.join(ROOT, "Vases"),
        "blurb": "Vases, bowls and lamps adorned with sculpted clay blooms.",
    },
    "florals": {
        "label": "Clay Florals & Sculpture",
        "src": os.path.join(ROOT, "Backgrounds", "Backgrounds"),
        "blurb": "Free-standing bouquets, blossoms and figurative sculpture.",
    },
}

# Files to exclude: duplicate shots of the same piece, detail crops of a
# piece already shown, and non-artwork graphics.
EXCLUDE = {
    # --- Panels ---
    "20170917_174128615_iOS.jpg",   # dup of 174123660
    "20170917_174219291_iOS.jpg",   # dup of 174213157
    "20181230_234757598_iOS.jpg",   # dup of 234745211
    "20191123_064218000_iOS.jpg",   # dup of 064217000
    "20220618_143153316_iOS (1).jpg",
    "20230407_013712000_iOS (1).jpg",
    "20230407_013844000_iOS (1).jpg",
    "20230427_231124413_iOS (1).jpg",
    "India0057-1.jpg",              # dup of India0057
    "Panels+(1)-Detail.JPG",
    "Panels+(5)-Detail.JPG",
    "DSCF1118-Zoom.jpg",
    # --- Vases ---
    "20201017_024909851_iOS (1).jpg",
    "20210418_080247977_iOS (1).jpg",
    "20210418_080303623_iOS (1).jpg",
    "20210418_081052173_iOS (1).jpg",
    "20210418_081109187_iOS (1).jpg",
    "20231210_124916000_iOS (1).jpg",
    "20231210_164917465_iOS (1).jpg",
    "20210418_053604000_iOS+1.jpg",
    "20210418_080720000_iOS+2.jpg",
    "20210705_033314000_iOS+1.jpg",
    "20201220_000157000_iOS.jpg",   # dup of 000148000
    "20210418_081052173_iOS.jpg",   # extra angle of the yellow-rose vase
    "20210418_081109187_iOS.jpg",   # extra angle of the yellow-rose vase
    "20210418_080303623_iOS.jpg",   # extra angle of the pink-rose vase
    "20210705_033314000_iOS.jpg",   # cluttered background shot of lamp
    "20210707_130541000_iOS.jpg",   # extra angle of lamp
    "20231207_090218000_iOS.jpg",   # cluttered kitchen shot
    "20231207_112646000_iOS.jpg",   # cluttered kitchen shot
    "20231210_045459000_iOS.jpg",   # extra angle of 045500000
    "IMG_8742+1.jpg",               # cluttered kitchen shot
    "a7d9e713-55f7-403b-959b-26f400124941.JPG",  # dup of the lotus vase
    # --- Backgrounds / florals ---
    "image021 - Copy.jpg",
    "image002.jpg",                 # dup of TreeGirl
    "image007.jpg",                 # marketing graphic, not an artwork photo
    "image008.jpg",                 # extra angle of the bronze figure
    "image020.jpg",                 # near-dup of image021
    "TreeGirl.psd",
    "BookReading Girl.psd",
}

# Hand-written titles for standout pieces (slug -> title).
CURATED_TITLES = {
    # Panels
    "panel1": "Rose in Bloom I",
    "panel3": "Rose in Bloom II",
    "panel5": "Rose in Bloom III",
    "panel6": "Twin Roses",
    "dscf1118": "Crimson Garden",
    "india0055": "Autumn Leaves I",
    "india0057": "Autumn Leaves II",
    "20230309-232629000-ios": "Climbing Roses",
    "20181230-234745211-ios": "Blush Bouquet",
    "20191128-210019482-ios": "Roses in Mahogany",
    "20211018-054031000-ios": "Scarlet Medley",
    "untitled-7": "Coral Vine",
    "lilies-copy": "White Lilies",
    "panels-1": "Cornflower Morning",
    "frame-panel": "Yellow Roses, Framed",
    # Vases
    "20190627-042607000-ios": "Lotus Vase",
    "20200412-205831000-ios": "Rose Posy Vase",
    "20210418-080720000-ios": "Antique Rose Urn",
    "20210418-081307000-ios": "Golden Rose Urn",
    "20210418-053604000-ios": "Magnolia Jar",
    "subject": "Rose Lamp",
    "20231207-142313000-ios": "Evening Rose Lamp",
    "clay-pots-033": "Hibiscus Bowl",
    "clay-pots-069": "Pink Daisy Bowl",
    "dscf1078": "White Rose Vessel",
    "dscf1120": "Poppy Splash",
    "dscf1235": "Iris Duet",
    "20210319-055007000-ios": "Marigold Blue Vase",
    # Florals
    "treegirl": "The Tree Girl",
    "image010": "Girl with a Vessel",
    "image003": "Crimson Roses",
    "image004": "Blush Roses",
    "image017": "Amber Arrangement",
    "image019": "Red Rose Frame",
    "image028": "Lily of the Valley Vase",
}

# Shop: pieces currently open to inquiries. slug -> short description.
SHOP_ITEMS = {
    "panel1": "A single sculpted rose in soft pink, mounted on an ivory panel. Ready to hang.",
    "panel6": "A pair of hand-sculpted roses with leaves, on a cream relief panel.",
    "dscf1118": "A dense, dramatic bouquet of red roses and wildflowers in a gilt frame.",
    "india0057": "Falling autumn leaves sculpted in relief on a warm umber ground.",
    "20230309-232629000-ios": "Climbing roses winding up a tall panel — graceful and architectural.",
    "20181230-234745211-ios": "A soft cluster of blush-pink roses in full bloom, framed.",
    "20210418-080720000-ios": "A stoneware-toned urn wrapped in sculpted antique roses.",
    "20210418-081307000-ios": "A tall urn with golden roses and deep green leaves in relief.",
    "20190627-042607000-ios": "A slender dark vase crowned with hand-formed lotus blossoms.",
    "clay-pots-033": "A free-formed bowl ringed with bright hibiscus blooms.",
    "dscf1078": "A sculptural vessel carrying full white roses — quiet and elegant.",
    "subject": "A one-of-a-kind lamp, its base garlanded with cream clay roses.",
    "image003": "A lush cluster of crimson clay roses, arranged for wall or table.",
    "image028": "A tall vase painted and sculpted with lily-of-the-valley sprays.",
}

# Standalone site images: (source path, output name, max px)
SITE_IMAGES = [
    (os.path.join(ROOT, "Profile Pictures", "Profile Pictures",
                  "dd3bda77-166b-4b17-8b64-9b2c47e3907e.JPG"), "portrait.jpg", 1200),
    (os.path.join(ROOT, "Profile Pictures", "Profile Pictures",
                  "IMG_1966.JPG"), "artist-with-panels.jpg", 1600),
    (os.path.join(ROOT, "Panels", "DSCF1118.JPG"), "hero-tall.jpg", 1600),
    (os.path.join(ROOT, "Backgrounds", "Backgrounds", "image003.jpg"), "hero.jpg", 1920),
]

FULL_MAX, FULL_Q = 1600, 82
THUMB_MAX, THUMB_Q = 640, 78


def slugify(name):
    stem = os.path.splitext(name)[0]
    stem = stem.replace("_iOS", "-ios")
    stem = re.sub(r"[^A-Za-z0-9]+", "-", stem).strip("-").lower()
    return stem


def save_resized(im, path, max_px, quality):
    im = ImageOps.exif_transpose(im)
    im = im.convert("RGB")
    im.thumbnail((max_px, max_px), Image.LANCZOS)
    im.save(path, "JPEG", quality=quality, optimize=True, progressive=True)
    return im.size


def pretty_title(slug, cat_label, index):
    if slug in CURATED_TITLES:
        return CURATED_TITLES[slug]
    noun = {"Wall Panels": "Floral Panel",
            "Vases & Vessels": "Sculpted Vessel",
            "Clay Florals & Sculpture": "Clay Floral Study"}[cat_label]
    return f"{noun} No. {index}"


def main():
    works = []
    for cat, info in CATEGORIES.items():
        out_full = os.path.join(ROOT, "assets", "works", cat)
        out_thumb = os.path.join(out_full, "thumbs")
        os.makedirs(out_thumb, exist_ok=True)
        files = sorted(os.listdir(info["src"]))
        n = 0
        for fname in files:
            if fname in EXCLUDE:
                continue
            if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            src = os.path.join(info["src"], fname)
            slug = slugify(fname)
            n += 1
            with Image.open(src) as im:
                w, h = save_resized(im, os.path.join(out_full, slug + ".jpg"),
                                    FULL_MAX, FULL_Q)
            with Image.open(src) as im:
                save_resized(im, os.path.join(out_thumb, slug + ".jpg"),
                             THUMB_MAX, THUMB_Q)
            works.append({
                "slug": slug,
                "category": cat,
                "title": pretty_title(slug, info["label"], n),
                "full": f"assets/works/{cat}/{slug}.jpg",
                "thumb": f"assets/works/{cat}/thumbs/{slug}.jpg",
                "w": w, "h": h,
                "forSale": slug in SHOP_ITEMS,
                "description": SHOP_ITEMS.get(slug, ""),
            })
        print(f"{cat}: {n} works")

    site_dir = os.path.join(ROOT, "assets", "site")
    os.makedirs(site_dir, exist_ok=True)
    for src, name, max_px in SITE_IMAGES:
        with Image.open(src) as im:
            save_resized(im, os.path.join(site_dir, name), max_px, 84)
        print("site:", name)

    manifest = {
        "categories": {k: {"label": v["label"], "blurb": v["blurb"]}
                       for k, v in CATEGORIES.items()},
        "works": works,
    }
    out_js = os.path.join(ROOT, "js", "works-data.js")
    os.makedirs(os.path.dirname(out_js), exist_ok=True)
    with open(out_js, "w") as f:
        f.write("// Generated by tools/build_images.py — edit titles there and re-run.\n")
        f.write("window.WORKS_DATA = ")
        json.dump(manifest, f, indent=1)
        f.write(";\n")
        f.write("var WORKS_DATA = window.WORKS_DATA;\n")
    print(f"manifest: {len(works)} works -> js/works-data.js")


if __name__ == "__main__":
    main()
