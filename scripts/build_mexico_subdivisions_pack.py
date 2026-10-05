"""Build the accepted stable-identity Mexico subdivisions component."""
from build_apkg import PUBLIC_PACKS, build_public_pack

if __name__ == "__main__":
    build_public_pack("mexico-subdivisions", PUBLIC_PACKS["mexico-subdivisions"])
