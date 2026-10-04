#!/usr/bin/env python3
"""Build one APKG per concept family (v2 architecture).

v1 shipped a single deck built on one `GeoConcept` note type shared by every
topic, so almost every note produced only the generic locator pair. v2 gives
each family its own note type, its own concept cards, and its own APKG, so a
family can be reviewed, fixed and imported independently.

Inputs:
  families/data/<family>.json      concept list extracted from the seed CSVs
  families/research/<family>.json  Wikipedia-verified topic fields
  out/anki_export/media/           map assets (shared with the v1 pipeline)

Output:
  out/families/<family>.apkg
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import sys
from pathlib import Path

import genanki

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from families.spec import BASE_FIELDS, FAMILIES, KOPPEN, KOPPEN_LETTERS, ConceptCard, Family

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "families" / "data"
RESEARCH_DIR = ROOT / "families" / "research"
MEDIA_DIR = ROOT / "out" / "anki_export" / "media"
#: Köppen distribution maps are 27 MB SVGs upstream; the v1 raster build already
#: rendered them to PNGs with the answer-leaking legend cropped off, so reuse those.
RASTER_MEDIA_DIR = ROOT / "out" / "apkg_build" / "staged-media-raster"
#: Committed map art, and the source of truth. It used to be checked LAST, on
#: the reasoning that a rebuilt v1 export should win -- but the v1 export step
#: is retired, so `out/anki_export/media` is now a stale staging directory that
#: was quietly shadowing 43 corrected files: every regenerated tectonic plate
#: map, every hand-traced areal polygon, and all 14 biome maps. The audit
#: passed throughout, because it reads the repo copies directly and never asked
#: which one the build actually ships.
REPO_MEDIA_DIRS = (
    ROOT / "media",
    ROOT / "media" / "locator" / "geoconcept",
    ROOT / "media" / "blank" / "geoconcept",
    ROOT / "media" / "photos" / "geoconcept",
    ROOT / "media" / "distribution" / "geoconcept",
)
OUT_DIR = ROOT / "out" / "families"
#: Image fields whose file is named after the concept and generated, not
#: researched: the range with its summit marked, the world map of one
#: boundary type. A missing file leaves the field empty and the card intact.
DERIVED_MEDIA = {
    "peak_map": "{slug}-peak.svg",
    "type_map": "boundary-type-{slug}.png",
}


def resolve_media(filename: str) -> Path | None:
    for directory in (*REPO_MEDIA_DIRS, MEDIA_DIR, RASTER_MEDIA_DIR):
        candidate = directory / filename
        if candidate.exists():
            return candidate
    return None

DEFAULT_DECK_ROOT = "World Geography Concepts"
DECK_ROOT = DEFAULT_DECK_ROOT


def stable_id(*parts: str) -> int:
    digest = hashlib.sha1("::".join(parts).encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") & 0x7FFFFFFF


def base_css(accent: str) -> str:
    """House card style, tinted per family so decks are distinguishable."""
    return f"""
.card {{
  font-family: "Arial", sans-serif;
  font-size: 18px;
  line-height: 1.45;
  color: #1d1d1d;
  background: #f7f4ea;
}}
.card-shell {{ max-width: 960px; margin: 0 auto; padding: 20px 24px 28px; }}
.card-type {{
  font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase;
  color: {accent}; margin-bottom: 10px; font-weight: 700;
}}
.concept-name, .answer-title {{ font-size: 30px; font-weight: 700; margin: 0 0 6px; }}
.aliases, .subtitle {{ color: #666; font-size: 15px; }}
.question {{ margin-top: 14px; font-size: 20px; }}
.map-wrap {{ margin: 16px 0 10px; }}
.media-large {{
  display: block; width: 100%; max-width: 100%; margin: 0 auto;
  border: 1px solid #d8d0bf; border-radius: 10px; background: #ffffff;
}}
.answer-block {{
  margin-top: 16px; padding: 14px 16px; background: #fffdf7;
  border: 1px solid #e5dcc9; border-left: 4px solid {accent}; border-radius: 10px;
}}
.answer-block h3 {{
  margin: 0 0 8px; font-size: 14px; text-transform: uppercase;
  letter-spacing: 0.04em; color: {accent};
}}
.answer-value {{ font-size: 22px; font-weight: 600; }}
.detail {{ margin-top: 8px; color: #6a6a6a; font-size: 14px; font-weight: 400; line-height: 1.45; }}
.stacked-list {{ white-space: pre-wrap; }}

.gallery {{ margin-top: 16px; }}
/* Capped, or a portrait photo pushes the distribution map a whole screen
   down on a phone. Crop rather than letterbox so the strip stays even. */
.ph-hero {{
  display: block; width: 100%; max-height: 42vh; object-fit: cover;
  border-radius: 10px; border: 1px solid #d8d0bf; background: #fff;
}}
.ph-strip {{ display: flex; gap: 8px; margin-top: 8px; }}
/* Equal-width thumbnails that crop rather than letterbox, so a portrait and
   a landscape photo sit in the same row without a ragged strip. */
.ph-thumb {{
  flex: 1 1 0; min-width: 0; height: 64px; object-fit: cover; cursor: pointer;
  border-radius: 6px; border: 2px solid transparent; opacity: 0.72;
}}
.ph-thumb.is-on {{ border-color: {accent}; opacity: 1; }}
.ph-credit {{ margin-top: 8px; color: #8a857a; font-size: 12px; line-height: 1.4; }}
.ph-credit a {{ color: #8a857a; }}
.ph-preload {{ display: none; }}
.nightMode .ph-hero {{ border-color: #3a3b40; background: #26272b; }}
.nightMode .ph-credit, .nightMode .ph-credit a {{ color: #8f8b81; }}
.note-block {{ margin-top: 14px; color: #4a4a4a; font-size: 16px; }}
.divider {{ height: 1px; background: #e6dece; margin: 18px 0; }}
.wiki-link {{ display: inline-block; margin-top: 8px; font-size: 14px; color: #245f8b; text-decoration: none; }}

.card.nightMode, .nightMode .card {{ color: #e6e3dc; background: #1f2023; }}
.nightMode .card-type, .nightMode .answer-block h3 {{ color: #d8c48a; }}
.nightMode .concept-name, .nightMode .answer-title {{ color: #f2efe8; }}
.nightMode .aliases, .nightMode .subtitle {{ color: #9c988d; }}
.nightMode .note-block {{ color: #c9c5bb; }}
.nightMode .detail {{ color: #a8a49a; }}
.nightMode .answer-block {{ background: #26272b; border-color: #3a3b40; border-left-color: {accent}; }}
.nightMode .media-large {{ border-color: #3a3b40; }}
.nightMode .divider {{ background: #3a3b40; }}
.nightMode .wiki-link {{ color: #6fb2e6; }}
"""


def wiki_tail() -> str:
    return """
  {{#wikipedia_url}}
  <hr class="divider">
  <iframe src="{{wikipedia_url}}" style="height: 60vh; width: 100%;" seamless="seamless"></iframe>
  <a class="wiki-link" href="{{wikipedia_url}}">Open full page</a>
  {{/wikipedia_url}}
"""


def subtitle_html(family: Family) -> str:
    """The family's subtitle field, for answer sides only.

    It never goes on the `1 Locate` front: for a chokepoint the subtitle is
    "Egypt" and for a named boundary it is "Levant", which is the answer to
    "where is this?".
    """
    if not family.subtitle_field:
        return ""
    field = family.subtitle_field
    return (
        f"{{{{#{field}}}}}"
        f'<div class="subtitle">{{{{{field}}}}}</div>'
        f"{{{{/{field}}}}}\n  "
    )


def name_card(family: Family) -> dict:
    """Shaded map -> name. Recognition, the rung below GeoTrainer's Which."""
    guard = family.name_card_require
    open_g = f"{{{{#{guard}}}}}" if guard else ""
    close_g = f"{{{{/{guard}}}}}" if guard else ""
    chip = f"Name this {family.noun}" if family.noun else "Name This"
    front = f"""{open_g}<div class="card-shell">
  <div class="card-type">{chip}</div>
  <div class="map-wrap">{{{{locator_map}}}}</div>
</div>{close_g}"""
    back = f"""<div class="card-shell">
  <div class="card-type">{chip}</div>
  <div class="answer-title">{{{{name}}}}</div>
  {subtitle_html(family)}{{{{#alt_names}}}}<div class="aliases">{{{{alt_names}}}}</div>{{{{/alt_names}}}}
  <div class="map-wrap">{{{{locator_map}}}}</div>
  {{{{#definition}}}}<div class="note-block">{{{{definition}}}}</div>{{{{/definition}}}}
{wiki_tail()}</div>"""
    return {"name": "0 Name", "qfmt": front, "afmt": back}


def locate_card(family: Family) -> dict:
    """Name -> position on the world map. Self-graded position recall."""
    front = """<div class="card-shell">
  <div class="card-type">Locate</div>
  <div class="concept-name">{{name}}</div>
  <div class="map-wrap">{{blank_map}}</div>
</div>"""
    back = f"""<div class="card-shell">
  <div class="card-type">Locate</div>
  <div class="answer-title">{{{{name}}}}</div>
  {subtitle_html(family)}<div class="map-wrap">{{{{locator_map}}}}</div>
  {{{{#definition}}}}<div class="note-block">{{{{definition}}}}</div>{{{{/definition}}}}
{wiki_tail()}</div>"""
    return {"name": "1 Locate", "qfmt": front, "afmt": back}


def gallery_html(card: ConceptCard) -> str:
    """A hero image with a thumbnail strip, on the answer side.

    The field supplies only markup -- one `.ph-hero`, then `.ph-thumb`s
    carrying the full-size filename and credit as data attributes. The swap
    lives here in the template.

    Deliberately back-side only: nothing has to survive the front-to-back
    handoff, which is where in-card state breaks across Anki's clients. And if
    the script never runs, the thumbnails are still four visible photographs,
    so the card degrades to something useful rather than to nothing.
    """
    if not card.gallery_field:
        return ""
    field = card.gallery_field
    return f"""
  {{{{#{field}}}}}<div class="gallery">{{{{{field}}}}}</div>
  <script>
  (function () {{
    // querySelector, not document.currentScript: Anki injects a card's HTML
    // and then evaluates its scripts separately, so currentScript is null by
    // the time this runs. There is one gallery per card.
    var root = document.querySelector(".gallery");
    if (!root) return;
    var hero = root.querySelector(".ph-hero");
    var credit = root.querySelector(".ph-credit");
    root.addEventListener("click", function (event) {{
      var thumb = event.target.closest(".ph-thumb");
      if (!thumb || !hero) return;
      hero.src = thumb.getAttribute("data-full");
      if (credit) credit.innerHTML = thumb.getAttribute("data-credit");
      root.querySelectorAll(".ph-thumb").forEach(function (other) {{
        other.classList.toggle("is-on", other === thumb);
      }});
    }});
  }})();
  </script>{{{{/{field}}}}}"""


def concept_card(family: Family, card: ConceptCard) -> dict:
    """A topic-specific card: prompt about the concept -> the answer field."""
    guards_open = "".join(f"{{{{#{f}}}}}" for f in card.required_fields())
    guards_close = "".join(f"{{{{/{f}}}}}" for f in reversed(card.required_fields()))

    if card.answer == "name":
        # Reverse direction: show the topic facts, recall the concept's name.
        # Show exactly the fields the card is keyed on when `require` names
        # them, so the prompt stays tight; otherwise fall back to the family's
        # fields minus bookkeeping ones.
        shown = [f for f in card.require if f in family.fields] or [
            f for f in family.fields
            if f not in {"term_origin", "fuzzy", "fixed_membership"}
        ]
        facts = "\n".join(
            f'  {{{{#{f}}}}}<div class="answer-block"><h3>{f.replace("_", " ").title()}</h3>'
            f'<div class="stacked-list">{{{{{f}}}}}</div></div>{{{{/{f}}}}}'
            for f in shown
        )
        front = f"""{guards_open}<div class="card-shell">
  <div class="card-type">{card.chip}</div>
  <div class="question">{card.prompt}</div>
{facts}
</div>{guards_close}"""
        back = f"""<div class="card-shell">
  <div class="card-type">{card.chip}</div>
  <div class="answer-title">{{{{name}}}}</div>
  <div class="map-wrap">{{{{locator_map}}}}</div>
  {{{{#definition}}}}<div class="note-block">{{{{definition}}}}</div>{{{{/definition}}}}
{wiki_tail()}</div>"""
        return {"name": card.name, "qfmt": front, "afmt": back}

    # A muted line under the answer: the caveat that makes it trustworthy
    # (which member acceded when, which treaty founded it), not a second recall
    # target. Guarded, so notes without one lose nothing.
    detail = ""
    if card.detail:
        detail = (
            f"\n    {{{{#{card.detail}}}}}"
            f'<div class="detail">{{{{{card.detail}}}}}</div>'
            f"{{{{/{card.detail}}}}}"
        )

    front = f"""{guards_open}<div class="card-shell">
  <div class="card-type">{card.chip}</div>
  <div class="concept-name">{{{{name}}}}</div>
  <div class="question">{card.prompt}</div>
</div>{guards_close}"""
    back = f"""<div class="card-shell">
  <div class="card-type">{card.chip}</div>
  <div class="answer-title">{{{{name}}}}</div>
  {{{{#alt_names}}}}<div class="aliases">{{{{alt_names}}}}</div>{{{{/alt_names}}}}
  <div class="answer-block">
    <div class="answer-value stacked-list">{{{{{card.answer}}}}}</div>{detail}
  </div>{gallery_html(card)}
  <div class="map-wrap">{{{{{card.image_field or "locator_map"}}}}}</div>
{wiki_tail()}</div>"""
    return {"name": card.name, "qfmt": front, "afmt": back}


def build_model(family: Family) -> genanki.Model:
    fields = list(BASE_FIELDS) + [f for f in family.fields if f not in BASE_FIELDS]
    if family.key == "regions-groupings":
        fields.append("fixed_membership")
    templates: list[dict] = []
    if family.has_maps:
        templates.append(name_card(family))
        if family.has_locate:
            templates.append(locate_card(family))
    templates += [concept_card(family, c) for c in family.concept_cards]
    return genanki.Model(
        model_id=stable_id("model-v2", family.model),
        name=family.model,
        fields=[{"name": f} for f in fields],
        templates=templates,
        css=base_css(family.accent),
        sort_field_index=fields.index("name"),
    )


def as_text(value) -> str:
    """Lists render one per line; the stacked-list CSS preserves the breaks."""
    if isinstance(value, list):
        return "\n".join(str(v) for v in value)
    if isinstance(value, bool):
        return "yes" if value else ""
    return "" if value is None else str(value)


def media_html(filename: str, alt: str) -> str:
    if not filename:
        return ""
    return f'<img class="media-large" src="{html.escape(filename)}" alt="{html.escape(alt)}" />'


def photo_gallery(entries: list[dict], media_files: set[str]) -> str:
    """Markup for one note's gallery: hero, thumbnail strip, credit line.

    The credit is not decoration. Most of these are CC BY or CC BY-SA, which
    require attribution wherever the image is shown, so every thumbnail
    carries its own and the swap script moves it with the hero.
    """
    if not entries:
        return ""
    for entry in entries:
        for key in ("file", "thumb"):
            resolved = resolve_media(entry[key])
            if resolved is None:
                raise SystemExit(f"gallery image missing from media dirs: {entry[key]}")
            media_files.add(str(resolved))

    def credit(entry: dict) -> str:
        return (f'{html.escape(entry["author"])} &middot; '
                f'<a href="{html.escape(entry["license_url"])}">'
                f'{html.escape(entry["license"])}</a> &middot; '
                f'<a href="{html.escape(entry["description_url"])}">Wikimedia Commons</a>')

    first = entries[0]
    thumbs = "".join(
        f'<img class="ph-thumb{" is-on" if i == 0 else ""}" '
        f'src="{html.escape(e["thumb"])}" alt="{html.escape(e["caption"])}" '
        f'data-full="{html.escape(e["file"])}" '
        f'data-credit="{html.escape(credit(e))}" />'
        for i, e in enumerate(entries)
    )
    # The other three full-size images are named only in `data-full`, and
    # Anki's media check looks for `src=`. Without this they count as unused,
    # so Check Media offers to delete exactly the files the gallery swaps in.
    # Hidden, but a real reference -- and it warms them for an instant swap.
    preload = "".join(f'<img src="{html.escape(e["file"])}" alt="" />' for e in entries[1:])
    return (
        f'<img class="ph-hero" src="{html.escape(first["file"])}" '
        f'alt="{html.escape(first["caption"])}" />'
        f'<div class="ph-strip">{thumbs}</div>'
        f'<div class="ph-credit">{credit(first)}</div>'
        f'<div class="ph-preload" aria-hidden="true">{preload}</div>'
    )


def build_family(family: Family, media_files: set[str]) -> tuple[genanki.Deck, int] | None:
    data_path = DATA_DIR / f"{family.key}.json"
    research_path = RESEARCH_DIR / f"{family.key}.json"
    if not data_path.exists():
        print(f"  ! {family.key}: no data file, skipped")
        return None
    data = json.loads(data_path.read_text(encoding="utf-8"))
    research = (
        json.loads(research_path.read_text(encoding="utf-8")) if research_path.exists() else {}
    )
    if not research:
        print(f"  ! {family.key}: no research file, concept cards will be empty")

    gallery_field = next((c.gallery_field for c in family.concept_cards if c.gallery_field), "")
    gallery_path = RESEARCH_DIR / family.extra.get("gallery", "")
    galleries: dict[str, list[dict]] = (
        json.loads(gallery_path.read_text(encoding="utf-8"))
        if gallery_field and family.extra.get("gallery") and gallery_path.exists()
        else {}
    )
    if gallery_field and not galleries:
        print(f"  ! {family.key}: no photo manifest, galleries will be empty")

    model = build_model(family)
    deck_name = f"{DECK_ROOT}::{family.deck_path}"
    deck = genanki.Deck(stable_id("deck-v2", deck_name), deck_name)

    field_names = [f["name"] for f in model.fields]
    count = 0
    for concept in data["concepts"]:
        slug = concept["slug"]
        extra = research.get(slug, {})
        values = {
            "slug": slug,
            "name": concept["name"],
            "alt_names": concept.get("alt_names", ""),
            "definition": concept.get("definition", ""),
            "blank_map": media_html(concept.get("blank_map", ""), "Blank world map"),
            "locator_map": media_html(concept.get("locator_map", ""), f"{concept['name']} map"),
            "wikipedia_url": concept.get("wikipedia_url", ""),
            "wikidata_id": concept.get("wikidata_id", ""),
        }
        if gallery_field:
            values[gallery_field] = photo_gallery(galleries.get(slug, []), media_files)
        for name, pattern in DERIVED_MEDIA.items():
            if name in field_names:
                filename = pattern.format(slug=slug)
                values[name] = media_html(filename, f"{concept['name']} {name.replace('_', ' ')}") \
                    if resolve_media(filename) else ""

        for name in field_names:
            if name in values:
                continue
            if name == "fixed_membership":
                values[name] = "" if extra.get("fuzzy") else "yes"
            else:
                values[name] = as_text(extra.get(name, concept.get(name, "")))

        for filename in (concept.get("blank_map", ""), concept.get("locator_map", "")):
            resolved = resolve_media(filename) if filename else None
            if resolved:
                media_files.add(str(resolved))

        deck.add_note(
            genanki.Note(
                model=model,
                fields=[values[name] for name in field_names],
                guid=genanki.guid_for("v2", family.model, slug),
                tags=[f"geo::{family.key}"],
            )
        )
        count += 1
    return deck, count


def build_koppen() -> list[tuple[genanki.Deck, int, set[str]]]:
    """Köppen: one deck for the classes, one for the letter system."""
    data = json.loads((DATA_DIR / "koppen.json").read_text(encoding="utf-8"))
    research_path = RESEARCH_DIR / "koppen.json"
    research = (
        json.loads(research_path.read_text(encoding="utf-8")) if research_path.exists() else {}
    )
    codes = research.get("codes", {})
    letters = research.get("letters", {})
    results = []
    media_files: set[str] = set()

    # --- classes -----------------------------------------------------------
    fields = ["code", "class_name", "group_code", "group_name", "criteria", "examples",
              "distribution_map", "blank_map", "wikipedia_url"]
    accent = KOPPEN.accent
    model = genanki.Model(
        model_id=stable_id("model-v2", KOPPEN.model),
        name=KOPPEN.model,
        fields=[{"name": f} for f in fields],
        templates=[
            {
                "name": "0 Code to Class",
                "qfmt": '<div class="card-shell"><div class="card-type">Code &rarr; Class</div>'
                        '<div class="concept-name">{{code}}</div></div>',
                "afmt": f'<div class="card-shell"><div class="card-type">Code &rarr; Class</div>'
                        f'<div class="answer-title">{{{{class_name}}}}</div>'
                        f'<div class="subtitle">{{{{group_code}}}} {{{{group_name}}}}</div>'
                        f'{{{{#criteria}}}}<div class="answer-block"><h3>Criteria</h3>'
                        f'<div>{{{{criteria}}}}</div></div>{{{{/criteria}}}}{wiki_tail()}</div>',
            },
            {
                "name": "1 Class to Code",
                "qfmt": '<div class="card-shell"><div class="card-type">Class &rarr; Code</div>'
                        '<div class="concept-name">{{class_name}}</div></div>',
                "afmt": f'<div class="card-shell"><div class="card-type">Class &rarr; Code</div>'
                        f'<div class="answer-title">{{{{code}}}}</div>'
                        f'{{{{#criteria}}}}<div class="answer-block"><h3>Criteria</h3>'
                        f'<div>{{{{criteria}}}}</div></div>{{{{/criteria}}}}{wiki_tail()}</div>',
            },
            {
                "name": "2 Distribution",
                "qfmt": '<div class="card-shell"><div class="card-type">Distribution</div>'
                        '<div class="map-wrap">{{distribution_map}}</div>'
                        '<div class="question">Which Köppen code is this?</div></div>',
                "afmt": f'<div class="card-shell"><div class="card-type">Distribution</div>'
                        f'<div class="answer-title">{{{{code}}}} — {{{{class_name}}}}</div>'
                        f'<div class="map-wrap">{{{{distribution_map}}}}</div>{wiki_tail()}</div>',
            },
            {
                "name": "3 Criteria",
                "qfmt": '{{#criteria}}<div class="card-shell"><div class="card-type">Criteria</div>'
                        '<div class="concept-name">{{code}} — {{class_name}}</div>'
                        '<div class="question">What are its defining criteria?</div></div>{{/criteria}}',
                "afmt": f'<div class="card-shell"><div class="card-type">Criteria</div>'
                        f'<div class="answer-title">{{{{code}}}}</div>'
                        f'<div class="answer-block"><h3>Criteria</h3><div class="answer-value">'
                        f'{{{{criteria}}}}</div></div>{wiki_tail()}</div>',
            },
            {
                "name": "4 Examples",
                "qfmt": '{{#examples}}<div class="card-shell"><div class="card-type">Examples</div>'
                        '<div class="concept-name">{{code}} — {{class_name}}</div>'
                        '<div class="question">Where does it occur?</div>'
                        # A blank world map to point at in your head (Elvis,
                        # 2026-09-29): it gives nothing away and makes the
                        # recall faster than picturing the globe unaided.
                        '<div class="map-wrap">{{blank_map}}</div></div>{{/examples}}',
                "afmt": f'<div class="card-shell"><div class="card-type">Examples</div>'
                        f'<div class="answer-title">{{{{code}}}}</div>'
                        f'<div class="answer-block"><h3>Examples</h3>'
                        f'<div class="answer-value stacked-list">{{{{examples}}}}</div></div>'
                        f'{wiki_tail()}</div>',
            },
        ],
        css=base_css(accent),
        sort_field_index=0,
    )
    deck_name = f"{DECK_ROOT}::{KOPPEN.deck_path}"
    deck = genanki.Deck(stable_id("deck-v2", deck_name), deck_name)
    for concept in data["concepts"]:
        code = concept["code"]
        extra = codes.get(code, {})
        values = {
            "code": code,
            "class_name": concept["name"],
            "group_code": concept.get("group_code", ""),
            "group_name": concept.get("group_name", ""),
            "criteria": as_text(extra.get("criteria", "")),
            "examples": as_text(extra.get("examples", "")),
            "distribution_map": media_html(concept.get("distribution_map", ""), f"{code} distribution"),
            "blank_map": media_html(concept.get("blank_map", ""), "Blank world map"),
            "wikipedia_url": concept.get("wikipedia_url", ""),
        }
        for filename in (concept.get("distribution_map", ""), concept.get("blank_map", "")):
            resolved = resolve_media(filename) if filename else None
            if resolved:
                media_files.add(str(resolved))
        deck.add_note(
            genanki.Note(model=model, fields=[values[f] for f in fields],
                         guid=genanki.guid_for("v2", KOPPEN.model, code),
                         tags=["geo::koppen"])
        )
    results.append((deck, len(data["concepts"]), set(media_files)))

    # --- letter system -----------------------------------------------------
    if letters:
        lfields = ["letter", "position", "position_label", "meaning"]
        lmodel = genanki.Model(
            model_id=stable_id("model-v2", KOPPEN_LETTERS.model),
            name=KOPPEN_LETTERS.model,
            fields=[{"name": f} for f in lfields],
            templates=[
                {
                    "name": "0 Letter to Meaning",
                    "qfmt": '<div class="card-shell"><div class="card-type">Letter &rarr; Meaning</div>'
                            '<div class="concept-name">{{letter}}</div>'
                            '<div class="subtitle">{{position_label}}</div></div>',
                    "afmt": '<div class="card-shell"><div class="card-type">Letter &rarr; Meaning</div>'
                            '<div class="answer-title">{{meaning}}</div>'
                            '<div class="subtitle">{{letter}} — {{position_label}}</div></div>',
                },
                {
                    "name": "1 Meaning to Letter",
                    "qfmt": '<div class="card-shell"><div class="card-type">Meaning &rarr; Letter</div>'
                            '<div class="concept-name">{{meaning}}</div>'
                            '<div class="subtitle">{{position_label}}</div></div>',
                    "afmt": '<div class="card-shell"><div class="card-type">Meaning &rarr; Letter</div>'
                            '<div class="answer-title">{{letter}}</div>'
                            '<div class="subtitle">{{position_label}}</div></div>',
                },
            ],
            css=base_css(KOPPEN_LETTERS.accent),
            sort_field_index=0,
        )
        deck_name = f"{DECK_ROOT}::{KOPPEN_LETTERS.deck_path}"
        ldeck = genanki.Deck(stable_id("deck-v2", deck_name), deck_name)
        labels = {"first": "first letter (main group)",
                  "second": "second letter (precipitation)",
                  "third": "third letter (temperature)"}
        n = 0
        for position, mapping in letters.items():
            for letter, meaning in mapping.items():
                ldeck.add_note(
                    genanki.Note(
                        model=lmodel,
                        fields=[letter, position, labels.get(position, position), meaning],
                        guid=genanki.guid_for("v2", KOPPEN_LETTERS.model, position, letter),
                        tags=["geo::koppen-letters"],
                    )
                )
                n += 1
        results.append((ldeck, n, set()))
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("families", nargs="*", help="family keys to build (default: all)")
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--deck-root", default=DEFAULT_DECK_ROOT,
                        help="parent deck name; live since 2026-09-29: 'Decks::Geography Drills::Geo Concepts'")
    parser.add_argument("--combined", type=Path,
                        help="also write one APKG containing every family deck")
    return parser.parse_args()


def main() -> int:
    global DECK_ROOT
    args = parse_args()
    DECK_ROOT = args.deck_root
    args.out_dir.mkdir(parents=True, exist_ok=True)
    all_decks: list[genanki.Deck] = []
    all_media: set[str] = set()
    wanted = set(args.families)

    summary = []
    for family in FAMILIES:
        if wanted and family.key not in wanted:
            continue
        media: set[str] = set()
        built = build_family(family, media)
        if built is None:
            continue
        deck, count = built
        all_decks.append(deck)
        all_media |= media
        path = args.out_dir / f"{family.key}.apkg"
        genanki.Package([deck], media_files=sorted(media)).write_to_file(path)
        cards = sum(1 for note in deck.notes for _ in note.cards)
        summary.append({"family": family.key, "notes": count, "cards": cards,
                        "media": len(media), "apkg": str(path)})
        print(f"  {family.key:22s} {count:3d} notes  {cards:4d} cards  -> {path.name}")

    if not wanted or "koppen" in wanted:
        for deck, count, media in build_koppen():
            all_decks.append(deck)
            all_media |= media
            key = "koppen" if "Letter" not in deck.name else "koppen-letters"
            path = args.out_dir / f"{key}.apkg"
            genanki.Package([deck], media_files=sorted(media)).write_to_file(path)
            cards = sum(1 for note in deck.notes for _ in note.cards)
            summary.append({"family": key, "notes": count, "cards": cards,
                            "media": len(media), "apkg": str(path)})
            print(f"  {key:22s} {count:3d} notes  {cards:4d} cards  -> {path.name}")

    if args.combined:
        args.combined.parent.mkdir(parents=True, exist_ok=True)
        genanki.Package(all_decks, media_files=sorted(all_media)).write_to_file(args.combined)
        print(f"\ncombined -> {args.combined}")

    report = args.out_dir / "build-report.json"
    report.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"\ntotal: {sum(s['notes'] for s in summary)} notes, "
          f"{sum(s['cards'] for s in summary)} cards across {len(summary)} decks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
