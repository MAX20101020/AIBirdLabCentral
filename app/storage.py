import os
import requests
from fastapi import HTTPException

PINATA_API_KEY = os.getenv("PINATA_API_KEY")
PINATA_API_SECRET = os.getenv("PINATA_API_SECRET")
PINATA_JWT = os.getenv("PINATA_JWT")


def upload_to_pinata(file_path: str, filename: str) -> str:
    url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    headers = {}
    if PINATA_JWT:
        headers["Authorization"] = f"Bearer {PINATA_JWT}"
    else:
        headers["pinata_api_key"] = PINATA_API_KEY
        headers["pinata_secret_api_key"] = PINATA_API_SECRET

    with open(file_path, "rb") as f:
        files = {"file": (filename, f)}
        response = requests.post(url, headers=headers, files=files)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Pinata error: {response.text}")

    ipfs_hash = response.json().get("IpfsHash")
    return f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}"