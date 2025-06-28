# transform.py

import numpy as np
import cv2
from config import CAMERA_INTRINSIC, TOL_ROT_RAD, TOL_TRANS_M, SAVE_DEBUG, result_root
import os

def depth_to_3d(u, v, z, intr):
    fx, fy = intr[0, 0], intr[1, 1]
    cx, cy = intr[0, 2], intr[1, 2]
    X = (u - cx) * z / fx
    Y = (v - cy) * z / fy
    return np.stack([X, Y, z], axis=-1)

def get_intrinsic_matrix():
    return np.array([
        [CAMERA_INTRINSIC['fx'], 0, CAMERA_INTRINSIC['cx']],
        [0, CAMERA_INTRINSIC['fy'], CAMERA_INTRINSIC['cy']],
        [0, 0, 1]
    ], dtype=np.float32)

def estimate_pose(depth, matches):
    u = matches['keypoints0'][:,0].astype(int)
    v = matches['keypoints0'][:,1].astype(int)
    z = depth[v, u]

    valid = z > 0.1
    u, v, z = u[valid], v[valid], z[valid]
    pts3d = depth_to_3d(u, v, z, get_intrinsic_matrix())
    pts2d = matches['keypoints1'][valid].astype(np.float32)

    if len(pts3d) < 6:
        return None, None, None

    ret, rvec, tvec, inliers = cv2.solvePnPRansac(
        pts3d.astype(np.float32),
        pts2d.astype(np.float32),
        get_intrinsic_matrix(), None,
        flags=cv2.SOLVEPNP_ITERATIVE
    )

    if not ret:
        return None, None, None

    if SAVE_DEBUG:
        np.savetxt(os.path.join(result_root, "pnp_inliers.txt"), inliers)

    return rvec, tvec, inliers

def compute_errors(rvec_old, tvec_old, rvec_new, tvec_new):
    rot_err = np.linalg.norm(rvec_old - rvec_new)
    trans_err = np.linalg.norm(tvec_old - tvec_new)
    return rot_err, trans_err

def has_converged(rot_err, trans_err):
    return rot_err < TOL_ROT_RAD and trans_err < TOL_TRANS_M