# ============================================================
# pi_green_water_full_filter.py
# Raspberry Pi 4 + Camera Module 3
# Full filtering ported from Green_plant_test_with_stats.py
# ============================================================

from picamera2 import Picamera2
import cv2
import numpy as np
import time
import matplotlib.pyplot as plt

# ------------------------------------------------------------
# MANUAL INPUT
# ------------------------------------------------------------
SOIL_HUMIDITY = 40.0  # %

# ------------------------------------------------------------
# HSV DEFINITIONS
# ------------------------------------------------------------
GREEN_LOWER = np.array([21, 26, 26])
GREEN_UPPER = np.array([95, 255, 255])

# ------------------------------------------------------------
# WATER FORMULA
# ------------------------------------------------------------
def predict_water(humidity, greenery):
    return 261.83 - humidity * 3.13314695 + greenery * 2.13997997

# ------------------------------------------------------------
# FILTERING FUNCTIONS (UNCHANGED)
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
# CAMERA CAPTURE (NO SAVE)
# ------------------------------------------------------------
def capture_frame():
    picam2 = Picamera2()
    picam2.configure(
        picam2.create_preview_configuration(
            main={"format": "RGB888", "size": (640, 480)}
        )
    )
    picam2.start()
    time.sleep(2)
    frame = picam2.capture_array()
    picam2.stop()
    return frame

# ------------------------------------------------------------
# FULL PLANT ANALYSIS
# ------------------------------------------------------------
def analyze_plant(image_rgb):
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

    green_mask = cv2.inRange(hsv, GREEN_LOWER, GREEN_UPPER)

    h, w = green_mask.shape
    center_strip = green_mask[:, w // 2 - w // 20 : w // 2 + w // 20]

    top_pixel = None
    bottom_pixel = None

    # --- bottom pixel search
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

    # --- top pixel search
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

    plant_height = (
        bottom_pixel - top_pixel
        if top_pixel is not None and bottom_pixel is not None
        else None
    )

    restricted_green_mask = green_mask.copy()
    if plant_height is not None:
        restricted_green_mask[:top_pixel, :] = 0
        restricted_green_mask[bottom_pixel + 1 :, :] = 0

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
# MAIN
# ------------------------------------------------------------
if __name__ == "__main__":
    print("📷 Capturing image...")
    image = capture_frame()

    print("🌱 Analyzing plant (full filtering)...")
    (
        green_ratio,
        green_mask,
        top_pixel,
        bottom_pixel,
        plant_height,
    ) = analyze_plant(image)

    water = predict_water(SOIL_HUMIDITY, green_ratio)

    print("\n--- RESULTS ---")
    print(f"Soil humidity: {SOIL_HUMIDITY:.1f}%")
    print(f"Green % (plant-only): {green_ratio:.2f}%")
    print(f"Top pixel: {top_pixel}")
    print(f"Bottom pixel: {bottom_pixel}")
    print(f"Plant height (px): {plant_height}")
    print(f"Predicted water: {water:.2f}")

    # --------------------------------------------------------
    # VISUALIZATION
    # --------------------------------------------------------
    overlay = image.copy()
    overlay[green_mask > 0] = [0, 255, 0]
    overlay = cv2.addWeighted(image, 0.7, overlay, 0.3, 0)

    h, w, _ = image.shape
    if top_pixel is not None:
        cv2.line(overlay, (int(0.15 * w), top_pixel), (int(0.85 * w), top_pixel), (255, 0, 0), 2)
    if bottom_pixel is not None:
        cv2.line(overlay, (int(0.15 * w), bottom_pixel), (int(0.85 * w), bottom_pixel), (255, 0, 0), 2)

    plt.figure(figsize=(12, 4))
    plt.suptitle(
        f"Green {green_ratio:.2f}% | Height {plant_height}px | Water {water:.2f}"
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
