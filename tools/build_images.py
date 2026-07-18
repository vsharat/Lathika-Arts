#!/usr/bin/env python3
"""Build optimized web images + manifest for the Lathika Arts portfolio site.

Reads the original photo folders at the repo root and curates them (skips
duplicate shots and detail crops), writing:

  assets/works/<category>/<slug>.jpg         (max 1600px, quality 82)
  assets/works/<category>/thumbs/<slug>.jpg  (max 640px,  quality 78)
  assets/site/*.jpg                          (hero / portrait images)
  js/works-data.js                           (portfolio + shop manifest)

Site structure:
  - "shop" section  (every work can be inquired about): Arrangements,
    Wall Panels, Vases & Vessels
  - "portfolio" section (display only): Sculptures, Paintings, Sketches

Titles and shop descriptions live in CURATED_TITLES / SHOP_DESCRIPTIONS
below — edit those and re-run:  python3 tools/build_images.py
"""
import os
import re
import json
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Category order here is the display order on the site.
CATEGORIES = {
    # ------------------------- shop -------------------------
    "arrangements": {
        "label": "Arrangements",
        "section": "shop",
        "src": os.path.join(ROOT, "Arrangements"),
        "blurb": "Bouquets, trays and table arrangements of hand-sculpted clay blooms.",
    },
    "panels": {
        "label": "Wall Panels",
        "section": "shop",
        "src": os.path.join(ROOT, "Panels"),
        "blurb": "Framed floral reliefs, each petal and leaf sculpted by hand.",
    },
    "vases": {
        "label": "Vases & Vessels",
        "section": "shop",
        "src": os.path.join(ROOT, "Vases"),
        "blurb": "Vases, bowls and lamps adorned with sculpted clay flowers.",
    },
    # ----------------------- portfolio ----------------------
    "sculptures": {
        "label": "Sculptures",
        "section": "portfolio",
        "src": os.path.join(ROOT, "Sculptures"),
        "blurb": "Figurative sculpture in clay and patina finishes.",
    },
    "paintings": {
        "label": "Paintings",
        "section": "portfolio",
        "src": os.path.join(ROOT, "Paintings"),
        "blurb": "Figurative and landscape paintings in vivid color.",
    },
    "sketches": {
        "label": "Sketches",
        "section": "portfolio",
        "src": os.path.join(ROOT, "Sketches"),
        "blurb": "Pencil studies and drawings.",
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
    # --- Arrangements ---
    "20181105_151754927_iOS.jpg",   # dup of 151750758
    "DSCF0739+copy.png",            # dup of DSCF0739.JPG
    "Plasti-ClayBackground.png",    # material/background graphic, not a work
    "ed8ed12e-b08f-400c-87fa-e48b2cf3d47b (1).jpg",
    "ed8ed12e-b08f-400c-87fa-e48b2cf3d47b (2).JPG",
    "image011 (1).jpg",
    "image014 (1).jpg",
    # --- Sculptures ---
    "Aamukta+_+Ahir+April+2012_0140-1.jpg",  # dup full view of 0135
    "DSC00097.JPG",                 # extra angle of the dancer
    "DSC00101.JPG",                 # extra angle of the dancer
    "DSC00102.JPG",                 # extra angle of the dancer
    # --- Paintings ---
    "3063a996-6740-4249-9dfe-279011c13697+1.JPG",
    "55eebeab-dee9-4865-8cda-817367889662+1.JPG",
    "IMG_9750.jpg",                 # dup of IMG_9749
    "26249aa5-bac5-494f-8ae7-6a71e875c6d6.JPG",  # framed dup of 7312c193
    "b435a840-0468-49b3-8a46-5d0a0d3ea73b.JPG",  # dup of fec34c2e
    # --- Sketches ---
    "PHOTO-2020-06-19-22-48-48.jpg",  # dup of sketch2
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
    # Arrangements
    "10": "Star Jasmine Scatter",
    "11": "Rose Harvest",
    "15": "Bouquet in Blue and Gold",
    "16": "Pastel Bouquet",
    "17": "Lavender and Cream",
    "20181105-151750758-ios": "Three Cream Roses",
    "20181216-163332184-ios": "Yellow Roses at Dusk",
    "20190810-024713369-ios": "Garden Medley",
    "20200428-165311000-ios": "Roses in a Round Vase",
    "217074-1501713842894-1835641907-866569-7613951-n": "Red and White Cascade",
    "7": "Crimson Buds",
    "dscf0738": "Pink Roses, Scattered",
    "dscf0739": "A Tray of Roses",
    "dscf0742": "A Tray of Roses II",
    "dscf1230-copy": "Pink Lily Buds",
    "mummys-art-work-18": "Two Roses",
    "november-2016-061": "Winter Roses",
    "ed8ed12e-b08f-400c-87fa-e48b2cf3d47b": "Daffodil Burst",
    "image011": "Mixed Rose Basket",
    "image014": "Golden Sunflowers",
    # Sculptures
    "015": "Girl on a Branch",
    "20201116-021654000-ios": "Jade Muse",
    "20210418-080720000-ios-1": "Mother and Child",
    "aamukta-ahir-april-2012-0135-small": "Maiden with Staff",
    "aamukta-ahir-april-2012-0136-1": "Maiden with Staff (Detail)",
    "dsc00095-small": "The Dancer",
    "dsc00100": "Dancer at Rest",
    "dscf1124": "Golden Repose",
    # Paintings
    "00a73e87-3b8a-42ae-bbe3-de29da7b8a25": "Twilight Reverie",
    "1419150d-fedd-44c2-91c7-96aec99c7a11": "River Blue",
    "20240329-202816000-ios": "Under the Canopy",
    "20240424-154632000-ios": "The Orchard Swing",
    "20240424-155338000-ios": "Moonlight in Red",
    "20240609-021143000-ios": "The Golden Sari",
    "3063a996-6740-4249-9dfe-279011c13697": "Moonlit Cascade",
    "55eebeab-dee9-4865-8cda-817367889662": "The Dancer in Yellow",
    "585fc2ce-fd1b-451e-aa8d-5b50605dad0f": "Portrait Study",
    "63335336-ccb9-4069-a9f7-1a016433ff07": "The Dove",
    "7312c193-b531-4c6b-a437-979e30265409": "Radiant in Orange",
    "826a5e50-8903-498c-afa7-6f8e51c9b155": "The Falls",
    "92283762-1f9a-47e4-9ee3-84b7527b7b4d": "Rest Beneath the Tree",
    "951976a0-8663-48e8-96f8-46a72129fb5e": "Moonrise Bather",
    "img-4098": "The Dancer, Framed",
    "img-5375": "Monsoon Grove",
    "img-7532": "Autumn Pond",
    "img-9584": "The Corner Table",
    "img-9585": "The Window Seat",
    "img-9748": "Evening in Blue",
    "img-9749": "Crimson Evening",
    "aa008e26-81a1-49ab-860c-ac9fd2a0fac1": "Lady by the Lake",
    "c943d45c-5183-4595-8364-332214c6273d": "Sisters at the Tree",
    "f5e0931f-687d-49a2-b1d0-ae6fd6976f20": "The Musicians",
    "fec34c2e-6dda-4e69-9955-bb7bd6fb6c6f": "Midnight Repose",
    # Sketches
    "mummys-art-work-16": "Mahatma",
    "skanu": "A Sideways Glance",
}

# Optional shop blurbs (slug -> description). Every work in a "shop"
# category is inquirable; pieces without an entry get a generic line.
SHOP_DESCRIPTIONS = {
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
    "ed8ed12e-b08f-400c-87fa-e48b2cf3d47b": "A burst of golden daffodils, every trumpet and petal shaped by hand.",
    "dscf0739": "A generous tray of pastel roses — dozens of blooms, no two alike.",
    "november-2016-061": "Deep red winter roses gathered into a lush centerpiece.",
    "20200428-165311000-ios": "Red and yellow roses in a round vase — a classic, joyful bouquet.",
    "image011": "A mixed basket of roses in pinks, creams and golds.",
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

TITLE_NOUNS = {
    "arrangements": "Floral Arrangement",
    "panels": "Floral Panel",
    "vases": "Sculpted Vessel",
    "sculptures": "Sculpture",
    "paintings": "Painting",
    "sketches": "Pencil Study",
}


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


def pretty_title(slug, cat, index):
    if slug in CURATED_TITLES:
        return CURATED_TITLES[slug]
    return f"{TITLE_NOUNS[cat]} No. {index}"


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
                "title": pretty_title(slug, cat, n),
                "full": f"assets/works/{cat}/{slug}.jpg",
                "thumb": f"assets/works/{cat}/thumbs/{slug}.jpg",
                "w": w, "h": h,
                "forSale": info["section"] == "shop",
                "description": SHOP_DESCRIPTIONS.get(slug, ""),
            })
        print(f"{cat}: {n} works")

    site_dir = os.path.join(ROOT, "assets", "site")
    os.makedirs(site_dir, exist_ok=True)
    for src, name, max_px in SITE_IMAGES:
        with Image.open(src) as im:
            save_resized(im, os.path.join(site_dir, name), max_px, 84)
        print("site:", name)

    manifest = {
        "categories": {k: {"label": v["label"], "blurb": v["blurb"],
                           "section": v["section"]}
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
