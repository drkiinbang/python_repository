# pipeline.py

import numpy as np
from renderer import Renderer
from matcher import FeatureMatcher
from transform import estimate_pose, compute_errors, has_converged, get_intrinsic_matrix
from visualizer import draw_projected_points, save_image
import cv2
from config import SAVE_DEBUG, DEBUG_STEP

class EOPRefinementPipeline:
    def __init__(self, model_path, frame_img, init_rvec, init_tvec):
        self.renderer = Renderer(model_path)
        self.matcher = FeatureMatcher()
        self.frame = frame_img
        self.rvec = init_rvec
        self.tvec = init_tvec
        self.K = get_intrinsic_matrix()

    def run(self):
        for i in range(10):
            extrinsic = self.compose_extrinsic(self.rvec, self.tvec)
            rgb, depth = self.renderer.render_rgbd(extrinsic)

            if DEBUG_STEP in ["render-only", "all"]:
                save_image(f"rgb_iter{i}.png", rgb)

            matches = self.matcher.match(rgb, self.frame, tag=f"iter{i}")
            if matches['matches'] is None:
                print("[!] 매칭 실패"); break

            rvec_new, tvec_new, inliers = estimate_pose(depth, matches)
            if rvec_new is None: print("[!] PnP 실패"); break

            rot_err, trans_err = compute_errors(self.rvec, self.tvec, rvec_new, tvec_new)
            print(f"[iter {i}] ΔR={rot_err:.4f} rad, ΔT={trans_err:.4f} m")

            if has_converged(rot_err, trans_err):
                print("[✓] 수렴 완료"); break

            self.rvec, self.tvec = rvec_new, tvec_new

            if SAVE_DEBUG and DEBUG_STEP == "all":
                proj_vis = draw_projected_points(self.frame.copy(), matches['keypoints0'], rvec_new, tvec_new, self.K)
                save_image(f"projected_iter{i}.png", proj_vis)

    def compose_extrinsic(self, rvec, tvec):
        R, _ = cv2.Rodrigues(rvec)
        ext = np.eye(4)
        ext[:3,:3] = R
        ext[:3, 3] = tvec.flatten()
        return ext
