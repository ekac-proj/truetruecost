# TrueTrueCost

Static directory: *What you'll actually pay after the promo ends* — estimated 6-month true cost of
self-storage by city (promo rate vs. post-increase rate + fees). Plain HTML/CSS/JS, no build step.

## Layout
```
index.html            home: problem, method, US state map, city tiles grouped by state (auto-generated between CITY_LIST markers), disclaimer
about.html            about / affiliate disclosure
how-it-works.html     methodology (linked from nav + footer)
size-guide.html       5x5–10x20 size guide and a browser-only "what do you need?" quiz
cities/_template.html city page template ({{PLACEHOLDERS}})
cities/<slug>.html    generated city pages (austin-tx, dallas-tx)
assets/style.css      styles;  assets/calc.js  6-month true-cost calculator
assets/size-quiz.js   size quiz used by size-guide.html (no network, no storage)
data/site.json        site URL + cost-model assumptions (promo 50%, +30% increase from month 5, $29 fee, $12/mo protection)
data/cities.json      index of all cities (nightly routine appends here via the script)
data/cities/<slug>.json  per-city market data + sources used to build the page
scripts/add_city.py   scaffold/publish helper
robots.txt, sitemap.xml
```

## Preview
```
cd /workspace/storage-true-cost && python3 -m http.server 8080
# open http://localhost:8080/
```
(Opening index.html directly via file:// also works — nothing is fetched at runtime.)

## Add a city
1. Scaffold a draft (noindex, TBD rows, not in sitemap/home list):
   `python3 scripts/add_city.py houston-tx "Houston, TX"`
2. Research 2–3 public price pages (SpareFoot, StorageCafe, Extra Space city blog, etc.) and create
   `data/cities/houston-tx.json` — copy `data/cities/austin-tx.json`. Per unit: `market` = list of average
   monthly rates from each source, `low` = lowest listed promo, `notes`. Add every source to `sources`.
3. Publish: `python3 scripts/add_city.py houston-tx "Houston, TX" --config data/cities/houston-tx.json --force`
   This computes the table, writes the page, upserts `data/cities.json`, regenerates `sitemap.xml`
   and the home page city list.
4. `python3 scripts/add_city.py --rebuild` regenerates sitemap, robots, the homepage state groups (inside the CITY_LIST markers) and shared footers. The US map markup in index.html stays put; assets/map.js highlights a state and jumps to its group, and reports an empty state by clearing the filter.
5. `python3 scripts/add_city.py --all` re-publishes every city from its JSON (use after template/CSS/model changes).

City pages link “Not sure what size?” to `size-guide.html?city=<slug>&name=<City, ST>#quiz`. The sentence is in `cities/_template.html` (`{{CITY_NAME_Q}}` is the URL-encoded metro name). Existing pages were updated in place. `--all` rewrites every city page from JSON, so use it when the template or the cost model changes, not merely to refresh that link.

Slugs: lowercase, hyphenated, `city-st`. To change the cost model, edit `data/site.json` and re-run
`python3 scripts/add_city.py --all` — calculator defaults (fee, protection, increase %, increase month, promo %, months) are filled from
`data/site.json` automatically; the rate field is prefilled with each city's 10x10 market rate.

## Renter quotes
The "Renters say" strip under the key figures pulls 2 quotes per city (deterministic by slug) from `renter_quotes` in
`data/site.json`. Keep them short, paraphrased and anonymized; edit the pool and run `--all`.

## Partner links
CTA buttons are placeholders: `href="#" rel="nofollow sponsored" data-partner="sparefoot|neighbor|storageunits"`.
When affiliate deals exist, replace `#` in `cities/_template.html` (or add a small JS map from
`data-partner` to the tracking URL) and rebuild pages.

## Deploy (not done yet — needs instructions)
- Static files only. Netlify: drag-and-drop the folder or `netlify deploy --dir . --prod`.
  Also works on Cloudflare Pages / GitHub Pages.
- Before deploy: set the real domain in `data/site.json` (`site_url`), `robots.txt` and the canonical
  tags in `index.html`/`about.html`, then `--rebuild` and re-run each city with `--force`.
- Exclude `scripts/` and `data/cities/` from the publish dir if you prefer (harmless if public).
