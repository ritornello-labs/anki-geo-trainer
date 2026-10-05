"""Markdown descriptions for GeoTrainer's public tree; never edits card content."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI = "https://en.wikipedia.org/wiki/"
FOOTER = "\n\n[All Ritornello decks and add-ons](https://ritornello.dev/) · [Support](https://ritornello.dev/support)"
COUNTRIES = {
    "United States": ("States of the United States", "U.S._state"),
    "Brazil": ("States and Federal District of Brazil", "Federative_units_of_Brazil"),
    "India": ("States and union territories of India", "States_and_union_territories_of_India"),
    "Russia": ("Federal subjects of Russia", "Federal_subjects_of_Russia"),
    "China": ("Administrative divisions of China", "Administrative_divisions_of_China"),
    "Canada": ("Provinces and territories of Canada", "Provinces_and_territories_of_Canada"),
    "Australia": ("States and territories of Australia", "States_and_territories_of_Australia"),
    "Argentina": ("Provinces of Argentina", "Provinces_of_Argentina"),
    "Mexico": ("States of Mexico", "States_of_Mexico"),
    "Indonesia": ("Provinces of Indonesia", "Provinces_of_Indonesia"),
}
TOPICS = {
    "Biomes": (
        "Recall biome names, locations, vegetation and climate; use the photographs and distribution maps to connect the terms with landscapes.",
        "Biome",
    ),
    "Mountain Ranges": (
        "Connect mountain-range names and locations with their peaks and geographic setting.",
        "Mountain_range",
    ),
    "Deserts": (
        "Connect desert names and locations with aridity and their geographic setting.",
        "Desert",
    ),
    "Plateaus, Highlands & Basins": (
        "Recall names and locations of plateaus, highlands and basins, then connect them with their characteristic landforms.",
        "Plateau",
    ),
    "Plateaus & Basins": (
        "Learn the shapes and positions of selected plateaus and basins.",
        "Plateau",
    ),
    "Plains, Grasslands & Steppes": (
        "Recall names and locations of plains, grasslands and steppes, with their landscape and vegetation concepts.",
        "Grassland",
    ),
    "Plains & Grasslands": (
        "Learn the shapes and positions of selected plains and grasslands.",
        "Grassland",
    ),
    "Peninsulas": (
        "Recall peninsula names, locations and their geographic connections.",
        "Peninsula",
    ),
    "Straits, Canals & Isthmuses": (
        "Recall the waterways and land bridges that connect or separate larger regions.",
        "Strait",
    ),
    "Capes": (
        "Recall cape names and locations, then connect them with their coastal setting.",
        "Cape_(geography)",
    ),
    "Major Plates": (
        "Recall the major tectonic plates, their locations and what they carry.",
        "List_of_tectonic_plates",
    ),
    "Minor Plates": (
        "Learn the locations of minor tectonic plates and their relationships to surrounding plates.",
        "List_of_tectonic_plates",
    ),
    "Plate Boundary Types": (
        "Distinguish convergent, divergent and transform boundaries by their motion and characteristic effects.",
        "Plate_tectonics#Plate_boundaries",
    ),
    "Named Plate Boundaries": (
        "Recall named plate boundaries, the plates they separate and their boundary types.",
        "Plate_tectonics#Plate_boundaries",
    ),
    "Plate Boundaries": (
        "Trace selected named plate boundaries on a map and compare their positions with the answer.",
        "Plate_tectonics#Plate_boundaries",
    ),
    "Tectonic Plates": (
        "Connect tectonic plate shapes and positions with plate motion and boundaries.",
        "Plate_tectonics",
    ),
    "Regions & Groupings": (
        "Recall regional names, locations and members; use the explanatory answers for groupings with flexible or disputed boundaries.",
        "Region",
    ),
    "Country Blocs & Organizations": (
        "Recall organization names, acronyms, purposes, founding dates and membership facts where supplied. Memberships can change; consult the linked references.",
        "International_organization",
    ),
    "Bloc Membership Drill": (
        "Click the countries belonging to the requested organization or grouping. Zoom and pan to reach small countries, then reveal selected and missed members.",
        "International_organization",
    ),
    "Islands & Archipelagos": (
        "Connect island and archipelago names with their locations and surrounding waters.",
        "Archipelago",
    ),
    "Lakes": (
        "Learn the positions of selected lakes and recognize them from their outlines.",
        "Lake",
    ),
    "Rivers": (
        "Trace a named river on a blank map. Zoom and pan as needed, then reveal the answer to compare its route with your line.",
        "River",
    ),
}


def link(label, article):
    return f"[{label}]({WIKI}{article})"


def description_for(name: str) -> str:
    if not name.startswith("GeoTrainer"):
        raise ValueError(f"Outside public GeoTrainer tree: {name}")
    path = name.split("::")
    leaf = path[-1]
    refs = []
    body = ""
    how = ""
    if name == "GeoTrainer":
        title = "GeoTrainer — Full Edition"
        body = "Map games and geography concepts in one collection: world countries, ten country-subdivision packs, physical geography, plate tectonics, islands and archipelagos, reference lines and time."
        how = "Start with one subject or task subdeck, then add others as useful. Current focused components share the same notes as this full edition. Games provide feedback; you choose Anki’s grade yourself."
        refs = [
            link("Geography", "Geography"),
            link("Köppen climate classification", "K%C3%B6ppen_climate_classification"),
        ]
    else:
        title = " — ".join(path[1:])
        if "Köppen" in path:
            body = "Learn the Köppen–Geiger climate codes and the temperature and precipitation patterns they describe."
            if leaf == "Letter System":
                body += " These cards isolate the meanings of the letters; their interpretation depends on the climate group and position in the code."
            elif leaf == "Climate Classes":
                body += " These cards connect selected class/group codes with their names, criteria, examples and distribution maps. The maps represent the 1991–2020 classification."
            how = "Learn the group letters first, then retrieve the more specific codes. Read the answer explanations before grading; classification is based on climate patterns rather than a country label."
            refs = [
                link("Classification and code guide", "K%C3%B6ppen_climate_classification"),
                link("Af — tropical rainforest", "Tropical_rainforest_climate"),
                link("Am — tropical monsoon", "Tropical_monsoon_climate"),
                link("Aw/As — tropical savanna", "Tropical_savanna_climate"),
                link("BWh/BWk — desert", "Desert_climate"),
                link("Cfa — humid subtropical", "Humid_subtropical_climate"),
                link("Cfb — oceanic", "Oceanic_climate"),
            ]
        elif "Reference Lines & Time" in path:
            if leaf.startswith("01 "):
                body = "Learn latitude, longitude and the reference lines used to describe a position on Earth."
                refs = [link("Geographic coordinates", "Geographic_coordinate_system")]
            elif leaf.startswith("02 "):
                body = "Connect Earth’s axial tilt with the tropics, polar circles, overhead Sun and polar day/night. Rotate the globe to place the requested line, then reveal its latitude."
                refs = [
                    link("Tropic of Cancer", "Tropic_of_Cancer"),
                    link("Polar circles", "Polar_circle"),
                ]
            elif leaf.startswith("03 "):
                body = "Reason about the calendar date when crossing the International Date Line. Distinguish the real date boundary from the straight 180-degree meridian."
                refs = [link("International Date Line", "International_Date_Line")]
            elif leaf.startswith("04 "):
                body = "Practice UTC foundations and randomized conversions between UTC and UTC−3, including previous-day and next-day results."
                refs = [link("Coordinated Universal Time", "Coordinated_Universal_Time")]
            elif "05 Time Zone Atlas" in path:
                body = "Recall a place’s UTC offset, then reveal its zone name and map. Standard/daylight conditions are stated where applicable; selected abbreviations have their own cards."
                refs = [link("Time zones", "Time_zone")]
            else:
                body = "Place reference lines on a globe, understand their geometry, reason about calendar dates and build a time-zone atlas."
                refs = [
                    link("Geographic coordinates", "Geographic_coordinate_system"),
                    link("International Date Line", "International_Date_Line"),
                    link("Time zones", "Time_zone"),
                ]
            how = "Retrieve the answer before revealing it. For conversions include both the hour and the date relationship; for atlas cards respect the stated seasonal condition."
        elif "Concepts" in path:
            topic = TOPICS.get(leaf)
            if topic:
                body, article = topic
                refs = [link(leaf, article)]
            else:
                body = "Focused recall cards connect names and map locations with the concepts behind this subject."
                refs = [link("Geography", "Geography")]
            how = "Try to retrieve the requested fact before revealing the answer. Use the linked article to understand unfamiliar terms, then choose Anki’s grade according to your recall."
        else:
            country = next((x for x in path if x in COUNTRIES), None)
            if country:
                label, article = COUNTRIES[country]
                subject = f"the subdivisions of {country}"
                refs = [link(label, article)]
                if country == "Indonesia":
                    subject += " using the accepted 38-province map"
            elif path[1] == "World Countries":
                subject = (
                    "world countries"
                    if len(path) == 2
                    else (
                        "continent silhouettes"
                        if "Continents" in path
                        else f"the countries of {path[2]}"
                    )
                )
                refs = [link("Sovereign states", "List_of_sovereign_states")]
            elif path[1] == "Plate Tectonics":
                subject = "tectonic plates and their boundaries"
                refs = [link("Plate tectonics", "Plate_tectonics")]
            elif path[1] == "Islands & Archipelagos":
                subject = "islands and archipelagos"
                refs = [link("Archipelagos", "Archipelago")]
            elif path[1] == "World":
                subject = "country subdivisions grouped by continent"
                refs = [link("Administrative divisions", "Administrative_division")]
            else:
                topic = next((TOPICS[x] for x in reversed(path) if x in TOPICS), None)
                subject = next(
                    (x.lower() for x in reversed(path[1:]) if x in TOPICS), "physical geography"
                )
                refs = [link("Background", topic[1] if topic else "Physical_geography")]
            if leaf.startswith("1 Which"):
                body = f"Identify {subject} from a dot or highlighted target on a map without internal borders. Reveal the answer to see the name and outline."
                how = "Name the target before revealing it. The random point stays consistent between the question and answer of a review."
            elif leaf == "2 Place":
                body = (
                    f"Place the supplied silhouettes of {subject} where they belong on a blank map."
                )
                how = "Drag the shape into position, then reveal the answer to compare your placement with the real location and distance feedback."
            elif leaf == "3 Sketch":
                body = f"Sketch {subject} in geographic context on a blank parent map."
                how = "Draw the outline where it belongs; shape, scale and position matter. Reveal the answer to compare your sketch with the target."
            elif leaf == "4 Draw":
                body = f"Draw the outlines of {subject} from memory on a blank canvas."
                how = "Recall the shape without a map or aspect-ratio hint. Reveal the answer to compare the outlines; grading normalizes drawing scale and position."
            elif leaf == "1 Trace":
                body = f"Trace {subject} on a blank map."
                how = "Zoom and pan as needed, draw the route, then reveal the answer to compare it with the target."
            elif leaf == "1 Globe Placement":
                body = "Place the extent of a named island or archipelago on a randomly oriented globe."
                how = "Rotate the globe and draw a movable, resizable ellipse around the target. Reveal the answer to compare coverage, centre and footprint."
            else:
                body = f"Learn {subject} through map games and focused recall."
                how = "Choose a task or concept subdeck to focus on one skill. Required map media and game code are bundled; linked Wikipedia articles need an internet connection."
            how += " Games may suggest a grade; you choose Anki’s answer grade yourself."
    return (
        f"# {title}\n\n{body}\n\n**How to study:** {how}\n\n**Read more:** "
        + " · ".join(refs)
        + FOOTER
    )
