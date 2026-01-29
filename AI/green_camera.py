# ============================================================
# pi_green_water_full_filter_viz.py
# Raspberry Pi 4 + Camera Module 3
# Volledige filtering geport van Green_plant_test_with_stats.py
# ============================================================

from picamera2 import Picamera2
import cv2
import numpy as np
import time
import matplotlib.pyplot as plt

# ------------------------------------------------------------
# HANDMATIGE INPUT
# ------------------------------------------------------------
SOIL_HUMIDITY = 45.0  # Huidige bodemvochtigheid in %

# ------------------------------------------------------------
# HSV WAARDES VOOR GROEN DETECTIE
# ------------------------------------------------------------
GREEN_LOWER = np.array([46, 53, 53])
GREEN_UPPER = np.array([70, 255, 255])

# ------------------------------------------------------------
# WATER FORMULE
# ------------------------------------------------------------
def predict_water(humidity, greenery):
    return 261.83 - humidity * 3.13314695 + greenery * 2.13997997

# ------------------------------------------------------------
# KLEP OPEN TIJD BEREKENEN
# ------------------------------------------------------------
def valve_open_time_ml(V_ml):
    a = 0.11455309
    b = 36.75567689
    c = 19.817595 - V_ml
    disc = b**2 - 4*a*c
    if disc < 0:
        return None
    return (-b + np.sqrt(disc)) / (2*a)

# ------------------------------------------------------------
# PIXEL VALIDATIE & VERTICALE CONNECTIES
# ------------------------------------------------------------
def is_valid_pixel(y, x, mask, radius=3, threshold=0.75):
    h, w = mask.shape
    y0 = max(0, y - radius)
    y1 = min(h, y + radius + 1)
    x0 = max(0, x - radius)
    x1 = min(w, x + radius + 1)
    patch = mask[y0:y1, x0:x1]
    return (np.count_nonzero(patch) / patch.size) >= threshold

def connected_vertically(y, x, mask, direction="up", length=10, min_ratio=0.6):
    h, w = mask.shape
    connected_rows = 0
    if direction == "up":
        for dy in range(1, length + 1):
            if y - dy < 0: break
            if mask[y - dy, x] > 0: connected_rows += 1
    else:
        for dy in range(1, length + 1):
            if y + dy >= h: break
            if mask[y + dy, x] > 0: connected_rows += 1
    return (connected_rows / length) >= min_ratio

# ------------------------------------------------------------
# CAMERA CAPTURE FUNCTIE
# ------------------------------------------------------------
def capture_frame():
    picam2 = Picamera2()
    picam2.configure(
        picam2.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)})
    )
    picam2.start()
    time.sleep(2)
    frame = picam2.capture_array()
    picam2.stop()
    return frame

# ------------------------------------------------------------
# PLANT ANALYSE
# ------------------------------------------------------------
def analyze_plant(image_rgb):
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    green_mask = cv2.inRange(hsv, GREEN_LOWER, GREEN_UPPER)
    h, w = green_mask.shape
    center_strip = green_mask[:, w // 2 - w // 20 : w // 2 + w // 20]

    top_pixel, bottom_pixel = None, None

    for y in reversed(range(center_strip.shape[0])):
        xs = np.where(center_strip[y] > 0)[0]
        for x in xs:
            if is_valid_pixel(y, x, center_strip) and connected_vertically(y, x, center_strip, "up"):
                bottom_pixel = y
                break
        if bottom_pixel is not None: break

    for y in range(center_strip.shape[0]):
        xs = np.where(center_strip[y] > 0)[0]
        for x in xs:
            if is_valid_pixel(y, x, center_strip) and connected_vertically(y, x, center_strip, "down"):
                top_pixel = y
                break
        if top_pixel is not None: break

    plant_height = (bottom_pixel - top_pixel if top_pixel is not None and bottom_pixel is not None else None)
    restricted_green_mask = green_mask.copy()
    if plant_height is not None:
        restricted_green_mask[:top_pixel, :] = 0
        restricted_green_mask[bottom_pixel + 1 :, :] = 0

    total_pixels = image_rgb.shape[0] * image_rgb.shape[1]
    green_pixels = np.count_nonzero(restricted_green_mask)
    green_ratio = (green_pixels / total_pixels) * 100

    return green_ratio, restricted_green_mask, top_pixel, bottom_pixel, plant_height

# ------------------------------------------------------------
# HOOFDPROGRAMMA
# ------------------------------------------------------------
if __name__ == "__main__":
    print("Capturing image...")
    image = capture_frame()
    print("Analyzing plant...")
    green_ratio, green_mask, top_pixel, bottom_pixel, plant_height = analyze_plant(image)

    water = predict_water(SOIL_HUMIDITY, green_ratio)
    valve_time = valve_open_time_ml(water)

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
        print("Predicted water is out of calibrated range!")

    # --------------------------------------------------------
    # VISUALISATIE
    # --------------------------------------------------------
    overlay = image.copy()
    overlay[green_mask > 0] = [0, 255, 0]
    overlay = cv2.addWeighted(image, 0.7, overlay, 0.3, 0)

    h, w, _ = image.shape
    if top_pixel is not None:
        cv2.line(overlay, (int(0.1*w), top_pixel), (int(0.9*w), top_pixel), (255,0,0), 2)
    if bottom_pixel is not None:
        cv2.line(overlay, (int(0.1*w), bottom_pixel), (int(0.9*w), bottom_pixel), (255,0,0), 2)

    # Maak een grote OpenCV window
    cv2.namedWindow("Plant Analysis", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Plant Analysis", 960, 540)
    cv2.imsh
