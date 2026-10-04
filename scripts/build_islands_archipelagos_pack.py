"""Build the accepted stable-identity Islands & Archipelagos component."""
from build_apkg import PUBLIC_PACKS, build_public_pack

if __name__ == "__main__":
    build_public_pack("islands-archipelagos", PUBLIC_PACKS["islands-archipelagos"])
