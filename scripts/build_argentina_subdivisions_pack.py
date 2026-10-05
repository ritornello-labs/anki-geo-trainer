"""Build the accepted stable-identity Argentina subdivisions component."""
from build_apkg import PUBLIC_PACKS, build_public_pack

if __name__ == "__main__":
    build_public_pack("argentina-subdivisions", PUBLIC_PACKS["argentina-subdivisions"])
