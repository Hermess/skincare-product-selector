# Image Audit

Audit date: 2026-05-25

## Approved Images

| Image | Purpose | Review result |
| --- | --- | --- |
| `assets/evidence-pipeline.svg` | Explains the evidence-backed recommendation workflow | Approved |
| `assets/source-ladder.svg` | Explains source priority and rejected source types | Approved |
| `assets/ingredient-position.svg` | Explains ingredient position and trace-ingredient caveats | Approved |

## Review Checklist

- Rendered locally with `sips` into transient `assets/audit/sips/*.png` files; those generated PNGs were reviewed and then removed from the clean package.
- No text overflow in the approved `sips` renders.
- No cropped content in the approved `sips` renders.
- No external images, trademarks, brand logos, or copyrighted product photos.
- Uses plain diagram shapes and self-authored text only.
- Chinese text is readable on a light background.

## Notes

Quick Look thumbnails may crop wide SVGs because they are generated as square thumbnails. The approved visual check was based on `sips` renders, which preserved the full SVG canvas. The repository keeps the SVG source files and this audit note, not the generated audit thumbnails.
