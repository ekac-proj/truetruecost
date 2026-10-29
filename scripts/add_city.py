#!/usr/bin/env python3
"""Scaffold / (re)build a TrueTrueCost city page.

Usage:
  python3 scripts/add_city.py <slug> "<Metro name, ST>" [--config data/cities/<slug>.json] [--force]
  python3 scripts/add_city.py --rebuild          # regenerate sitemap.xml (incl. privacy & terms), home city groups, shared footers
  python3 scripts/add_city.py --all              # re-publish every city that has data/cities/<slug>.json

Without --config the page is created as a DRAFT (noindex, placeholder rows, not in
sitemap or home list). With --config (see data/cities/austin-tx.json for the format)
the table is computed from the market rates and the page is published.
Every run updates data/cities.json, sitemap.xml and the city list in index.html.
"""
import argparse, datetime, html, json, re, statistics, sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "cities" / "_template.html"
INDEX_JSON = ROOT / "data" / "cities.json"
SITE = json.loads((ROOT / "data" / "site.json").read_text())
M = SITE["model"]
TODAY = datetime.date.today().isoformat()
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "DC": "District of Columbia",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
    "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
    "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon",
    "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
    "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia",
    "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}


def money(x):
    return f"${round(x):,}"


def true_cost(rate, inc):
    """6-month total and monthly avg for a given post-promo rate and increase."""
    n, k = M["months"], M["increase_from_month"]
    rent = rate * M["promo_month1_fraction"]
    for month in range(2, n + 1):
        rent += rate * (1 + inc) if month >= k else rate
    total = rent + M["admin_fee"] + M["protection_per_month"] * n
    return total / n, rent / n


def unit_row(u):
    rate = statistics.mean(u["market"])
    avg_mid, rent_mid = true_cost(rate, M["increase_mid"])
    avg_lo, _ = true_cost(rate, M["increase_low"])
    avg_hi, _ = true_cost(rate, M["increase_high"])
    after_mid = rate * (1 + M["increase_mid"])
    srcs = len(u["market"])
    basis = "single source — estimate" if srcs == 1 else f"avg of {srcs} sources"
    low = (f"promos from {money(u['low'])}" if u.get("low") is not None else "lowest promo: no public figure")
    true = (f"<span class=\"big\">~{money(avg_mid)}/mo</span>"
            f"<span class=\"small\">range {money(avg_lo)}–{money(avg_hi)}<br>rent only {money(rent_mid)}</span>")
    promo = (f"<span class=\"big\">{money(rate)}</span>"
             f"<span class=\"small\">{basis}<br>{low}</span>")
    after = (f"<span class=\"big\">~{money(after_mid)}</span>"
             f"<span class=\"small\">range {money(rate * (1 + M['increase_low']))}–{money(rate * (1 + M['increase_high']))}</span>")
    row = (f"<tr><th scope=\"row\">{html.escape(u['size'])}</th><td class=\"true\">{true}</td>"
           f"<td>{promo}</td><td>{after}</td><td class=\"notes\">{html.escape(u.get('notes', ''))}</td></tr>")
    return row, round(avg_mid), round(rate), round(after_mid)


def quote_strip(slug):
    """Two anonymized, paraphrased renter quotes, picked deterministically per city for variety."""
    pool = SITE.get("renter_quotes") or []
    if not pool:
        return ""
    i = sum(ord(ch) for ch in slug) % len(pool)
    picks = [pool[i], pool[(i + 1) % len(pool)]] if len(pool) > 1 else [pool[i]]
    figs = "\n".join(f'  <figure><blockquote>{html.escape(q["text"])}</blockquote>'
                     f'<figcaption>{html.escape(q.get("who", "Renter"))}</figcaption></figure>' for q in picks)
    return ('<p class="quotes-label" id="renters-say">Renters say</p>\n'
            f'<div class="quotes" aria-labelledby="renters-say">\n{figs}\n</div>\n'
            '<p class="small quotes-note">Paraphrased and anonymized from public renter forums and social posts.</p>')


def calc_subs(rate10):
    return {"CALC_RATE": str(round(rate10 or 100)), "CALC_MONTHS": str(M["months"]),
            "CALC_FEE": str(round(M["admin_fee"])), "CALC_PROT": str(round(M["protection_per_month"])),
            "CALC_INC": str(round(M["increase_mid"] * 100)), "CALC_INC_FROM": str(M["increase_from_month"]),
            "CALC_PROMO_PCT": str(round((1 - M["promo_month1_fraction"]) * 100))}


def draft_rows():
    return "\n".join(
        f"<tr><th scope=\"row\">{s}</th><td class=\"true\">TBD</td><td>TBD</td><td>TBD</td><td class=\"notes\">Research pending</td></tr>"
        for s in ["5x5", "5x10", "10x10", "10x15", "10x20"])


def load_index():
    return json.loads(INDEX_JSON.read_text()) if INDEX_JSON.exists() else {"cities": []}


def save_index(idx):
    idx["cities"].sort(key=lambda c: c["name"])
    idx["updated"] = TODAY
    INDEX_JSON.write_text(json.dumps(idx, indent=2) + "\n")


def footer(prefix=""):
    p = prefix
    return f"""<footer class="site"><div class="wrap cols">
  <div>
    <a class="brand" href="{p}index.html">{SITE['site_name']}</a>
    <p>{html.escape(SITE.get('tagline', 'Storage · the price after the promo'))}</p>
  </div>
  <div>
    <h4>Explore</h4>
    <ul><li><a href="{p}index.html#cities">Cities</a></li><li><a href="{p}how-it-works.html">How it works &amp; methodology</a></li><li><a href="{p}size-guide.html">Size guide</a></li><li><a href="{p}about.html">About</a></li><li><a href="{p}privacy.html">Privacy Policy</a></li><li><a href="{p}terms.html">Terms of Use</a></li><li><a href="{p}sitemap.xml">Sitemap</a></li></ul>
  </div>
  <div>
    <h4>Disclosure</h4>
    <p>Some “compare” links are partner links marked <code>rel="sponsored"</code>. We may earn a commission at no cost to you. Partners never influence our estimates.</p>
    <p>Estimates only — not quotes, offers or financial advice.</p>
  </div>
</div></footer>"""


def replace_block(text, name, content):
    return re.sub(rf"(<!-- {name}_START -->).*?(<!-- {name}_END -->)",
                  lambda m: f"{m.group(1)}\n{content}\n{m.group(2)}", text, flags=re.S)


def rebuild(idx):
    live = [c for c in idx["cities"] if c.get("status") == "published"]
    base = SITE["site_url"].rstrip("/")
    upd = idx.get("updated", TODAY)
    urls = [(f"{base}/", upd), (f"{base}/how-it-works.html", upd), (f"{base}/size-guide.html", upd),
            (f"{base}/about.html", upd), (f"{base}/privacy.html", upd), (f"{base}/terms.html", upd)]
    urls += [(f"{base}/{c['path']}", c["updated"]) for c in live]
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    xml += [f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>" for u, d in urls]
    xml.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(xml) + "\n")
    (ROOT / "robots.txt").write_text("User-agent: *\nAllow: /\nDisallow: /cities/_template.html\nDisallow: /scripts/\n"
                                     "Disallow: /previews/\nDisallow: /outreach/\nDisallow: /revenue-model/\n\n"
                                     f"Sitemap: {base}/sitemap.xml\n")

    groups = {}
    for c in live:
        code = c["slug"].rsplit("-", 1)[-1].upper()
        groups.setdefault(code, []).append(c)
    codes = sorted(groups, key=lambda s: (STATE_NAMES.get(s, s), s))
    blocks = ['  <div class="state-chips" role="toolbar" aria-label="States with city pages">',
              '    <button type="button" class="chip" data-state="*" aria-pressed="false">All cities</button>']
    for code in codes:
        blocks.append(f'    <button type="button" class="chip" data-state="{code}" aria-pressed="false">{html.escape(STATE_NAMES.get(code, code))}</button>')
    blocks.append("  </div>")
    blocks.append('  <div class="state-groups">')
    for code in codes:
        name = STATE_NAMES.get(code, code)
        cities = sorted(groups[code], key=lambda c: c["name"])
        count = "1 city" if len(cities) == 1 else f"{len(cities)} cities"
        blocks.append(f'  <section class="state-group" id="state-{code.lower()}" data-state="{code}" data-state-name="{html.escape(name)}">')
        blocks.append(f'    <h3 class="state-heading" tabindex="-1">{html.escape(name)} <span class="state-count">{count}</span></h3>')
        blocks.append('    <ul class="cities">')
        for c in cities:
            fig = (f'<span class="fig">${c["true_avg_10x10"]}<small>/mo</small></span>'
                   f'<span class="cap">10x10 true 6-month average</span>'
                   f'<span class="adv">vs ${c["rate_10x10"]} advertised rate</span>') if c.get("true_avg_10x10") else ""
            blocks.append(f'    <li data-state="{code}"><a class="tile" href="{c["path"]}"><span class="name">{html.escape(c["name"])}</span>{fig}'
                          f'<span class="go">View sizes &amp; sources →</span></a></li>')
        blocks.append("    </ul>")
        blocks.append("  </section>")
    blocks.append("  </div>")
    for name in ["index.html", "about.html", "how-it-works.html", "size-guide.html", "privacy.html", "terms.html"]:
        f = ROOT / name
        if not f.exists():
            continue
        text = f.read_text()
        if name == "index.html":
            text = replace_block(text, "CITY_LIST", "\n".join(blocks))
        text = replace_block(text, "FOOTER", footer(""))
        f.write_text(text)
    city_footer = footer("../")
    for city_html in sorted((ROOT / "cities").glob("*.html")):
        if city_html.name.startswith("_"):
            continue
        text = city_html.read_text()
        new, n = re.subn(r'<footer class="site">.*?</footer>', city_footer, text, count=1, flags=re.S)
        if n:
            city_html.write_text(new)
    print(f"sitemap.xml: {len(urls)} urls; index.html: {len(live)} cities in {len(codes)} states")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug", nargs="?")
    ap.add_argument("name", nargs="?", help='Metro name, e.g. "Austin, TX"')
    ap.add_argument("--config", help="JSON with market data; publishes the page")
    ap.add_argument("--force", action="store_true", help="overwrite an existing page")
    ap.add_argument("--rebuild", action="store_true", help="only regenerate sitemap + home list + footers")
    ap.add_argument("--all", action="store_true", help="re-publish every city with a data/cities/<slug>.json")
    a = ap.parse_args()
    idx = load_index()
    if a.rebuild:
        rebuild(idx); return
    if a.all:
        for c in list(idx["cities"]):
            cfgp = ROOT / "data" / "cities" / f"{c['slug']}.json"
            if cfgp.exists():
                publish(idx, c["slug"], c["name"], str(cfgp), True)
        rebuild(idx); return
    if not a.slug or not a.name:
        ap.error("slug and name are required (or use --rebuild)")
    if not SLUG_RE.match(a.slug) or a.slug.startswith("_"):
        ap.error("slug must be lowercase letters/digits/hyphens, e.g. austin-tx")
    publish(idx, a.slug, a.name, a.config, a.force)
    rebuild(idx)


def publish(idx, slug, name, config, force):
    out = ROOT / "cities" / f"{slug}.html"
    if out.exists() and not force:
        sys.exit(f"{out} exists; use --force to overwrite")

    cfg = json.loads(Path(config).read_text()) if config else None
    entry = {"slug": slug, "name": name, "path": f"cities/{slug}.html",
             "status": "published" if cfg else "draft", "updated": TODAY}
    prev = next((c for c in idx["cities"] if c["slug"] == slug), None)
    entry["published"] = (prev or {}).get("published") or (TODAY if cfg else None)

    short = name.split(",")[0].strip()
    if cfg:
        rows, avg10, rate10, after10 = [], None, None, None
        for u in cfg["units"]:
            r, avg, rate, after = unit_row(u); rows.append(r)
            if u["size"].replace(" ", "") == "10x10": avg10, rate10, after10 = avg, rate, after
        entry.update(true_avg_10x10=avg10, rate_10x10=rate10, data_asof=cfg["data_asof"])
        tips = cfg.get("local_tips") or []
        local = (f"<h2 id=\"local\">Notes for {html.escape(short)}</h2>\n<ul class=\"prose\">\n"
                 + "\n".join(f"  <li>{html.escape(t)}</li>" for t in tips) + "\n</ul>") if tips else ""
        sources = "\n".join(f'    <li><a href="{html.escape(s["url"])}" rel="nofollow noopener" target="_blank">{html.escape(s["label"])}</a></li>'
                            for s in cfg["sources"])
        subs = {"INTRO": html.escape(cfg["intro"]), "TABLE_ROWS": "\n".join(rows), "DATA_ASOF": html.escape(cfg["data_asof"]),
                "LOCAL_TIPS": local, "SOURCES": sources, "ROBOTS_META": "",
                **calc_subs(rate10),
                "RATE_10": money(rate10) if rate10 else "—", "AFTER_10": f"~{money(after10)}" if after10 else "—",
                "TRUE_10": f"~{money(avg10)}" if avg10 else "—"}
    else:
        subs = {"INTRO": f"Draft: research for {html.escape(name)} is pending.", "TABLE_ROWS": draft_rows(),
                "RATE_10": "—", "AFTER_10": "—", "TRUE_10": "—",
                "DATA_ASOF": "TBD", "LOCAL_TIPS": "", "SOURCES": "    <li>TBD</li>",
                "ROBOTS_META": '<meta name="robots" content="noindex">', **calc_subs(None)}
    subs.update(QUOTES=quote_strip(slug), CITY_NAME=html.escape(name), CITY_NAME_Q=quote(name, safe=""),
                CITY_SHORT=html.escape(short), SLUG=slug,
                UPDATED=TODAY, SITE_URL=SITE["site_url"].rstrip("/"), FOOTER=footer("../"))
    page = TEMPLATE.read_text()
    for k, v in subs.items():
        page = page.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{[A-Z_]+\}\}", page)
    if left:
        sys.exit(f"unfilled placeholders: {left}")
    out.write_text(page)
    idx["cities"] = [c for c in idx["cities"] if c["slug"] != slug] + [entry]
    if cfg:
        order = idx.setdefault("order", [])
        if slug not in order:
            order.append(slug)
    save_index(idx)
    print(f"wrote {out.relative_to(ROOT)} ({entry['status']})")


if __name__ == "__main__":
    main()
