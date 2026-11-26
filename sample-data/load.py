"""Puts the sample items, with their descriptions and pictures, into a running app.

    set -a && . ./.env && set +a && python3 sample-data/load.py

Signs in as the admin from ADMIN_EMAIL and ADMIN_PASSWORD. Items that exist (same SKU) keep their stock;
their description is set, and pictures are added only if they have none. APP_URL changes the address.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
API = os.environ.get("APP_URL", "http://localhost:8200").rstrip("/") + "/api"

ITEMS = [
    {
        "sku": "MON-24",
        "name": "24 inch monitor",
        "quantity": 4,
        "reorder_level": 5,
        "images": ["monitor.png", "monitor-back.png"],
        "description": "Full HD 24 inch screen on a tilting stand, with HDMI and DisplayPort inputs.\n"
        "Comes with its power cable and one HDMI cable.",
    },
    {
        "sku": "KB-02",
        "name": "Keyboard",
        "quantity": 12,
        "reorder_level": 6,
        "images": ["keyboard.png", "keyboard-close.png"],
        "description": "Compact wired keyboard with quiet keys and a USB connection.\n"
        "Works with Windows, macOS and Linux.",
    },
    {
        "sku": "CBL-01",
        "name": "USB-C cable",
        "quantity": 40,
        "reorder_level": 10,
        "images": ["cable.png", "cable-plug.png"],
        "description": "1 metre braided USB-C to USB-C cable for charging and data.",
    },
]


def call(path, token=None, method="GET", json_body=None, image=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    data = image
    if image is not None:
        headers["Content-Type"] = "image/png"
    elif json_body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(json_body).encode()
    request = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def main():
    try:
        sign_in = {"login": os.environ["ADMIN_EMAIL"], "password": os.environ["ADMIN_PASSWORD"]}
    except KeyError as missing:
        sys.exit(f"Set {missing} first (see .env)")
    token = call("/auth/login", method="POST", json_body=sign_in)["access_token"]
    existing = {item["sku"]: item for item in call("/items", token)}

    for sample in ITEMS:
        item = existing.get(sample["sku"])
        if item is None:
            fields = {key: sample[key] for key in ("sku", "name", "quantity", "reorder_level")}
            item = call("/items", token, "POST", json_body=fields)
        call(f"/items/{item['id']}", token, "PATCH", json_body={"description": sample["description"]})
        if not item["image_ids"]:
            for name in sample["images"]:
                call(f"/items/{item['id']}/images", token, "POST", image=(HERE / name).read_bytes())
        print(f"{sample['sku']}: description and pictures in place")


if __name__ == "__main__":
    main()
