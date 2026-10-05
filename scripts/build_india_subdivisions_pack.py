"""Build the accepted stable-identity India subdivisions component."""
from build_apkg import PUBLIC_PACKS, build_public_pack

if __name__ == "__main__":
    build_public_pack("india-subdivisions", PUBLIC_PACKS["india-subdivisions"])
