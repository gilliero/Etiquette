#!/usr/bin/env python3
import os
import argparse
import requests
from PIL import Image, ImageDraw, ImageFont
import qrcode
import subprocess

# ----------------------- NetBox API -----------------------
def get_devices(base_url, token):
    url = f"{base_url}/api/dcim/devices/"
    headers = {"Authorization": f"Token {token}", "Accept": "application/json"}
    devices = []

    while url:
        response = requests.get(url, headers=headers, verify=True)
        if response.status_code != 200:
            print(f"Erreur {response.status_code} : {response.text}")
            return []

        data = response.json()
        for dev in data.get("results", []):
            # Exclure les machines de type "VM"
            device_type = dev.get("device_type", {})
            # Essayez d'adapter la clé selon la structure exacte de l'API NetBox
            type_name = device_type.get("model", "") or device_type.get("slug", "")
            if type_name.lower() == "vm":
                continue
            devices.append({
                "id": dev.get("id"),
                "name": dev.get("name"),
                "asset_tag": dev.get("asset_tag") or ""
            })

        url = data.get("next")  # pagination

    return devices

# ----------------------- Etiquette -----------------------
dpi = 300
width_mm = 90
height_mm = 38

def mm_to_px(mm):
    return int((mm / 25.4) * dpi)

width_px = mm_to_px(width_mm)
height_px = mm_to_px(height_mm)
output_dir = "etiquettes"
os.makedirs(output_dir, exist_ok=True)

def generate_label(device):
    img = Image.new("RGB", (width_px, height_px), "white")
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("arialbd.ttf", 54)
        font_small = ImageFont.truetype("arial.ttf", 32)
    except:
        font_title = ImageFont.load_default()
        font_small = ImageFont.load_default()

    top_margin = 18
    bottom_margin = 18
    codes_height = int((height_px - top_margin - bottom_margin) * 0.55)
    qr_size = codes_height

    # QR codes
    barcode_value = f"{device['asset_tag']}" if device['asset_tag'] else f"None-{device['id']}"
    
    qr1 = qrcode.QRCode(box_size=3, border=1)
    qr1.add_data(barcode_value)
    qr1.make(fit=True)
    qr1_img = qr1.make_image(fill_color="black", back_color="white").convert("RGB")
    qr1_img = qr1_img.resize((qr_size, qr_size))

    qr2 = qrcode.QRCode(box_size=3, border=1)
    device_url = f"https://icit-nsot.epfl.ch/dcim/devices/{device['id']}"
    qr2.add_data(device_url)
    qr2.make(fit=True)
    qr2_img = qr2.make_image(fill_color="black", back_color="white").convert("RGB")
    qr2_img = qr2_img.resize((qr_size, qr_size))

    # Positionnement fixe des QR codes
    margin_mm = 3  # distance du bord en mm
    qr1_x = mm_to_px(margin_mm)
    qr2_x = width_px - mm_to_px(margin_mm) - qr_size
    y_pos = (height_px - qr_size) // 2

    img.paste(qr1_img, (qr1_x, y_pos))
    img.paste(qr2_img, (qr2_x, y_pos))

    # Texte (nom du device) centré entre les deux QR
    text = device['name'].split('.')[0]
    bbox = draw.textbbox((0, 0), text, font=font_title)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    # Centrage horizontal parfait entre les deux QR
    espace_gauche = qr1_x + qr_size
    espace_droit = qr2_x
    espace_centre = espace_droit - espace_gauche
    text_x = espace_gauche + (espace_centre - text_width) // 2
    text_y = y_pos + (qr_size - text_height) // 2
    draw.text((text_x, text_y), text, fill="black", font=font_title)

    # Texte sous QR codes
    barcode_text_bbox = draw.textbbox((0,0), barcode_value, font=font_small)
    barcode_text_width = barcode_text_bbox[2] - barcode_text_bbox[0]
    barcode_text_x = qr1_x + (qr_size - barcode_text_width) // 2
    barcode_text_y = y_pos + qr_size + 5
    draw.text((barcode_text_x, barcode_text_y), barcode_value, fill="black", font=font_small)

    dcim_text = "DCIM"
    dcim_bbox = draw.textbbox((0,0), dcim_text, font=font_small)
    dcim_text_width = dcim_bbox[2] - dcim_bbox[0]
    dcim_text_x = qr2_x + (qr_size - dcim_text_width) // 2
    dcim_text_y = y_pos + qr_size + 5
    draw.text((dcim_text_x, dcim_text_y), dcim_text, fill="black", font=font_small)

    output_path = os.path.join(output_dir, f"{text}.png")
    img.save(output_path, dpi=(dpi, dpi))
    print(f"Label generated: {output_path}")
    return os.path.abspath(output_path)

# ----------------------- Main -----------------------
def main():
    parser = argparse.ArgumentParser(description="NetBox Device Labels Generator")
    parser.add_argument("--url", default="https://icit-nsot.epfl.ch", help="NetBox base URL")
    parser.add_argument("--token", required=True, help="NetBox API token")
    args = parser.parse_args()

    devices = get_devices(args.url, args.token)
    if not devices:
        print("No devices found. Exiting.")
        return

    generated_files = []
    for device in devices:
        generated_files.append(generate_label(device))

    # Impression (Windows)
    printer_name = "Brother QL-720NW USB"
    for file_path in generated_files:
        try:
            ps_command = [
                "powershell",
                "-Command",
                f'Start-Process ptedit54.exe -ArgumentList \'/pt "{file_path}" "{printer_name}"\' -Wait'
            ]
            subprocess.run(ps_command, check=True)
            print(f"Sent to printer: {file_path}")
        except Exception as e:
            print(f"Could not print {file_path}: {e}")

if __name__ == "__main__":
    main()
