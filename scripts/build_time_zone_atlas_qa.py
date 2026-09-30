"""Build the optional, suspended-on-import time-zone atlas QA package.

Map boundaries come from Timezone Boundary Builder 2026d. The generated SVGs
are answer illustrations, not claims that a UTC offset defines a legal zone.
"""

from __future__ import annotations

import argparse
import html
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import genanki
from shapely.geometry import Point, box, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/time-zone-atlas-qa.json"
BOUNDARIES = ROOT / ".tmp/reference-lines-qa/timezones-2026d.geojson.zip"
LAND = ROOT / "data/bundles/world-islands.json"
MEDIA = ROOT / ".tmp/time-zone-atlas-qa/media"
OUTPUT = ROOT / "dist/time-zone-atlas-qa.apkg"
MODEL_ID = 1_607_432_001
DECK_ROOT = "GeoTrainer::Reference Lines & Time::05 Time Zone Atlas"
CONTINENTS = ("Africa", "Asia", "Europe", "North America", "Oceania", "South America")
DECK_IDS = {name: 1_607_431_200 + index for index, name in enumerate(CONTINENTS, 1)}
MODEL_NAME = "Time Zone Atlas — QA v1"
BRAZIL = {
    "America/Noronha", "America/Belem", "America/Fortaleza", "America/Recife",
    "America/Araguaina", "America/Maceio", "America/Bahia", "America/Sao_Paulo",
    "America/Campo_Grande", "America/Cuiaba", "America/Santarem",
    "America/Porto_Velho", "America/Boa_Vista", "America/Manaus",
    "America/Eirunepe", "America/Rio_Branco",
}
INSTANT = datetime(2026, 9, 25, 12, tzinfo=UTC)
SOURCES = {
    "brasilia": "https://www.gov.br/ouvidorias/pt-br/ouvidorias/eventos/seminarios-nacionais-de-ouvidoria-2025/manaus/programacao",
    "manaus": "https://www.gov.br/ouvidorias/pt-br/ouvidorias/eventos/seminarios-nacionais-de-ouvidoria-2025/manaus/programacao",
    "new-york": "https://www.nist.gov/pml/time-and-frequency-division/local-time-faqs",
    "los-angeles": "https://www.nist.gov/pml/time-and-frequency-division/local-time-faqs",
    "mexico-city": "https://www.diputados.gob.mx/LeyesBiblio/pdf/LHHEUM.pdf",
    "london": "https://www.gov.uk/when-do-the-clocks-change",
    "paris": "https://www.ecb.europa.eu/paym/target/consolidation/profuse/shared/pdf/2021-05-20-t2_glossary_v2-3.pdf",
    "urumqi-local": "https://github.com/eggert/tz/blob/main/asia",
    "urumqi-official": "https://github.com/eggert/tz/blob/main/asia",
    "taipei": "https://www.stdtime.gov.tw/english/details/details.htm",
    "tokyo": "https://www.nict.go.jp/en/sts/jst.html",
    "adelaide": "https://www.stylemanual.gov.au/grammar-punctuation-and-conventions/numbers-and-measurements/dates-and-time",
    "lord-howe": "https://www.stylemanual.gov.au/grammar-punctuation-and-conventions/numbers-and-measurements/dates-and-time",
}
AMBIGUOUS_BARE_CODES = {"ACT", "BST", "CST", "EDT", "EST", "IST", "PST"}


def projection(bounds: list[float], width: int, height: int):
    west, south, east, north = bounds
    scale = min((width - 24) / (east - west), (height - 24) / (north - south))
    cx, cy = (west + east) / 2, (south + north) / 2
    return lambda lon, lat: (round(width / 2 + (lon - cx) * scale, 2),
                             round(height / 2 - (lat - cy) * scale, 2))


def path_data(geometry, project) -> str:
    if geometry.is_empty:
        return ""
    kind = geometry.geom_type
    if kind in {"MultiPolygon", "MultiLineString", "GeometryCollection"}:
        return " ".join(filter(None, (path_data(part, project) for part in geometry.geoms)))
    if kind == "Polygon":
        rings = [geometry.exterior, *geometry.interiors]
        return " ".join(path_data(ring, project) + "Z" for ring in rings)
    if kind in {"LineString", "LinearRing"}:
        points = [project(x, y) for x, y in geometry.coords]
        if len(points) < 2:
            return ""
        return "M" + "L".join(f"{x},{y}" for x, y in points)
    return ""


def svg_path(geometry, project, attrs: str) -> str:
    d = path_data(geometry, project)
    return f'<path d="{d}" {attrs}/>' if d else ""


def map_svg(item: dict, zones: list[tuple[str, object]], land: list) -> str:
    width, height = 480, 250
    bounds = item["bounds"]
    extent = box(*bounds)
    project = projection(bounds, width, height)
    tol = max(bounds[2] - bounds[0], bounds[3] - bounds[1]) / 650
    point = Point(item["lon"], item["lat"])
    matches = [tzid for tzid, geom in zones if tzid == item["tzid"] and geom.covers(point)]
    if not matches:
        raise ValueError(f"{item['key']}: selected civil-time geometry misses place")
    target = {item["tzid"]}
    if item.get("brazil"):
        wanted = INSTANT.astimezone(ZoneInfo(item["tzid"])).utcoffset()
        target = {tzid for tzid in BRAZIL
                  if INSTANT.astimezone(ZoneInfo(tzid)).utcoffset() == wanted}
    elements = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" '
                f'aria-label="Continental map of {html.escape(item["place"])} and its time area">',
                '<rect width="480" height="250" fill="#b8d9df"/>']
    for lon in range(-180, 181, 15):
        if bounds[0] <= lon <= bounds[2]:
            x, _ = project(lon, 0)
            elements.append(f'<path d="M{x},0V250" stroke="#d9e9e9" stroke-width=".6"/>')
    for lat in range(-75, 76, 15):
        if bounds[1] <= lat <= bounds[3]:
            _, y = project(0, lat)
            elements.append(f'<path d="M0,{y}H480" stroke="#d9e9e9" stroke-width=".6"/>')
    for geom in land:
        if geom.intersects(extent):
            clipped = geom.intersection(extent).simplify(tol, preserve_topology=True)
            elements.append(svg_path(clipped, project, 'fill="#f1ead9" fill-rule="evenodd"'))
            boundary = geom.boundary.intersection(extent).simplify(tol, preserve_topology=True)
            elements.append(svg_path(boundary, project,
                                     'fill="none" stroke="#9baba3" stroke-width=".8"'))
    inset_geoms = []
    for tzid, geom in zones:
        if tzid in target and geom.intersects(extent):
            inset_geoms.append(geom)
            clipped = geom.intersection(extent).simplify(tol, preserve_topology=True)
            elements.append(svg_path(clipped, project,
                                     'fill="#e9ae8e" fill-opacity=".9" fill-rule="evenodd"'))
            boundary = geom.boundary.intersection(extent).simplify(tol, preserve_topology=True)
            style = ('fill="none" stroke="#9c5d24" stroke-width="1.5" '
                     'stroke-dasharray="5 3"' if item.get("special") else
                     'fill="none" stroke="#a84c35" stroke-width="1.5"')
            elements.append(svg_path(boundary, project, style))
    x, y = project(item["lon"], item["lat"])
    anchor = "end" if x > 325 else "start"
    label_x = x - 12 if anchor == "end" else x + 12
    label_y = min(235, max(25, y - 8))
    elements += [f'<circle cx="{x}" cy="{y}" r="9" fill="#fff9ea"/>',
                 f'<circle cx="{x}" cy="{y}" r="4.5" fill="#102c36"/>',
                 f'<text x="{label_x}" y="{label_y}" text-anchor="{anchor}" '
                 'fill="#102c36" stroke="#fff9ea" stroke-width="4" paint-order="stroke" '
                 f'font-size="16" font-family="Arial,sans-serif" font-weight="700">'
                 f'{html.escape(item["place"])}</text>', '</svg>']
    if item["key"] in {"noronha", "lord-howe", "taipei", "singapore"}:
        selected = unary_union(inset_geoms)
        minx, miny, maxx, maxy = selected.bounds
        span_x = max(.7, (maxx - minx) * 2.4, (maxy - miny) * 2.4 * 130 / 95)
        if item["key"] == "taipei":
            span_x = 8
        span_y = span_x * 95 / 130
        lon, lat = item["lon"], item["lat"]
        detail_bounds = [lon - span_x / 2, lat - span_y / 2,
                         lon + span_x / 2, lat + span_y / 2]
        detail_extent = box(*detail_bounds)
        detail_project = projection(detail_bounds, 130, 95)
        detail = ['<g transform="translate(340 10)">',
                  '<rect x="0" y="0" width="130" height="95" rx="7" '
                  'fill="#b8d9df" stroke="#526e70" stroke-width="1.5"/>']
        for geom in land:
            if geom.intersects(detail_extent):
                clipped = geom.intersection(detail_extent).simplify(span_x / 900,
                                                                    preserve_topology=True)
                detail.append(svg_path(clipped, detail_project,
                                       'fill="#f1ead9" fill-rule="evenodd"'))
        for geom in inset_geoms:
            if geom.intersects(detail_extent):
                clipped = geom.intersection(detail_extent).simplify(span_x / 900,
                                                                    preserve_topology=True)
                detail.append(svg_path(clipped, detail_project,
                                       'fill="#e9ae8e" stroke="#a84c35" '
                                       'stroke-width="1.5" fill-rule="evenodd"'))
        px, py = detail_project(lon, lat)
        detail += [f'<circle cx="{px}" cy="{py}" r="3" fill="#102c36" '
                   'stroke="#fff9ea" stroke-width="1.5"/>',
                   '<text x="7" y="87" fill="#102c36" stroke="#fff9ea" '
                   'stroke-width="2.5" paint-order="stroke" font-size="10" '
                   'font-family="Arial,sans-serif" font-weight="700">DETAIL</text>',
                   '<rect x="0" y="0" width="130" height="95" rx="7" fill="none" '
                   'stroke="#526e70" stroke-width="1.5"/>', '</g>']
        elements[-1:-1] = detail
    return "".join(elements)


def template(question: str, answer: str, zone: str, gate: str) -> dict:
    front = (f'{{{{#{gate}}}}}<main class="tza"><div class="mast">TIME ZONE ATLAS</div>'
             f'<h1>{question}</h1><div class="answer-cue">UTC offset?</div></main>'
             f'{{{{/{gate}}}}}')
    back = (f'{{{{#{gate}}}}}<main class="tza"><div class="mast">TIME ZONE ATLAS</div>'
            f'<h1>{question}</h1><div class="answer">{answer}</div>'
            f'<p class="zone">{zone}</p><p class="region">{{{{Region}}}}</p>'
            '<div class="map"><img src="{{Map}}" alt="{{MapAlt}}"></div>'
            '<p class="legend">{{MapLegend}}</p>'
            '{{#Note}}<p class="note">{{Note}}</p>{{/Note}}'
            '<p class="source"><a href="{{Source}}">Time-zone source</a> · '
            '<a href="https://github.com/evansiroky/timezone-boundary-builder/releases/tag/2026d">'
            'Boundary source</a> · OpenStreetMap / ODbL 1.0</p>'
            f'</main>{{{{/{gate}}}}}')
    return {"name": gate, "qfmt": front, "afmt": back}


def atlas_decks() -> tuple[list, list[str]]:
    items = json.loads(MANIFEST.read_text())
    keys = [item["key"] for item in items]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate atlas keys")
    for item in items:
        if bool(item.get("code")) != bool(item.get("code_expansion")):
            raise ValueError(f"incomplete abbreviation: {item['key']}")
        if bool(item.get("second_code")) != bool(item.get("second_code_expansion")):
            raise ValueError(f"incomplete daylight abbreviation: {item['key']}")
        if item.get("second_code") and not item.get("second_offset"):
            raise ValueError(f"abbreviation without offset: {item['key']}")
    codes = [(item[field], item["key"]) for item in items for field in ("code", "second_code")
             if item.get(field)]
    if len({code for code, _ in codes}) != len(codes):
        raise ValueError("abbreviation collision in atlas")
    forbidden = {code for code, _ in codes} & AMBIGUOUS_BARE_CODES
    if forbidden:
        raise ValueError(f"bare code ambiguous within this roster: {sorted(forbidden)}")
    with zipfile.ZipFile(BOUNDARIES) as archive:
        features = json.loads(archive.read("combined.json"))["features"]
    zones = [(feature["properties"]["tzid"], shape(feature["geometry"])) for feature in features]
    land_data = json.loads(LAND.read_text())
    land = [shape(feature["geometry"]) for feature in land_data["land"]["features"]]
    MEDIA.mkdir(parents=True, exist_ok=True)
    fields = ["Key", "Place", "Region", "Zone", "SecondZone", "Offset", "SecondOffset", "Code",
              "SecondCode", "CodeExpansion", "SecondCodeExpansion", "Question",
              "SecondQuestion", "Map", "MapAlt", "MapLegend", "Note", "Source"]
    model = genanki.Model(
        MODEL_ID, MODEL_NAME, fields=[{"name": field} for field in fields],
        templates=[
            template("{{Question}}", "{{Offset}}", "{{Zone}}", "Offset"),
            template("{{SecondQuestion}}", "{{SecondOffset}}", "{{SecondZone}}", "SecondOffset"),
            template("What UTC offset does {{Code}} mean?", "{{Offset}}", "{{Code}} · {{CodeExpansion}}", "Code"),
            template("What UTC offset does {{SecondCode}} mean?",
                     "{{SecondOffset}}", "{{SecondCode}} · {{SecondCodeExpansion}}", "SecondCode"),
        ],
        css=(ROOT / "anki/time-zone-atlas/card.css").read_text(), sort_field_index=0,
    )
    decks = {name: genanki.Deck(DECK_IDS[name], f"{DECK_ROOT}::{name}")
             for name in CONTINENTS}
    media = []
    for item in items:
        filename = f"_time_zone_atlas_{item['key']}.svg"
        path = MEDIA / filename
        path.write_text(map_svg(item, zones, land))
        media.append(str(path))
        condition = item.get("condition")
        if condition:
            question = f"In {item['place']}, what is the UTC offset for {condition}?"
        elif item.get("second_offset"):
            question = f"What is {item['place']}'s UTC offset during standard time?"
        else:
            question = f"What is {item['place']}'s UTC offset?"
        second_question = (f"What is {item['place']}'s UTC offset during daylight time?"
                           if item.get("second_offset") else "")
        source = SOURCES.get(item["key"], "https://www.iana.org/time-zones/releases/2026d")
        if item.get("special"):
            map_legend = "Dashed area: approximate local time practice. Dot: Ürümqi."
            map_alt = "Map of Asia with Ürümqi marked and an approximate Xinjiang Time practice area"
        elif item.get("brazil"):
            map_legend = ("Highlighted areas: Brazilian regions at this UTC offset "
                          "on 25 September 2026. Dot: place.")
            map_alt = (f"South America map highlighting Brazilian areas at {item['offset']} "
                       f"on 25 September 2026, with {item['place']} marked")
        elif item["key"] in {"lord-howe", "noronha", "singapore"}:
            map_legend = "Continental context; inset enlarges the time area. Dot: place."
            map_alt = f"Wide-area map with {item['place']} marked and an enlarged time-area inset"
        elif item["key"] == "taipei":
            map_legend = "Continental context; inset enlarges Taiwan's time area. Dot: Taipei."
            map_alt = "East Asia map with Taipei marked and an enlarged Taiwan time-area inset"
        else:
            map_legend = "Highlighted area: selected civil-time area. Dot: place."
            map_alt = f"Continental map highlighting {item['place']}'s civil-time area"
        note_text = item.get("note", "")
        if item.get("second_offset") and not note_text:
            note_text = (f"Standard time: {item['offset']}. "
                         f"Daylight time: {item['second_offset']}.")
        values = [item["key"], item["place"], item["region"], item["zone"],
                  item.get("second_zone", ""), item["offset"],
                  item.get("second_offset", ""), item.get("code", ""),
                  item.get("second_code", ""), item.get("code_expansion", ""),
                  item.get("second_code_expansion", ""), question, second_question,
                  filename, map_alt, map_legend, note_text, source]
        tags = ["ai-created", "geo-time-zone::qa", "geo-time-zone::continent::" +
                item["continent"].lower().replace(" ", "-")]
        if item.get("second_offset"):
            tags.append("geo-time-zone::seasonal")
        if ":" in item["offset"] or ":" in item.get("second_offset", ""):
            tags.append("geo-time-zone::fractional")
        note = genanki.Note(model=model, fields=values, tags=tags,
                            guid=genanki.guid_for("time-zone-atlas-qa-v1", item["key"]))
        decks[item["continent"]].add_note(note)
    return list(decks.values()), media


def build(output: Path = OUTPUT) -> Path:
    decks, media = atlas_decks()
    output.parent.mkdir(parents=True, exist_ok=True)
    package = genanki.Package(decks)
    package.media_files = media
    package.write_to_file(output)
    print(f"wrote {output}: {sum(len(d.notes) for d in decks)} notes, {len(media)} maps")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    build(parser.parse_args().output)
