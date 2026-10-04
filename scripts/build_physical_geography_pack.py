"""Build the accepted Physical Geography component, with its concept media."""
from build_apkg import PUBLIC_PACKS, build_public_pack

if __name__ == "__main__":
    build_public_pack("physical-geography", PUBLIC_PACKS["physical-geography"])
