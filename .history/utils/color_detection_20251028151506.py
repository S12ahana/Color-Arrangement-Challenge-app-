import cv2
import numpy as np

def find_centroid(mask):
    """Find the centroid (x, y) of the largest contour in a binary mask."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        c = max(contours, key=cv2.contourArea)
        M = cv2.moments(c)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            return (cx, cy)
    return None

def detect_colors(frame):
    """Detect red, blue, green, yellow, pink, and violet objects and return their centroid positions."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

  
    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 120, 70])
    upper_red2 = np.array([180, 255, 255])

   
    lower_blue = np.array([100, 150, 0])
    upper_blue = np.array([140, 255, 255])

    
    lower_green = np.array([40, 70, 70])
    upper_green = np.array([80, 255, 255])

    # Yellow
    lower_yellow = np.array([20, 100, 100])
    upper_yellow = np.array([30, 255, 255])

    # Pink (Magenta)
    lower_pink = np.array([160, 100, 100])
    upper_pink = np.array([170, 255, 255])

    # Violet (Purple)
    lower_violet = np.array([130, 100, 100])
    upper_violet = np.array([150, 255, 255])

    # --- Create masks ---
    mask_red = cv2.inRange(hsv, lower_red1, upper_red1) | cv2.inRange(hsv, lower_red2, upper_red2)
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
    mask_green = cv2.inRange(hsv, lower_green, upper_green)
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
    mask_pink = cv2.inRange(hsv, lower_pink, upper_pink)
    mask_violet = cv2.inRange(hsv, lower_violet, upper_violet)

    # --- Find centroids ---
    positions = {
        "Red": find_centroid(mask_red),
        "Blue": find_centroid(mask_blue),
        "Green": find_centroid(mask_green),
        "Yellow": find_centroid(mask_yellow),
        "Pink": find_centroid(mask_pink),
        "Violet": find_centroid(mask_violet)
    }

    return positions
