# multi_photo_pipeline.py

import os
import cv2
import numpy as np
from pipeline import EOPRefinementPipeline
from matcher import FeatureMatcher
from transform import get_intrinsic_matrix_from_dict
from tkinter import filedialog, Tk

def ask_directory(title):
    root = Tk(); root.withdraw()
    path = filedialog.askdirectory(title=title)
    root.destroy()
    return path

def load_image_sequence(folder):
    image_paths = sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.png'))])
    return [cv2.imread(p) for p in image_paths], image_paths

def match_between_images(image_list):
    matcher = FeatureMatcher()
    matches_between = []
    for i in range(len(image_list) - 1):
        img1, img2 = image_list[i], image_list[i + 1]
        matches = matcher.match(img1, img2, tag=f"seq_{i}_{i+1}")
        matches_between.append(matches)
    return matches_between

def refine_with_model_all_images(model_path, image_list, init_eop_list, intrinsics):
    refined_poses = []
    for i, (img, init_eop) in enumerate(zip(image_list, init_eop_list)):
        rvec, tvec = init_eop
        pipeline = EOPRefinementPipeline(model_path, img, rvec, tvec, intrinsics)
        pipeline.run()
        refined_poses.append((pipeline.rvec, pipeline.tvec))
    return refined_poses