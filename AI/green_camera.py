# ============================================================
# pi_green_water_live.py
# Raspberry Pi 4 + Camera Module 3
# ============================================================

from picamera2 import Picamera2
import cv2
import numpy as np
import time
import matplotlib.pyplot as plt

# ------------------------------------------------------------
# MANUAL INPUT (soil sensor not connected yet)
# ------------------------------------------------------------
SOIL_HUMIDITY = 40.0  # % (change manually)

# ------------------------------------------------------------
# GREEN DETECTION (HSV)
# ------------------------------------------------------------
GREEN_LOWER = np.array([21, 26, 26])
GREEN_UPPER = np.array([95, 255, 255])

# ------------------------------------------------------------
# WATER PREDICTION FORMULA
# ------------------------------------------------------------
def predict_water(humidity, greenery):
    return (
        261.83
        - humidity * 3.13314695
        + greenery * 2.13997997
    )

# ------------------------------------------------------------
# CAMERA CAPTURE (NO SAVING)
# ------------------------------------------------------------
def capture_frame():
    picam2 = Picamera2()
    picam2.configure(
        picam2.create_preview_configuration(
            main={"format": "RGB888", "size": (640, 480)}
        )
    )
    picam2.start()
    time.sleep(2)  # camera warm-up
    frame = picam2.capture_array()
    picam2.stop()
    return frame

# ------------------------------------------------------------
# GREENERY ANALYSIS
# ------------------------------------------------------------
def analyze_greenery(image_rgb):
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

    green_mask = cv2.inRange(hsv, GREEN_LOWER, GREEN_UPPER)

    total_pixels = image_rgb.shape[0] * image_rgb.shape[1]
    green_pixels = np.count_nonzero(green_mask)

    green_percentage = (green_pixels / total_pixels) * 100
    return green_percentage, green_mask

# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
if __name__ == "__main__":
    print("📷 Capturing image from Pi Camera...")
    image = capture_frame()

    print("🌱 Analyzing greenery...")
    greenery_percent, green_mask = analyze_greenery(image)

    predicted_water = predict_water(
        humidity=SOIL_HUMIDITY,
        greenery=greenery_percent
    )

    print("\n--- RESULTS ---")
    print(f"Soil humidity (manual): {SOIL_HUMIDITY:.1f}%")
    print(f"Greenery percentage:   {greenery_percent:.2f}%")
    print(f"Predicted water value: {predicted_water:.2f}")

    # --------------------------------------------------------
    # VISUALIZATION
    # --------------------------------------------------------
    overlay = image.copy()
    overlay[green_mask > 0] = [0, 255, 0]
    overlay = cv2.addWeighted(image, 0.7, overlay, 0.3, 0)

    plt.figure(figsize=(12, 4))
    plt.suptitle(
        f"Greenery: {greenery_percent:.2f}% | "
        f"Soil: {SOIL_HUMIDITY:.1f}% | "
        f"Water: {predicted_water:.2f}"
    )

    plt.subplot(1, 3, 1)
    plt.title("Captured Image")
    plt.imshow(image)
    plt.axis("off")

    plt.subplot(1, 3, 2)
    plt.title("Green Mask")
    plt.imshow(green_mask, cmap="gray")
    plt.axis("off")

    plt.subplot(1, 3, 3)
    plt.title("Green Overlay")
    plt.imshow(overlay)
    plt.axis("off")

    plt.tight_layout()
    plt.show()
