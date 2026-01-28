# ============================================================
# Green_plant_test_with_stats.py
# ============================================================

import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from glob import glob

# ------------------------------------------------------------
# CONFIGURATIE
# ------------------------------------------------------------
image_folder = "test_set"        # Map met testafbeeldingen
show_visuals = True              # Visualisatie aan/uit
save_results = False             # Resultaten opslaan in CSV
output_csv = "green_analysis_results.csv"  # Naam CSV-bestand

# ------------------------------------------------------------
# KLEURDEFINITIES (HSV)
# ------------------------------------------------------------
GREEN_LOWER = np.array([21, 26, 26])  # Minimum HSV-waarden voor groen
GREEN_UPPER = np.array([95, 255, 255])  # Maximum HSV-waarden voor groen
DARK_GREEN_MAX_V = 100                # Maximale brightness voor donkergroen

# ------------------------------------------------------------
# RESULTATEN OPSLAG
# ------------------------------------------------------------
results = []  # Hier slaan we de resultaten per afbeelding op

# ------------------------------------------------------------
# FUNCTIES
# ------------------------------------------------------------
def is_valid_pixel(y, x, mask, radius=3, threshold=0.75):
    """
    Controleer of een pixel 'groen genoeg' is door een vierkante patch rond de pixel te bekijken.
    radius: grootte van de patch (in pixels)
    threshold: minimaal percentage pixels dat groen moet zijn
    """
    h, w = mask.shape
    y0 = max(0, y - radius)
    y1 = min(h, y + radius + 1)
    x0 = max(0, x - radius)
    x1 = min(w, x + radius + 1)
    patch = mask[y0:y1, x0:x1]
    return (np.count_nonzero(patch) / patch.size) >= threshold  # True als genoeg pixels groen zijn


def connected_vertically(y, x, mask, direction='up', length=10, min_ratio=0.5):
    """
    Controleer of een pixel verticaal verbonden is met andere groene pixels.
    direction: 'up' of 'down'
    length: aantal pixels verticaal dat gecontroleerd wordt
    min_ratio: minimaal percentage pixels dat groen moet zijn om geldig te zijn
    """
    h, w = mask.shape
    connected_rows = 0

    if direction == 'up':
        for dy in range(1, length + 1):
            if y - dy < 0:
                break
            if mask[y - dy, x] > 0:
                connected_rows += 1
    else:  # down
        for dy in range(1, length + 1):
            if y + dy >= h:
                break
            if mask[y + dy, x] > 0:
                connected_rows += 1

    return (connected_rows / length) >= min_ratio  # True als voldoende pixels verbonden zijn


# ------------------------------------------------------------
# AFBEELDINGEN VERWERKEN
# ------------------------------------------------------------
# Alle JPG/JPEG-afbeeldingen in submappen van image_folder
image_paths = glob(os.path.join(image_folder, "*/*.jpg")) + \
              glob(os.path.join(image_folder, "*/*.jpeg")) + \
              glob(os.path.join(image_folder, "*/*.JPG")) + \
              glob(os.path.join(image_folder, "*/*.JPEG"))

for img_path in image_paths:
    image_bgr = cv2.imread(img_path)  # Lees afbeelding in BGR
    if image_bgr is None:
        continue

    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)  # Converteer naar RGB
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)        # Converteer naar HSV

    # --------------------------------------------------------
    # GROENE PIXELS DETECTEREN
    # --------------------------------------------------------
    green_mask = cv2.inRange(hsv, GREEN_LOWER, GREEN_UPPER)  # Masker voor alle groene pixels
    dark_green_mask = green_mask.copy()
    dark_green_mask[hsv[:, :, 2] > DARK_GREEN_MAX_V] = 0     # Alleen donkergroen

    # --------------------------------------------------------
    # PLANT HOOGTE SCHATTEN
    # --------------------------------------------------------
    h, w = green_mask.shape
    center_strip = green_mask[:, w // 2 - w // 20: w // 2 + w // 20]  # Centrale verticale strook

    top_pixel = bottom_pixel = None
    vertical_check_len = 10        # Aantal pixels verticaal om connectie te checken
    vertical_min_ratio = 0.6       # Percentage verbonden pixels dat groen moet zijn

    # Zoek bottom pixel
    for y in reversed(range(center_strip.shape[0])):
        xs = np.where(center_strip[y, :] > 0)[0]
        for x in xs:
            if (
                is_valid_pixel(y, x, center_strip, radius=3, threshold=0.75)
                and connected_vertically(y, x, center_strip, direction='up', length=vertical_check_len, min_ratio=vertical_min_ratio)
            ):
                bottom_pixel = y
                break
        if bottom_pixel is not None:
            break

    # Zoek top pixel
    for y in range(center_strip.shape[0]):
        xs = np.where(center_strip[y, :] > 0)[0]
        for x in xs:
            if (
                is_valid_pixel(y, x, center_strip, radius=3, threshold=0.75)
                and connected_vertically(y, x, center_strip, direction='down', length=vertical_check_len, min_ratio=vertical_min_ratio)
            ):
                top_pixel = y
                break
        if top_pixel is not None:
            break

    plant_height = (bottom_pixel - top_pixel) if top_pixel is not None and bottom_pixel is not None else None

    # --------------------------------------------------------
    # BEPERK GROENE PIXELS TOT PLANTGEBIED
    # --------------------------------------------------------
    restricted_green_mask = green_mask.copy()
    if top_pixel is not None and bottom_pixel is not None:
        restricted_green_mask[:top_pixel, :] = 0
        restricted_green_mask[bottom_pixel + 1:, :] = 0

    restricted_dark_green_mask = dark_green_mask.copy()
    restricted_dark_green_mask[restricted_green_mask == 0] = 0

    # --------------------------------------------------------
    # METRIEKEN BEREKENEN
    # --------------------------------------------------------
    total_pixels = image_rgb.shape[0] * image_rgb.shape[1]  # Totaal aantal pixels in afbeelding
    green_pixels = np.count_nonzero(restricted_green_mask)  # Aantal groene pixels
    dark_green_pixels = np.count_nonzero(restricted_dark_green_mask)

    green_ratio = (green_pixels / total_pixels) * 100      # % groene pixels
    dark_green_ratio = (dark_green_pixels / total_pixels) * 100
    mean_green_saturation = np.mean(hsv[:, :, 1][restricted_green_mask > 0]) if green_pixels > 0 else 0

    # --------------------------------------------------------
    # RESULTATEN OPSLAAN
    # --------------------------------------------------------
    class_name = os.path.basename(os.path.dirname(img_path))  # Naam van de klasse/submap
    file_name = os.path.basename(img_path)                    # Bestandsnaam

    results.append([
        file_name,
        class_name,
        green_ratio,
        dark_green_ratio,
        mean_green_saturation,
        top_pixel,
        bottom_pixel,
        plant_height
    ])

    # --------------------------------------------------------
    # VISUALISATIE
    # --------------------------------------------------------
    if show_visuals:
        overlay = image_rgb.copy()
        overlay[restricted_green_mask > 0] = [0, 255, 0]  # Groen overlay
        overlay = cv2.addWeighted(image_rgb, 0.7, overlay, 0.3, 0)

        line_start_x = int(0.15 * w)
        line_end_x = int(0.85 * w)

        if top_pixel is not None:
            cv2.line(overlay, (line_start_x, top_pixel), (line_end_x, top_pixel), (255, 0, 0), 2)
        if bottom_pixel is not None:
            cv2.line(overlay, (line_start_x, bottom_pixel), (line_end_x, bottom_pixel), (255, 0, 0), 2)

        plt.figure(figsize=(12, 4))
        plt.suptitle(file_name)

        plt.subplot(1, 3, 1)
        plt.title("Original")
        plt.imshow(image_rgb)
        plt.axis("off")

        plt.subplot(1, 3, 2)
        plt.title("Restricted green mask")
        plt.imshow(restricted_green_mask, cmap="gray")
        plt.axis("off")

        plt.subplot(1, 3, 3)
        plt.title("Green overlay + top/bottom")
        plt.imshow(overlay)
        plt.axis("off")

        plt.tight_layout()
        plt.show()

    # --------------------------------------------------------
    # CONSOLE OUTPUT
    # --------------------------------------------------------
    print(f"\nAfbeelding: {file_name} ({class_name})")
    print(f"Percentage groene pixels (plant-only): {green_ratio:.2f}%")
    print(f"Percentage donkergroene pixels: {dark_green_ratio:.2f}%")
    print(f"Gemiddelde groene verzadiging: {mean_green_saturation:.2f}")
    print(f"Top pixel: {top_pixel}")
    print(f"Bottom pixel: {bottom_pixel}")
    print(f"Geschatte plant hoogte (pixels): {plant_height}")

# =============================================================
# STATISTIEKEN OVER ALLE AFBEELDINGEN
# =============================================================
green_ratios = [r[2] for r in results if r[2] is not None]
heights = [r[7] for r in results if r[7] is not None]

if green_ratios and heights:
    print("\n--- STATISTIEKEN OVER ALLE AFBEELDINGEN ---")
    print(f"Green leaf % - Gemiddeld: {np.mean(green_ratios):.2f}, Min: {np.min(green_ratios):.2f}, Max: {np.max(green_ratios):.2f}")
    print(f"Plant height - Gemiddeld: {np.mean(heights):.2f}, Min: {np.min(heights):.2f}, Max: {np.max(heights):.2f}")
