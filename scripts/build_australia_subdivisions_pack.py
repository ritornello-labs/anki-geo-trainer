"""Build the accepted stable-identity Australia subdivisions component."""
from build_apkg import PUBLIC_PACKS, build_public_pack

if __name__ == "__main__":
    build_public_pack("australia-subdivisions", PUBLIC_PACKS["australia-subdivisions"])
