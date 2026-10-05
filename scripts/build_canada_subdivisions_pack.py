"""Build the accepted stable-identity Canada subdivisions component."""
from build_apkg import PUBLIC_PACKS, build_public_pack

if __name__ == "__main__":
    build_public_pack("canada-subdivisions", PUBLIC_PACKS["canada-subdivisions"])
