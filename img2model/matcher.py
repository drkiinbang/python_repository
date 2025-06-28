# matcher.py

import torch
from superpoint_superglue_deployment.inference import Matching
from config import SAVE_DEBUG, result_root
import cv2
import numpy as np
import os

class FeatureMatcher:
    def __init__(self, device='cuda'):
        self.matcher = Matching(device=device)

    def match(self, img0, img1, tag="frame"):
        gray0 = cv2.cvtColor(img0, cv2.COLOR_BGR2GRAY) if img0.ndim == 3 else img0
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY) if img1.ndim == 3 else img1

        data = self.matcher({'image0': gray0, 'image1': gray1})

        if SAVE_DEBUG:
            matched_img = self.draw_matches(gray0, gray1, data, tag)
            cv2.imwrite(os.path.join(result_root, f"matches_{tag}.png"), matched_img)

        return data

    def draw_matches(self, img0, img1, data, tag=""):
        mk0 = data['keypoints0'][data['matches'][:,0]]
        mk1 = data['keypoints1'][data['matches'][:,1]]
        match_vis = np.hstack([img0, img1])
        vis = cv2.cvtColor(match_vis, cv2.COLOR_GRAY2BGR)
        for p0, p1 in zip(mk0, mk1):
            p0 = tuple(np.round(p0).astype(int))
            p1 = tuple(np.round(p1).astype(int) + [img0.shape[1], 0])
            cv2.line(vis, p0, p1, (0,255,0), 1)
            cv2.circle(vis, p0, 2, (0,0,255), -1)
            cv2.circle(vis, p1, 2, (255,0,0), -1)
        return vis