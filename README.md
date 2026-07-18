# Lathika Arts — Portfolio Website

A modern, mobile-first portfolio site for Lathika's hand-sculpted clay art:
floral wall panels, sculpted vases & vessels, and free-standing clay florals.

This is a **pure portfolio site — no e-commerce**. The Shop page shows
available pieces without prices; visitors press **Inquire** and their message
is emailed to the address configured below.

## Pages

| Page | Purpose |
|---|---|
| `index.html` | Landing page — hero, collections, featured works, artist intro |
| `gallery.html` | Full portfolio with category filters and a lightbox viewer |
| `shop.html` | Available pieces with the email-inquiry flow (no prices, no checkout) |
| `about.html` | Artist bio and photos |
| `contact.html` | General contact / commission form |

No build step or framework — plain HTML/CSS/JS. Works on GitHub Pages
(Settings → Pages → deploy from branch, root folder) or any static host.

## Changing the inquiry email

Edit **one line** in [`js/config.js`](js/config.js):

```js
inquiryEmail: "ahir.valluri@gmail.com",
```

Forms are delivered by [formsubmit.co](https://formsubmit.co) (free, no
account needed). **The very first message sent to a new address triggers a
one-time activation email to that inbox — click the link in it once**, and
every later inquiry arrives normally. If sending ever fails, the form shows
the visitor a direct `mailto:` link as a fallback, so no inquiry is lost.

## Editing artworks, titles and shop items

Artwork data lives in `js/works-data.js`, which is **generated** by
[`tools/build_images.py`](tools/build_images.py) from the original photo
folders (`Panels/`, `Vases/`, `Backgrounds/`). To make changes, edit the
dictionaries at the top of that script and re-run it:

- `CURATED_TITLES` — give a piece a proper title (otherwise it gets a
  numbered one like "Floral Panel No. 12")
- `SHOP_ITEMS` — which pieces appear in the Shop, with their descriptions
- `EXCLUDE` — photos to leave out (duplicate shots, etc.)

```bash
pip install Pillow
python3 tools/build_images.py
```

The script re-creates the optimized web images in `assets/works/` (1600px
full size + 640px thumbnails, EXIF-corrected, metadata stripped) and
rewrites the manifest. Add new photos to the original folders and re-run to
include them.

## Bio and text content

The About-page bio and homepage copy are placeholder text written for the
redesign — edit `about.html` / `index.html` directly to personalize them.

## Local preview

```bash
python3 -m http.server 8000
# open http://localhost:8000
```
