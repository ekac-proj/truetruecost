#!/usr/bin/env python3
"""Build data/zip-lookup.json from Census 2020 geography and published cities.

Download the three Census files into a directory (default /tmp/census):

  tab20_zcta520_place20_natl.txt
  2020_Gaz_zcta_national.txt
  2020_Gaz_place_national.txt

The output maps a ZIP Code Tabulation Area to a published city page when at
least half of the ZCTA's land area sits in that Census place. It does not
contain storage prices by ZIP.
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from area_bands import load_all_bands  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "zip-lookup.json"

FIPS = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT",
    "10": "DE", "11": "DC", "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL",
    "18": "IN", "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME", "24": "MD",
    "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT", "31": "NE",
    "32": "NV", "33": "NH", "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND",
    "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD",
    "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA", "54": "WV",
    "55": "WI", "56": "WY",
}
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
# Census place names that are the legal place behind one of our city slugs.
ALIASES = {
    "boise-city-id": "boise-id",
    "augusta-richmond-county-ga": "augusta-ga",
    "nashville-davidson-tn": "nashville-tn",
    "lexington-fayette-ky": "lexington-ky",
    "urban-honolulu-hi": "honolulu-hi",
    "louisville-jefferson-county-ky": "louisville-ky",
    "indianapolis-city-balance-in": "indianapolis-in",
}
SUFFIXES = (
    " consolidated government (balance)",
    " metropolitan government (balance)",
    " metro government (balance)",
    " urban county (balance)",
    " city and borough",
    " city (balance)",
    " municipality",
    " consolidated government",
    " metropolitan government",
    " metro government",
    " urban county",
    " city",
    " town",
    " village",
    " borough",
    " CDP",
    " comunidad",
    " zona urbana",
)
MAJORITY = 50  # nearest percent of ZCTA land area
OVERLAP_MIN = 5
NEAR_MILES = 60
TOP_NEAR = 3


def strip_suffix(name):
    for suffix in SUFFIXES:
        if name.endswith(suffix):
            return name[: -len(suffix)].strip()
    return name.strip()


def slugify(name, state):
    text = name.lower().replace("'", "").replace(".", "").replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return f"{text}-{state.lower()}"


def haversine(lat1, lon1, lat2, lon2):
    radius = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def read_table(path):
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    header = [col.strip() for col in lines[0].split("\t")]
    rows = []
    for line in lines[1:]:
        if not line.strip():
            continue
        cols = [col.strip() for col in line.split("\t")]
        if len(cols) < len(header):
            continue
        rows.append(dict(zip(header, cols)))
    return rows


def load_places(path, wanted):
    """Map published slug -> census place, preferring the largest land area."""
    by_slug = {}
    for row in read_table(path):
        state = row["USPS"]
        if state not in STATE_NAMES:
            continue
        short = strip_suffix(row["NAME"])
        slug = ALIASES.get(slugify(short, state), slugify(short, state))
        if slug not in wanted:
            continue
        land = int(row["ALAND"] or 0)
        current = by_slug.get(slug)
        if current and current["land"] >= land:
            continue
        by_slug[slug] = {
            "geoid": row["GEOID"],
            "name": short,
            "land": land,
            "lat": float(row["INTPTLAT"]),
            "lng": float(row["INTPTLONG"]),
        }
    missing = sorted(wanted - set(by_slug))
    if missing:
        raise SystemExit("no Census place for: " + ", ".join(missing))
    return by_slug


def load_zcta_points(path):
    points = {}
    for row in read_table(path):
        geoid = row["GEOID"].zfill(5)
        if not re.fullmatch(r"\d{5}", geoid):
            continue
        points[geoid] = (float(row["INTPTLAT"]), float(row["INTPTLONG"]))
    return points


def load_overlaps(path):
    """zip -> {land, places: {geoid: (part_land, display_name, state)}}"""
    overlaps = {}
    raw = path.read_text(encoding="utf-8-sig").splitlines()
    for line in raw[1:]:
        parts = line.split("|")
        if len(parts) < 18 or not parts[1] or not parts[9]:
            continue
        zcta = parts[1].zfill(5)
        place_geoid = parts[9]
        state = FIPS.get(place_geoid[:2])
        if not state:
            continue
        try:
            zcta_land = int(parts[3] or 0)
            part_land = int(parts[16] or 0)
        except ValueError:
            continue
        bucket = overlaps.setdefault(zcta, {"land": zcta_land, "places": {}})
        bucket["land"] = max(bucket["land"], zcta_land)
        name = strip_suffix(parts[10]) or parts[10]
        prev = bucket["places"].get(place_geoid)
        if prev and prev[0] >= part_land:
            continue
        bucket["places"][place_geoid] = (part_land, name, state)
    return overlaps


def nearest(origin, cities, skip):
    ranked = []
    lat, lng = origin
    for slug, city in cities.items():
        if slug in skip:
            continue
        dist = haversine(lat, lng, city["lat"], city["lng"])
        if dist <= NEAR_MILES:
            miles = max(1, int(round(dist)))
            ranked.append((miles, slug))
    ranked.sort()
    return [[slug, miles] for miles, slug in ranked[:TOP_NEAR]]


def build(census_dir):
    census_dir = Path(census_dir)
    index = json.loads((ROOT / "data" / "cities.json").read_text())
    published = [c for c in index["cities"] if c.get("status") == "published"]
    wanted = {c["slug"] for c in published}
    places = load_places(census_dir / "2020_Gaz_place_national.txt", wanted)
    geoid_slug = {place["geoid"]: slug for slug, place in places.items()}
    points = load_zcta_points(census_dir / "2020_Gaz_zcta_national.txt")
    overlaps = load_overlaps(census_dir / "zcta_place.txt")

    cities = {}
    for city in published:
        place = places[city["slug"]]
        state = city["slug"].rsplit("-", 1)[-1].upper()
        cities[city["slug"]] = {
            "name": city["name"],
            "short": city["name"].split(",")[0].strip(),
            "state": state,
            "state_name": STATE_NAMES[state],
            "rate": city.get("rate_10x10"),
            "true": city.get("true_avg_10x10"),
            "lat": place["lat"],
            "lng": place["lng"],
        }

    zips = {}
    for zcta, origin in points.items():
        info = overlaps.get(zcta)
        slug = ""
        pct = 0
        place_name = ""
        state = ""
        overlap = []
        others = []
        skip = set()
        if info and info["land"] > 0 and info["places"]:
            ranked = sorted(info["places"].items(), key=lambda item: -item[1][0])
            geoid, (part, name, st) = ranked[0]
            pct = int(round(100 * part / info["land"]))
            place_name = name
            state = st
            if geoid in geoid_slug and pct >= OVERLAP_MIN:
                published_slug = geoid_slug[geoid]
                if pct >= MAJORITY:
                    slug = published_slug
                    skip.add(slug)
                else:
                    dist = haversine(origin[0], origin[1], cities[published_slug]["lat"], cities[published_slug]["lng"])
                    overlap.append([published_slug, pct, max(1, int(round(dist)))])
                    skip.add(published_slug)
            # Other places with a real share of the land. 90210 is the case this exists for:
            # Los Angeles is the land-area majority and Beverly Hills is still a large part.
            if pct < 80:
                for other_geoid, (other_part, other_name, other_state) in ranked[1:]:
                    other_pct = int(round(100 * other_part / info["land"]))
                    if other_pct < 15:
                        break
                    others.append([other_name, other_state, other_pct])
                    if len(others) == 2:
                        break
            for other_geoid, (other_part, _name, _st) in ranked[1:]:
                other_slug = geoid_slug.get(other_geoid)
                if not other_slug or other_slug == slug:
                    continue
                other_pct = int(round(100 * other_part / info["land"]))
                if other_pct < OVERLAP_MIN:
                    continue
                dist = haversine(origin[0], origin[1], cities[other_slug]["lat"], cities[other_slug]["lng"])
                overlap.append([other_slug, other_pct, max(1, int(round(dist)))])
                skip.add(other_slug)
            overlap.sort(key=lambda item: -item[1])
        near = nearest(origin, cities, skip)
        if not state and not slug and not overlap and not near:
            continue
        # [slug, land %, place, state, near [slug, miles], overlap [slug, %, miles], other places [name, state, %]]
        zips[zcta] = [slug, pct, place_name, state, near, overlap, others]

    payload = {
        "meta": {
            "geography": "U.S. Census Bureau 2020 ZIP Code Tabulation Area (ZCTA) to Place relationship file, with 2020 Gazetteer internal points for distance.",
            "relationship_file": "https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/tab20_zcta520_place20_natl.txt",
            "gazetteer": "https://www.census.gov/geographies/reference-files/time-series/geo/gazetteer-files.html",
            "majority_land_pct": MAJORITY,
            "near_miles": NEAR_MILES,
            "note": "A ZCTA approximates a USPS ZIP Code. It is not a USPS ZIP Code. A city match means about half or more of the ZCTA land area is inside that Census place. Distance is straight-line miles between Census internal points, not drive time. This file has no storage prices.",
        },
        "cities": {slug: {k: v for k, v in city.items() if k not in ("lat", "lng")} for slug, city in cities.items()},
        "bands": load_all_bands(),
        "zips": zips,
    }
    OUT.write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)} cities={len(cities)} zips={len(zips)} bands={len(payload['bands'])} bytes={OUT.stat().st_size}")
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--census-dir", default="/tmp/census")
    args = parser.parse_args()
    build(args.census_dir)


if __name__ == "__main__":
    main()
