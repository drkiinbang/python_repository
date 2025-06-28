# visualizer.py

import cv2
import numpy as np
import os
from config import result_root

def overlay_points(image, points, color=(0,255,0), radius=3):
    for pt in points:
        cv2.circle(image, tuple(np.round(pt).astype(int)), radius, color, -1)
    return image

def draw_projected_points(image, pts3d, rvec, tvec, K):
    pts2d, _ = cv2.projectPoints(pts3d, rvec, tvec, K, None)
    for p in pts2d.reshape(-1,2):
        cv2.circle(image, tuple(np.round(p).astype(int)), 3, (255,0,0), -1)
    return image

def save_image(name, image):
    path = os.path.join(result_root, name)
    cv2.imwrite(path, image)