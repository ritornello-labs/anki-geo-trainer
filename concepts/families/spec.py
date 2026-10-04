"""Per-family note-type specifications for the v2 deck architecture.

The v1 deck used one `GeoConcept` note type for every topic, so each note got
the intersection of what all topics need — in practice just a locator pair.
v2 gives each family its own fields and its own concept cards, and ships one
APKG per family.

Card families follow GeoTrainer's naming so these decks can later be folded
into it as extra rungs on the same skill ladder:

    0 Name     shaded map      -> name it        (recognition)
    1 Locate   name            -> shaded map     (position recall, self-graded)
    5 <topic>  topic-specific concept cards      (the semantic layer)

Every family shares the Name/Locate pair; `concept_cards` adds the cards that
only make sense for that topic.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ConceptCard:
    """A topic-specific card template.

    name:      card template name, e.g. "5 Countries"
    chip:      the small uppercase label shown at the top of the card
    prompt:    question rendered under the concept name on the front
    answer:    field whose value is the answer
    require:   fields that must be non-empty for the card to generate
    """

    name: str
    chip: str
    prompt: str
    answer: str
    require: tuple[str, ...] = ()
    #: Optional second field shown as a muted line under the answer: the
    #: caveat that makes the answer trustworthy ("Timor-Leste acceded in
    #: October 2025") rather than a second thing to recall.
    detail: str = ""
    #: Optional field holding a photo gallery (one hero plus a thumbnail
    #: strip), rendered on the answer side under the answer. For cards whose
    #: answer is a description of something you would recognise on sight, a
    #: sentence about "sclerophyll shrubs with small waxy leaves" is worth far
    #: less than four photographs of them.
    gallery_field: str = ""
    #: Optional field holding an image for the answer side, drawn in place of
    #: the family locator map: the range with its summit marked, rather than
    #: the range alone.
    image_field: str = ""

    def required_fields(self) -> tuple[str, ...]:
        return self.require or (self.answer,)


@dataclass(frozen=True)
class Family:
    key: str
    title: str
    #: Anki model name; must be globally unique in the collection.
    model: str
    #: Extra fields beyond the shared base ones.
    fields: tuple[str, ...]
    concept_cards: tuple[ConceptCard, ...]
    #: Accent colour so each family is recognisable at a glance mid-review.
    accent: str
    #: Families whose spatial recall GeoTrainer already owns; we still ship
    #: Name/Locate here so the concept deck stands alone, but this flags the
    #: overlap for the eventual merge.
    geotrainer_overlap: bool = False
    subtitle_field: str = ""
    #: What the `0 Name` front says it is asking for: "Name this strait, canal
    #: or isthmus". Without it the chip read "Name This" over a map, and a
    #: shaded patch inside South Africa invited "South Africa" as the answer
    #: when the card meant the Veld -- the map is where the eyes go, so the
    #: prompt has to say what kind of thing is outlined on it.
    noun: str = ""
    #: Deck path under the review-tree root, e.g. "Köppen::Climate Classes".
    #: Defaults to the title. Elvis grouped the two Köppen decks and the major
    #: and minor plates on 2026-09-23; `scripts/regroup_decks_live.py` moved the
    #: live cards and this keeps builds and pushes aimed at the same decks.
    deck: str = ""
    #: False for families that are not places (e.g. a taxonomy of
    #: boundary types), which get no Name/Locate map cards.
    has_maps: bool = True
    #: False when "find it on a blank map" is not a sensible task even though
    #: the family has a locator map. A bloc's locator IS its membership, so
    #: asking to locate it would just be the Members card with worse grading.
    has_locate: bool = True
    #: Field that must be non-empty for the `0 Name` card to generate. Blocs
    #: use it: 29 pairs of them share more than half their members, so a
    #: shaded map of "27 European countries" does not pick out one answer.
    name_card_require: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def deck_path(self) -> str:
        return self.deck or self.title


BASE_FIELDS = (
    "slug",
    "name",
    "alt_names",
    "definition",
    "blank_map",
    "locator_map",
    "wikipedia_url",
    "wikidata_id",
)


FAMILIES: tuple[Family, ...] = (
    Family(
        key="peninsulas",
        noun="peninsula",
        title="Peninsulas",
        model="Geo Peninsula",
        fields=("countries", "waters"),
        concept_cards=(
            ConceptCard("5 Countries", "Countries", "Which countries are on it?", "countries"),
            ConceptCard("6 Waters", "Waters", "Which waters flank it?", "waters"),
        ),
        accent="#2f6f4f",
    ),
    Family(
        key="chokepoints",
        noun="strait, canal or isthmus",
        title="Straits, Canals & Isthmuses",
        model="Geo Chokepoint",
        fields=("connects", "separates", "location"),
        concept_cards=(
            ConceptCard("5 Connects", "Connects", "What does it connect?", "connects"),
            ConceptCard("6 Separates", "Separates", "What does it separate?", "separates"),
        ),
        accent="#1f6f7a",
        subtitle_field="location",
    ),
    Family(
        key="capes",
        noun="cape",
        title="Capes",
        model="Geo Cape",
        fields=("country", "waters", "significance"),
        concept_cards=(
            ConceptCard("5 Country", "Country", "Which country is it in?", "country"),
            ConceptCard("6 Significance", "Significance", "Why does it matter?", "significance"),
            # Numbered 7 rather than slotted in at 6: renaming a live template
            # would orphan the existing Significance cards and lose their
            # scheduling, and the ordinal is cosmetic.
            ConceptCard("7 Waters", "Waters", "Which waters meet there?", "waters"),
        ),
        accent="#7a4a1f",
    ),
    Family(
        key="mountain-ranges",
        noun="mountain range",
        title="Mountain Ranges",
        model="Geo Mountain Range",
        fields=("highest_peak", "countries", "role", "peak_map"),
        concept_cards=(
            # `peak_map` is the range's own shading with the summit marked, so
            # the answer side shows where the peak sits, not just its name.
            ConceptCard("5 Highest Peak", "Highest Peak", "What is its highest peak?", "highest_peak",
                        image_field="peak_map"),
            ConceptCard("6 Countries", "Countries", "Which countries does it run through?", "countries"),
            ConceptCard("7 Role", "Role", "What is its defining role?", "role"),
        ),
        accent="#5b4a7a",
        geotrainer_overlap=True,
    ),
    Family(
        key="deserts",
        noun="desert",
        title="Deserts",
        model="Geo Desert",
        fields=("desert_type", "countries", "superlative"),
        concept_cards=(
            ConceptCard("5 Type", "Type", "What type of desert is it?", "desert_type"),
            ConceptCard("6 Countries", "Countries", "Which countries does it span?", "countries"),
            ConceptCard("7 Superlative", "Superlative", "What is it notable for?", "superlative"),
        ),
        accent="#96662a",
        geotrainer_overlap=True,
    ),
    Family(
        key="tectonic-plates",
        noun="tectonic plate",
        title="Tectonic Plates",
        deck="Tectonic Plates::Major Plates",
        model="Geo Tectonic Plate",
        # No boundary-type card here on purpose: the boundary fact states the
        # motion ("subducts", "splits from", "grinds past"), so classifying it
        # would test the verb, not the geology. The classification is drilled
        # in `named-boundaries`, where the prompt is a place name instead.
        fields=("plate_kind", "boundary_fact", "carries"),
        concept_cards=(
            ConceptCard("5 Boundary", "Boundary", "What famous boundary interaction involves it?", "boundary_fact"),
            ConceptCard("6 Carries", "Carries", "What does it carry?", "carries"),
            ConceptCard("7 Kind", "Kind", "Major or minor, and what crust?", "plate_kind"),
        ),
        accent="#8a3b3b",
        geotrainer_overlap=True,
    ),
    Family(
        key="plateaus-basins",
        noun="plateau, highland or basin",
        title="Plateaus, Highlands & Basins",
        model="Geo Plateau Basin",
        fields=("countries", "bounded_by", "distinctive"),
        concept_cards=(
            ConceptCard("5 Countries", "Countries", "Which countries is it in?", "countries"),
            ConceptCard("6 Bounded By", "Bounded By", "What bounds or defines it?", "bounded_by"),
            ConceptCard("7 Distinctive", "Distinctive", "What is most distinctive about it?", "distinctive"),
        ),
        accent="#4a6a8a",
    ),
    Family(
        key="plains-grasslands",
        noun="plain, grassland or steppe",
        title="Plains, Grasslands & Steppes",
        model="Geo Grassland",
        fields=("countries", "vegetation", "term_origin"),
        concept_cards=(
            # The reverse card is the point of this family: these are largely
            # regional words for grassland, so "which region's term is this?"
            ConceptCard("5 Region Term", "Which Term", "Which term names this region's grassland?", "name",
                        require=("countries", "vegetation")),
            ConceptCard("6 Countries", "Countries", "Where is it?", "countries"),
            ConceptCard("7 Term Origin", "Term Origin", "Where does the name come from?", "term_origin"),
        ),
        accent="#4f7a2f",
    ),
    Family(
        key="islands-archipelagos",
        noun="island or archipelago",
        title="Islands & Archipelagos",
        model="Geo Archipelago",
        fields=("countries", "waters", "distinctive"),
        concept_cards=(
            ConceptCard("5 Countries", "Countries", "Which countries or territories?", "countries"),
            ConceptCard("6 Waters", "Waters", "Which waters does it lie in?", "waters"),
            ConceptCard("7 Distinctive", "Distinctive", "What is most distinctive about it?", "distinctive"),
        ),
        accent="#1f6f8a",
    ),
    Family(
        key="regions-groupings",
        noun="region or grouping",
        title="Regions & Groupings",
        model="Geo Region Grouping",
        fields=("members", "basis", "fuzzy"),
        concept_cards=(
            ConceptCard("5 Members", "Members", "Which countries make it up?", "members"),
            # Reverse: members -> grouping name. Only for fixed-membership
            # groupings; fuzzy macroregions have no crisp member list to show.
            ConceptCard("6 Name From Members", "Which Grouping", "Which grouping is this?", "name",
                        require=("members", "fixed_membership")),
            ConceptCard("7 Basis", "Basis", "What defines this grouping?", "basis"),
        ),
        accent="#6a4a8a",
    ),
    Family(
        key="plate-boundaries",
        title="Plate Boundary Types",
        model="Geo Plate Boundary",
        fields=("motion", "crust", "features", "examples", "type_map"),
        concept_cards=(
            ConceptCard("5 Motion", "Motion", "How do the plates move?", "motion", image_field="type_map"),
            ConceptCard("6 Crust", "Crust", "What happens to the crust?", "crust", image_field="type_map"),
            ConceptCard("7 Features", "Features", "What landforms and hazards form there?", "features", image_field="type_map"),
            ConceptCard("8 Examples", "Examples", "Where does it occur?", "examples", image_field="type_map"),
            # Reverse: given the motion and what happens to crust, name the type.
            ConceptCard("9 Name From Motion", "Which Boundary", "Which boundary type is this?", "name",
                        require=("motion", "crust")),
        ),
        accent="#8a3b3b",
        has_maps=False,
    ),
    Family(
        key="minor-plates",
        noun="minor tectonic plate",
        title="Minor Tectonic Plates",
        deck="Tectonic Plates::Minor Plates",
        model="Geo Minor Plate",
        # The 35 PB2002 plates outside the headline 17. Its own deck so it can
        # be studied (or ignored) independently of the major-plate deck.
        fields=("plate_kind", "boundary_fact", "carries", "region"),
        concept_cards=(
            ConceptCard("5 Boundary", "Boundary", "What boundary interaction defines it?", "boundary_fact"),
            ConceptCard("6 Carries", "Carries", "What does it carry?", "carries"),
            ConceptCard("7 Kind", "Kind", "Minor or micro, and what crust?", "plate_kind"),
        ),
        accent="#8a3b3b",
        subtitle_field="region",
    ),
    Family(
        key="country-blocs",
        noun="bloc or organization",
        title="Country Blocs & Organizations",
        model="Geo Country Bloc",
        # The static rungs of the bloc ladder: recognise the membership map,
        # then reproduce the list. The interactive tap-the-members drill is a
        # separate note type built on the GeoTrainer engine.
        fields=("acronym_expansion", "members", "member_count", "founded",
                "founded_note", "purpose", "hq", "membership_note", "category",
                "map_unique"),
        concept_cards=(
            ConceptCard("5 Members", "Members", "Which countries belong?", "members",
                        detail="membership_note"),
            ConceptCard("6 Acronym", "Acronym", "What do the letters stand for?", "acronym_expansion"),
            ConceptCard("7 Founded", "Founded", "When was it founded?", "founded",
                        detail="founded_note"),
            ConceptCard("8 Purpose", "Purpose", "What is it for?", "purpose", detail="hq"),
            ConceptCard("9 Size", "Size", "How many members does it have?", "member_count"),
        ),
        accent="#3b5f8a",
        subtitle_field="category",
        has_locate=False,
        name_card_require="map_unique",
    ),
    Family(
        key="named-boundaries",
        noun="plate boundary",
        title="Named Plate Boundaries",
        model="Geo Named Boundary",
        # Where the three types stop being definitions and become geography:
        # the prompt is a place you can point at, so nothing gives the answer
        # away. This is also the level at which plate pairs are worth knowing.
        fields=("boundary_type", "plates", "forms", "region"),
        concept_cards=(
            ConceptCard("5 Type", "Type", "Convergent, divergent or transform?", "boundary_type"),
            ConceptCard("6 Plates", "Plates", "Which plates meet here?", "plates"),
            ConceptCard("7 Forms", "Forms", "What does it build or trigger?", "forms"),
        ),
        accent="#8a3b3b",
        subtitle_field="region",
    ),
    Family(
        key="biomes",
        noun="biome",
        title="Biomes",
        model="Geo Biome",
        fields=("climate", "vegetation", "koppen", "examples", "photos",
                "mean_temperature", "mean_temperature_note",
                "annual_rainfall", "annual_rainfall_note",
                "temperature_swing", "temperature_swing_note"),
        concept_cards=(
            ConceptCard("5 Climate", "Climate", "What climate defines it?", "climate"),
            ConceptCard("6 Vegetation", "Vegetation", "What vegetation characterises it?", "vegetation",
                        gallery_field="photos"),
            ConceptCard("7 Koppen", "Köppen", "Which Köppen codes correspond?", "koppen"),
            # No `8 Examples` card: Elvis's verdict was that the map already
            # answers "where does it occur?", and the field stays for the audit.
            # The three climate dimensions the free-text `climate` sentence
            # rolls together. Answers are buckets, not numbers: a biome is a
            # range, and grading "was 180 mm close enough to 150-250?" every
            # review is not a skill. The measured spread rides underneath.
            ConceptCard("9 Temperature", "Temperature",
                        "How warm is it through the year, on average?",
                        "mean_temperature", detail="mean_temperature_note"),
            ConceptCard("10 Rainfall", "Rainfall",
                        "How much precipitation does it get in a year?",
                        "annual_rainfall", detail="annual_rainfall_note"),
            ConceptCard("11 Seasonality", "Seasonality",
                        "How far apart are its coldest and warmest months?",
                        "temperature_swing", detail="temperature_swing_note"),
        ),
        accent="#2f7a5f",
        extra={"gallery": "biome-photos.json"},
    ),
)


#: Köppen is structurally unlike the rest (a code system, not places), so it
#: gets its own model and its own card set — including the letter-semantics
#: cards that let you derive classes instead of memorising each one.
KOPPEN = Family(
    key="koppen",
    title="Köppen Climate",
    deck="Köppen::Climate Classes",
    model="Geo Koppen Class",
    fields=("code", "class_name", "group_code", "group_name", "criteria", "examples",
            "distribution_map", "blank_map"),
    concept_cards=(
        ConceptCard("5 Criteria", "Criteria", "What are its defining criteria?", "criteria"),
        ConceptCard("6 Examples", "Examples", "Where does it occur?", "examples"),
    ),
    accent="#2f5f8a",
)

#: The letter system itself: one note per letter+position, e.g. "second letter
#: w" -> "dry winter". These are what make the classification derivable.
KOPPEN_LETTERS = Family(
    key="koppen-letters",
    title="Köppen Letter System",
    deck="Köppen::Letter System",
    model="Geo Koppen Letter",
    fields=("letter", "position", "meaning", "position_label"),
    concept_cards=(),
    accent="#2f5f8a",
)
