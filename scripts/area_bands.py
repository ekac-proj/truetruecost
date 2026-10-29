"""Pull cited neighborhood street-rate examples out of city JSON.

The figures are copied from local_tips that already name StorageCafe areas.
Nothing here assigns a ZIP code to a dollar amount.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRICE_RE = re.compile(r"~?\$\d[\d,]*(?:[–\-]\s*\$\d[\d,]*)?\+?")

AREA_HINT = re.compile(
    r"among the cheaper|cheapest areas|Cheaper areas per|Cheapest areas per|by neighborhood"
)

LABEL_TRAIL = re.compile(
    r"\s+(?:average about|averages about|can run|run highest|runs highest|run|runs|is the most expensive|are the most expensive|is among the highest)$",
    re.I,
)


def _clean_label(text):
    label = text.strip(" \t\r\n.;,")
    label = re.sub(r"^(and|while)\s+", "", label, flags=re.I)
    label = re.sub(r"^(?:about)\s+", "", label, flags=re.I)
    label = LABEL_TRAIL.sub("", label).strip(" \t.;,")
    label = re.sub(r"\s+", " ", label)
    return label


def items_from_clause(clause):
    """Split a clause into named areas. A price after several names stays with that whole group."""
    clause = clause.replace("(", " ").replace(")", " ")
    clause = re.sub(r"\s+", " ", clause).strip(" .")
    matches = list(PRICE_RE.finditer(clause))
    if not matches:
        return []
    items = []
    start = 0
    for match in matches:
        label = _clean_label(clause[start:match.start()])
        rate = re.sub(r"\s+", "", match.group(0)).replace("-", "–")
        window = clause[max(0, match.start() - 16):match.start()].lower()
        if "about" in window and not rate.startswith("~"):
            rate = "~" + rate
        if label:
            items.append({"name": label, "rate": rate})
        start = match.end()
    return items


def _unit(tip):
    if "10x10" in tip:
        return "10x10"
    if "standard unit" in tip:
        return "standard unit"
    return "as published"


def _source(cfg):
    sources = cfg.get("sources") or []
    stats = [s for s in sources if "storagecafe.com" in s.get("url", "") and "industry-statistics" in s.get("url", "")]
    picked = (stats or [s for s in sources if "storagecafe.com" in s.get("url", "")])
    if not picked:
        return {"label": "StorageCafe city statistics", "url": "https://www.storagecafe.com/"}
    return {"label": picked[0]["label"], "url": picked[0]["url"]}


def _asof(cfg, source_label):
    match = re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+20\d{2}", source_label)
    if match:
        months = {
            "Jan": "Jan", "Feb": "Feb", "Mar": "Mar", "Apr": "Apr", "May": "May", "Jun": "Jun",
            "Jul": "Jul", "Aug": "Aug", "Sep": "Sep", "Oct": "Oct", "Nov": "Nov", "Dec": "Dec",
        }
        year = re.search(r"20\d{2}", match.group(0)).group(0)
        return f"{months[match.group(1)]} {year}"
    data_asof = cfg.get("data_asof") or ""
    found = re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+20\d{2}", data_asof)
    return found.group(0) if found else data_asof


def _leftover_parts(leftover):
    leftover = (leftover or "").strip(" .")
    if not leftover:
        return [], []
    # A sentence that only finishes "run highest" / "are the most expensive" is not a new fact.
    if re.fullmatch(r"(?:run highest|are the most expensive|is the most expensive)", leftover, re.I):
        return [], []
    extra = items_from_clause(leftover)
    if extra and not leftover.lower().startswith("oakland"):
        return extra, []
    sentence = leftover.rstrip(".") + "."
    return [], [sentence]


def _split_rest(rest):
    parts = re.split(r"\.\s+", rest.strip().rstrip("."), maxsplit=1)
    higher = parts[0].strip()
    leftover = parts[1].strip() if len(parts) > 1 else ""
    return higher, leftover


def _clauses(text):
    """Return (lower clause, higher clause, leftover sentence) or None."""
    match = re.search(
        r"lists (.+?) among the cheaper areas for a standard unit\. (.+?) is among the highest\.(?:\s*(.*))?$",
        text,
    )
    if match:
        return match.group(1), match.group(2), (match.group(3) or "").strip()
    match = re.search(
        r"lists (.+?) (?:among|as) the cheapest areas(?: for a (?:standard unit|10x10))?, while (.+)$",
        text,
    )
    if match:
        higher, leftover = _split_rest(match.group(2))
        return match.group(1), higher, leftover
    match = re.search(r"(?:Cheaper|Cheapest) areas per StorageCafe include (.+?); (.+)$", text)
    if match:
        higher, leftover = _split_rest(match.group(2))
        return match.group(1), higher, leftover
    match = re.search(r"by neighborhood: (.+?), while (.+)$", text)
    if match:
        higher, leftover = _split_rest(match.group(2))
        return match.group(1), higher, leftover
    return None


def parse_tip(tip):
    """Return a band dict, or None if this tip is not an area price list."""
    text = " ".join(tip.split())
    if "lowest around" in text or "highest in" in text or "highest around" in text:
        return None
    if not AREA_HINT.search(text):
        return None
    clauses = _clauses(text)
    if not clauses:
        raise ValueError(f"unparsed area tip: {text}")
    lower = items_from_clause(clauses[0])
    higher = items_from_clause(clauses[1])
    if not lower or not higher:
        raise ValueError(f"area tip missing prices: {text}")
    also, aside = _leftover_parts(clauses[2])
    # Unit size has to be named on the area list itself. A later sentence about another city does not count.
    unit_text = text.split(" Oakland ")[0]
    return {
        "unit": _unit(unit_text),
        "lower": lower,
        "higher": higher,
        "also": also,
        "aside": aside,
    }


def bands_for_config(cfg):
    found = []
    for tip in cfg.get("local_tips") or []:
        parsed = parse_tip(tip)
        if parsed:
            found.append(parsed)
    if not found:
        return None
    if len(found) > 1:
        raise ValueError("more than one area-price tip")
    band = found[0]
    source = _source(cfg)
    band["source_label"] = source["label"]
    band["source_url"] = source["url"]
    band["asof"] = _asof(cfg, source["label"])
    return band


def load_all_bands():
    bands = {}
    errors = []
    for path in sorted((ROOT / "data" / "cities").glob("*.json")):
        cfg = json.loads(path.read_text())
        try:
            band = bands_for_config(cfg)
        except ValueError as exc:
            errors.append(f"{path.stem}: {exc}")
            continue
        if band:
            bands[path.stem] = band
    if errors:
        raise SystemExit("area band parse errors:\n" + "\n".join(errors))
    return bands


def _items_html(items):
    rows = []
    for item in items:
        rows.append(
            f'<li><span class="band-name">{html.escape(item["name"])}</span>'
            f'<span class="band-rate">{html.escape(item["rate"])}</span></li>'
        )
    return "\n".join(rows)


def render_band_html(band):
    """Static city-page markup. The same facts are rendered from JSON on near.html."""
    if not band:
        return ""
    asof = html.escape(band["asof"])
    if band["unit"] == "10x10":
        unit_sentence = "These are 10x10 street rates"
    elif band["unit"] == "standard unit":
        unit_sentence = "These are street rates for what StorageCafe calls a standard unit"
    else:
        unit_sentence = "The sentence we copied does not name the unit size"
    parts = [
        '<div class="area-bands">',
        f'<h3>Area examples StorageCafe published ({asof})</h3>',
        f'<p>{unit_sentence}, copied from that city statistics page. '
        'They show how wide the spread between named areas can be. '
        'They are not a price for your ZIP, not a facility quote, and not the six-month true cost on this page. '
        'Your ZIP is not matched to any of these areas.</p>',
        '<div class="band-grid">',
        '<div><h4>Lower-priced areas they named</h4><ul>',
        _items_html(band["lower"]),
        '</ul></div>',
        '<div><h4>Higher-priced areas they named</h4><ul>',
        _items_html(band["higher"]),
        '</ul></div>',
    ]
    if band.get("also"):
        parts.extend([
            '<div><h4>Also cited</h4><ul>',
            _items_html(band["also"]),
            '</ul></div>',
        ])
    parts.append('</div>')
    for sentence in band.get("aside") or []:
        parts.append(f'<p>{html.escape(sentence)}</p>')
    parts.append(
        f'<p class="small">Source: <a href="{html.escape(band["source_url"])}" rel="nofollow noopener" target="_blank">{html.escape(band["source_label"])}</a></p>'
    )
    parts.append('</div>')
    return "\n".join(parts)


if __name__ == "__main__":
    bands = load_all_bands()
    print(f"{len(bands)} cities")
    for slug, band in bands.items():
        print(f"\n{slug} [{band['unit']}] {band['asof']}")
        print("  lower:", band["lower"])
        print("  higher:", band["higher"])
        if band["also"]:
            print("  also:", band["also"])
        if band["aside"]:
            print("  aside:", band["aside"])
