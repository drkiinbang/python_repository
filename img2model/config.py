# config.py

import os

# 기본 경로 설정
data_root = "./data"
result_root = "./results"
os.makedirs(result_root, exist_ok=True)

# 렌더링 설정
RENDER_WIDTH = 1280
RENDER_HEIGHT = 720
FOV_DEG = 60.0

# 카메라 내부 파라미터 (예시)
CAMERA_INTRINSIC = {
    'fx': 2000.0,
    'fy': 2000.0,
    'cx': RENDER_WIDTH / 2,
    'cy': RENDER_HEIGHT / 2,
    'width': RENDER_WIDTH,
    'height': RENDER_HEIGHT
}

# 반복 정합 수렴 조건
TOL_ROT_RAD = 0.01   # 회전 오차(rad)
TOL_TRANS_M = 0.01   # 위치 오차(m)

# 중간결과 저장 여부
SAVE_DEBUG = True
DEBUG_STEP = "all"  # render-only, match-only, pnp-only, all