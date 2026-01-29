# ============================================================
# pi_green_water_full_filter_viz.py
# Optimized for Darker Greens, High Precision & Fullscreen
# ============================================================

from picamera2 import Picamera2
import cv2
import numpy as np
import time
import random
import sys

# ------------------------------------------------------------
# HSV WAARDES - Strict enough for blue, sensitive to dark green
# ------------------------------------------------------------
GREEN_LOWER = np.array([39, 61, 21])  
GREEN_UPPER = np.array([90, 255, 255])

# ------------------------------------------------------------
# MATH FORMULAS
# ------------------------------------------------------------
def predict_water(humidity, greenery):
    return 261.83 - humidity * 3.13314695 + greenery * 2.13997997

def valve_open_time_ml(V_ml):
    a, b, c = 0.11455309, 36.75567689, 19.817595 - V_ml
    disc = b**2 - 4*a*c
    if disc < 0: return 0.0
    return (-b + np.sqrt(disc)) / (2*a)

# ------------------------------------------------------------
# PIXEL VALIDATION LOGIC
# ------------------------------------------------------------
def is_valid_pixel(y, x, mask, radius=3, threshold=0.75):
    h, w = mask.shape
    y0, y1 = max(0, y - radius), min(h, y + radius + 1)
    x0, x1 = max(0, x - radius), min(w, x + radius + 1)
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
# ANALYSIS & CAPTURE (Safe Sequence)
# ------------------------------------------------------------
def capture_frame():
    picam2 = Picamera2()
    try:
        picam2.configure(picam2.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)}))
        picam2.start()
        time.sleep(1.5) # Sensor warm-up
        frame = picam2.capture_array()
    finally:
        # Crucial: Releases camera hardware even if capture fails
        picam2.stop()
        picam2.close()
    return frame

def analyze_plant(image_rgb):
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    green_mask = cv2.inRange(hsv, GREEN_LOWER, GREEN_UPPER)
    h, w = green_mask.shape
    center_strip = green_mask[:, w // 2 - w // 20 : w // 2 + w // 20]

    top_pixel, bottom_pixel = None, None

    # Detect Bottom
    for y in reversed(range(center_strip.shape[0])):
        xs = np.where(center_strip[y] > 0)[0]
        if len(xs) > 0:
            if is_valid_pixel(y, xs[0], center_strip) and connected_vertically(y, xs[0], center_strip, "up"):
                bottom_pixel = y
                break
        if bottom_pixel is not None: break

    # Detect Top
    for y in range(center_strip.shape[0]):
        xs = np.where(center_strip[y] > 0)[0]
        if len(xs) > 0:
            if is_valid_pixel(y, xs[0], center_strip) and connected_vertically(y, xs[0], center_strip, "down"):
                top_pixel = y
                break
        if top_pixel is not None: break

    plant_height = (bottom_pixel - top_pixel if top_pixel is not None and bottom_pixel is not None else None)
    
    restricted_green_mask = green_mask.copy()
    if plant_height is not None:
        restricted_green_mask[:top_pixel, :] = 0
        restricted_green_mask[bottom_pixel + 1 :, :] = 0

    green_ratio = (np.count_nonzero(restricted_green_mask) / (h * w)) * 100
    return green_ratio, restricted_green_mask, top_pixel, bottom_pixel, plant_height

# ------------------------------------------------------------
# MAIN EXECUTION
# ------------------------------------------------------------
if __name__ == "__main__":
    SOIL_HUMIDITY = round(random.uniform(40.0, 45.0), 1)
    
    print("Capturing...")
    try:
        img_rgb = capture_frame()
    except Exception as e:
        print(f"Error: {e}")
        print("Camera busy. Run 'sudo pkill python' and try again.")
        sys.exit()

    green_ratio, mask, top, bot, height = analyze_plant(img_rgb)
    water_ml = predict_water(SOIL_HUMIDITY, green_ratio)
    v_time = valve_open_time_ml(water_ml)

    # UI PREPARATION
    orig_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    mask_visual = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    mask_visual[mask > 0] = [0, 200, 0] 

    # HUD Overlay Box
    hud = orig_bgr.copy()
    cv2.rectangle(hud, (5, 5), (285, 155), (10, 10, 10), -1) 
    orig_bgr = cv2.addWeighted(hud, 0.75, orig_bgr, 0.25, 0) 

    # Height Lines (drawn across both views)
    if top and bot:
        for v in [orig_bgr, mask_visual]:
            cv2.line(v, (0, top), (640, top), (255, 255, 255), 1, cv2.LINE_AA)
            cv2.line(v, (0, bot), (640, bot), (255, 255, 255), 1, cv2.LINE_AA)

    font = cv2.FONT_HERSHEY_DUPLEX
    stats = [
        (f"SOIL: {SOIL_HUMIDITY}%", (0, 215, 255)),
        (f"PLANT: {green_ratio:.2f}%", (100, 255, 0)),
        (f"WATER: {water_ml:.1f} ml", (255, 160, 60)),
        (f"VALVE: {v_time:.2f} s", (220, 120, 255))
    ]

    for i, (text, color) in enumerate(stats):
        cv2.putText(orig_bgr, text, (15, 45 + (i * 32)), font, 0.7, color, 1, cv2.LINE_AA)

    combined = np.hstack((orig_bgr, mask_visual))
    
    # FULLSCREEN DISPLAY ENGINE
    window_name = "Leafy AI Analysis"
    cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        remaining = max(0, 20 - int(elapsed))
        
        display_frame = combined.copy()
        cv2.putText(display_frame, f"AUTO-CLOSE IN {remaining}s", (10, 465), font, 0.5, (200, 200, 200), 1)
        cv2.putText(display_frame, "PRESS 'Q' TO EXIT", (520, 465), font, 0.5, (0, 0, 255), 1)
        
        cv2.imshow(window_name, display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27 or elapsed > 20:
            break
        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            break

    cv2.destroyAllWindows()
    print("\n[RESET] Terminal ready.")
