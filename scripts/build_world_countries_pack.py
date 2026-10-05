"""Build the accepted stable-identity World Countries component."""
from build_apkg import PUBLIC_PACKS, build_public_pack

if __name__ == "__main__":
    build_public_pack("world-countries", PUBLIC_PACKS["world-countries"])
