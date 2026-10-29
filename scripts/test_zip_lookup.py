#!/usr/bin/env python3
"""Checks for the committed ZIP crosswalk. No network and no invented prices."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from area_bands import bands_for_config, load_all_bands  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main():
    data = json.loads((ROOT / "data" / "zip-lookup.json").read_text())
    zips = data["zips"]
    bands = data["bands"]

    austin = zips["78701"]
    assert austin[0] == "austin-tx" and austin[1] == 100, austin
    assert "$" not in json.dumps(austin)

    beverly = zips["90210"]
    assert beverly[0] == "los-angeles-ca", beverly
    assert beverly[1] < 80
    assert any(place[0] == "Beverly Hills" and place[2] >= 30 for place in beverly[6]), beverly
    assert "$" not in json.dumps(beverly)

    katy = zips["77494"]
    assert katy[0] == "" and katy[2] == "Katy", katy
    assert any(item[0] == "houston-tx" and item[1] < 50 for item in katy[5]), katy

    burlington = zips["05401"]
    assert burlington[0] == "burlington-vt" and burlington[1] == 100, burlington
    assert zips["05403"][0] == "south-burlington-vt"
    assert zips["05405"][0] == "burlington-vt"
    assert zips["05408"][0] == "burlington-vt"
    assert "metro proxy" in data["cities"]["burlington-vt"]["note"]
    assert "$" not in json.dumps(burlington)

    assert zips["10001"][0] == "new-york-ny"
    assert zips["96825"][0] == "east-honolulu-hi"
    assert zips["99501"][0] == "anchorage-ak"
    assert zips["94103"][0] == "san-francisco-ca"
    assert "85001" not in zips  # not a 2020 ZCTA; do not guess
    assert "30301" not in zips

    houston = bands["houston-tx"]
    assert houston["unit"] == "10x10"
    assert "Beechnut" in houston["lower"][0]["name"]
    assert houston["higher"][0]["rate"].startswith("$250")
    assert "storagecafe.com" in houston["source_url"]
    assert bands["phoenix-az"]["unit"] == "10x10"
    assert bands["san-francisco-ca"]["unit"] == "as published"
    assert any("Oakland" in line for line in bands["san-francisco-ca"]["aside"])

    # City JSON remains the source for area examples. The lookup file must match it.
    live = load_all_bands()
    assert set(live) == set(bands)
    assert live["chicago-il"]["higher"][0]["name"].startswith("Lakeview")
    sample = json.loads((ROOT / "data" / "cities" / "houston-tx.json").read_text())
    assert bands_for_config(sample)["lower"][0]["rate"] == houston["lower"][0]["rate"]

    # A ZIP row never carries a storage price.
    for key in ("78701", "90210", "77494", "10001", "72703"):
        assert "$" not in json.dumps(zips[key])
    print(f"ok cities={len(data['cities'])} zips={len(zips)} bands={len(bands)}")


if __name__ == "__main__":
    main()
