"""Describe generated public leaves and their frozen parent decks."""

import json

import genanki
from deck_descriptions import ROOT, description_for


class MarkdownDeck(genanki.Deck):
    def to_json(self):
        data = super().to_json()
        data["md"] = True
        return data


def describe_public_decks(decks):
    """Keep existing leaf IDs; include explicit, frozen parent descriptions."""
    by_name = {}
    for deck in decks:
        enriched = MarkdownDeck(deck.deck_id, deck.name, description_for(deck.name))
        enriched.notes = deck.notes
        enriched.models = deck.models
        by_name[deck.name] = enriched
    parents = json.loads((ROOT / "data/deck-container-identities.json").read_text())["decks"]
    for name in list(by_name):
        parts = name.split("::")
        for n in range(1, len(parts)):
            parent = "::".join(parts[:n])
            if parent not in by_name:
                by_name[parent] = MarkdownDeck(parents[parent], parent, description_for(parent))
    assert len({d.deck_id for d in by_name.values()}) == len(by_name)
    return [by_name[name] for name in sorted(by_name)]
