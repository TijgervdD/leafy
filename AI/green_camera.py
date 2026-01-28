# ============================================================
# pi_green_water_full_filter.py
# Raspberry Pi 4 + Camera Module 3
# Volledige filtering geport van Green_plant_test_with_stats.py
# ============================================================

from picamera2 import Picamera2  # Camera library voor Raspberry Pi
import cv2  # OpenCV voor beeldverwerking
import numpy as np  # Voor wiskunde en arrays
import time  # Voor vertragingen
import matplotlib.pyplot as plt  # Voor visualisatie

# ------------------------------------------------------------
# HANDMATIGE INPUT
# ------------------------------------------------------------
SOIL_HUMIDITY = humidi  # Huidige bodemvochtigheid in %

# ------------------------------------------------------------
# HSV WAARDES VOOR GROEN DETECTIE
# ------------------------------------------------------------
GREEN_LOWER = np.array([46, 53, 53])  # Ondergrens HSV voor groen
GREEN_UPPER = np.array([70, 255, 255])  # Bovengrens HSV voor groen

# ------------------------------------------------------------
# WATER FORMULE
# ------------------------------------------------------------
def predict_water(humidity, greenery):
    """
    Bereken hoeveelheid water (ml) gebaseerd op bodemvocht en groenpercentage
    """
    return 261.83 - humidity * 3.13314695 + greenery * 2.13997997

# ------------------------------------------------------------
# KLEP OPEN TIJD BEREKENEN
# ------------------------------------------------------------
def valve_open_time_ml(V_ml):
    """
    Bereken hoe lang de solenoïde klep open moet staan voor een doelvolume V_ml.
    Retourneert tijd in seconden. Geeft None terug als V_ml buiten bereik ligt.
    """
    a = 0.11455309
    b = 36.75567689
    c = 19.817595 - V_ml

    # Discriminant van de kwadratische vergelijking
    discriminant = b**2 - 4*a*c
    if discriminant < 0:
        # Volume buiten het gekalibreerde bereik
        return None

    # Bereken de tijd met de positieve wortel
    t = (-b + np.sqrt(discriminant)) / (2*a)
    return t

# ------------------------------------------------------------
# FUNCTIE OM TE CONTROLEREN OF PIXEL GELDIG IS
# ------------------------------------------------------------
def is_valid_pixel(y, x, mask, radius=3, threshold=0.75):
    """
    Controleer of een pixel genoeg groene pixels in de buurt heeft
    radius = grootte van de buurt
    threshold = percentage groene pixels dat minimaal moet zijn
    """
    h, w = mask.shape
    y0 = max(0, y - radius)
    y1 = min(h, y + radius + 1)
    x0 = max(0, x - radius)
    x1 = min(w, x + radius + 1)
    patch = mask[y0:y1, x0:x1]
    return (np.count_nonzero(patch) / patch.size) >= threshold

# ------------------------------------------------------------
# FUNCTIE OM VERTICAAL VERBONDEN PIXELS TE CONTROLEREN
# ------------------------------------------------------------
def connected_vertically(y, x, mask, direction="up", length=10, min_ratio=0.6):
    """
    Controleer of een pixel verbonden is met andere pixels in verticale richting
    direction = 'up' of 'down'
    length = aantal pixels dat gecontroleerd wordt
    min_ratio = minimum ratio van verbonden pixels
    """
    h, w = mask.shape
    connected_rows = 0

    if direction == "up":
        for dy in range(1, length + 1):
            if y - dy < 0:
                break
            if mask[y - dy, x] > 0:
                connected_rows += 1
    else:
        for dy in range(1, length + 1):
            if y + dy >= h:
                break
            if mask[y + dy, x] > 0:
                connected_rows += 1

    return (connected_rows / length) >= min_ratio

# ------------------------------------------------------------
# CAMERA CAPTURE FUNCTIE
# ------------------------------------------------------------
def capture_frame():
    """
    Maak een foto met de Raspberry Pi camera
    """
    picam2 = Picamera2()
    picam2.configure(
        picam2.create_preview_configuration(
            main={"format": "RGB888", "size": (640, 480)}
        )
    )
    picam2.start()
    time.sleep(2)  # Wacht tot camera klaar is
    frame = picam2.capture_array()
    picam2.stop()
    return frame

# ------------------------------------------------------------
# VOLLEDIGE PLANT ANALYSE
# ------------------------------------------------------------
def analyze_plant(image_rgb):
    """
    Analyseer de plant op groene pixels en bepaal top en bottom pixel
    """
    # Converteer naar BGR voor OpenCV
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    # Converteer naar HSV om groen makkelijker te detecteren
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

    # Maak een mask van alle groene pixels
    green_mask = cv2.inRange(hsv, GREEN_LOWER, GREEN_UPPER)

    # Focus op het centrale deel van de plant
    h, w = green_mask.shape
    center_strip = green_mask[:, w // 2 - w // 20 : w // 2 + w // 20]

    top_pixel = None
    bottom_pixel = None

    # --- zoek bottom pixel
    for y in reversed(range(center_strip.shape[0])):
        xs = np.where(center_strip[y] > 0)[0]
        for x in xs:
            if (
                is_valid_pixel(y, x, center_strip)
                and connected_vertically(y, x, center_strip, "up")
            ):
                bottom_pixel = y
                break
        if bottom_pixel is not None:
            break

    # --- zoek top pixel
    for y in range(center_strip.shape[0]):
        xs = np.where(center_strip[y] > 0)[0]
        for x in xs:
            if (
                is_valid_pixel(y, x, center_strip)
                and connected_vertically(y, x, center_strip, "down")
            ):
                top_pixel = y
                break
        if top_pixel is not None:
            break

    # Bereken plant hoogte
    plant_height = (
        bottom_pixel - top_pixel
        if top_pixel is not None and bottom_pixel is not None
        else None
    )

    # Beperk mask tot plant hoogte
    restricted_green_mask = green_mask.copy()
    if plant_height is not None:
        restricted_green_mask[:top_pixel, :] = 0
        restricted_green_mask[bottom_pixel + 1 :, :] = 0

    # Bereken percentage groene pixels
    total_pixels = image_rgb.shape[0] * image_rgb.shape[1]
    green_pixels = np.count_nonzero(restricted_green_mask)
    green_ratio = (green_pixels / total_pixels) * 100

    return (
        green_ratio,
        restricted_green_mask,
        top_pixel,
        bottom_pixel,
        plant_height,
    )

# ------------------------------------------------------------
# HOOFDPROGRAMMA
# ------------------------------------------------------------
if __name__ == "__main__":
    print("Capturing image...")
    image = capture_frame()  # Maak een foto van de plant

    print("Analyzing plant (full filtering)...")
    # Analyseer de plant op groen en hoogte
    (
        green_ratio,
        green_mask,
        top_pixel,
        bottom_pixel,
        plant_height,
    ) = analyze_plant(image)

    # Bereken hoeveelheid water en klep open tijd
    water = predict_water(SOIL_HUMIDITY, green_ratio)
    valve_time = valve_open_time_ml(water)

    # Print resultaten
    print("\n--- RESULTS ---")
    print(f"Soil humidity: {SOIL_HUMIDITY:.1f}%")
    print(f"Green % (plant-only): {green_ratio:.2f}%")
    print(f"Top pixel: {top_pixel}")
    print(f"Bottom pixel: {bottom_pixel}")
    print(f"Plant height (px): {plant_height}")
    print(f"Predicted water: {water:.2f} ml")
    if valve_time is not None:
        print(f"Valve should open for: {valve_time:.2f} s")
    else:
        print("Predicted water is out of the calibrated range!")

    # --------------------------------------------------------
    # VISUALISATIE
    # --------------------------------------------------------
    overlay = image.copy()  # Maak kopie van originele afbeelding
    overlay[green_mask > 0] = [0, 255, 0]  # Highlight groene pixels
    overlay = cv2.addWeighted(image, 0.7, overlay, 0.3, 0)  # Combineer overlay met originele

    h, w, _ = image.shape
    # Teken top pixel lijn
    if top_pixel is not None:
        cv2.line(
            overlay, (int(0.15 * w), top_pixel), (int(0.85 * w), top_pixel), (255, 0, 0), 2
        )
    # Teken bottom pixel lijn
    if bottom_pixel is not None:
        cv2.line(
            overlay, (int(0.15 * w), bottom_pixel), (int(0.85 * w), bottom_pixel), (255, 0, 0), 2
        )

    # Maak figuur met 3 plots
    plt.figure(figsize=(12, 4))
    plt.suptitle(
        f"Green {green_ratio:.2f}% | Height {plant_height}px | Water {water:.2f} ml | Valve {valve_time:.2f} s"
    )

    plt.subplot(1, 3, 1)
    plt.title("Captured")
    plt.imshow(image)
    plt.axis("off")

    plt.subplot(1, 3, 2)
    plt.title("Restricted Mask")
    plt.imshow(green_mask, cmap="gray")
    plt.axis("off")

    plt.subplot(1, 3, 3)
    plt.title("Overlay + Top/Bottom")
    plt.imshow(overlay)
    plt.axis("off")

    plt.tight_layout()
    plt.show()
