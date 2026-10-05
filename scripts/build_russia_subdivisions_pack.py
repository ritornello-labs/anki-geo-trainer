"""Build the accepted stable-identity Russia subdivisions component."""
from build_apkg import PUBLIC_PACKS, build_public_pack

if __name__ == "__main__":
    build_public_pack("russia-subdivisions", PUBLIC_PACKS["russia-subdivisions"])
