"""Build the accepted 38-province Indonesia component with stable identities."""
from build_apkg import PUBLIC_PACKS, build_public_pack

if __name__ == "__main__":
    build_public_pack("indonesia-subdivisions", PUBLIC_PACKS["indonesia-subdivisions"])
