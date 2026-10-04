"""Build the accepted Plate Tectonics component with stable public IDs."""
from build_apkg import PUBLIC_PACKS, build_public_pack

if __name__ == "__main__":
    build_public_pack("plate-tectonics", PUBLIC_PACKS["plate-tectonics"])
