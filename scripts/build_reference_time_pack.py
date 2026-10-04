"""Build the accepted Reference Lines & Time public component."""
from pathlib import Path
import genanki
from build_reference_lines_qa import reference_decks
from build_time_zone_atlas_qa import atlas_decks

def build():
    atlas, media = atlas_decks()
    decks = reference_decks() + atlas
    output = Path(__file__).resolve().parents[1] / "dist/geo-trainer-reference-lines-time.apkg"
    output.parent.mkdir(parents=True, exist_ok=True)
    package = genanki.Package(decks)
    package.media_files = media
    package.write_to_file(output)
    print(output)
    return output

if __name__ == "__main__":
    build()
