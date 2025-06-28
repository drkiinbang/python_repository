import numpy as np
import cv2
import json
from renderer import Renderer
from tkinter import filedialog, Tk
import os
import yaml

def euler_to_rotmat(euler_angles):
    omega, phi, kappa = euler_angles
    Rx = np.array([[1, 0, 0],
                   [0, np.cos(omega), -np.sin(omega)],
                   [0, np.sin(omega), np.cos(omega)]])
    Ry = np.array([[np.cos(phi), 0, np.sin(phi)],
                   [0, 1, 0],
                   [-np.sin(phi), 0, np.cos(phi)]])
    Rz = np.array([[np.cos(kappa), -np.sin(kappa), 0],
                   [np.sin(kappa), np.cos(kappa), 0],
                   [0, 0, 1]])
    return Rz @ Ry @ Rx

def load_initial_eop(path):
    if path.endswith('.yaml') or path.endswith('.yml'):
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
            X = data['X']
            Y = data['Y']
            Z = data['Z']
            omega = np.deg2rad(data['Omega'])
            phi = np.deg2rad(data['Phi'])
            kappa = np.deg2rad(data['Kappa'])
    else:
        with open(path, 'r') as f:
            values = list(map(float, f.read().strip().split()))
            X, Y, Z, omega, phi, kappa = values

    R = euler_to_rotmat([omega, phi, kappa])
    rvec, _ = cv2.Rodrigues(R)
    tvec = np.array([X, Y, Z], dtype=np.float32).reshape(3, 1)
    return rvec, tvec

def compose_extrinsic(rvec, tvec):
    R, _ = cv2.Rodrigues(rvec)
    ext = np.eye(4)
    ext[:3,:3] = R
    ext[:3,3] = tvec.flatten()
    return ext

def load_intrinsics(path):
    with open(path, 'r') as f:
        return json.load(f)

def ask_file(title, filetypes):
    root = Tk(); root.withdraw()
    path = filedialog.askopenfilename(title=title, filetypes=filetypes)
    root.destroy()
    return path

if __name__ == '__main__':
    model_path = ask_file("3D 모델 OBJ 파일 선택", [("OBJ files", "*.obj")])
    eop_path = ask_file("초기 EOP 텍스트 선택", [("Yaml files", "*.yaml")])
    intrinsics_path = ask_file("카메라 내부 파라미터 JSON 선택", [("JSON files", "*.json")])

    rvec, tvec = load_initial_eop(eop_path)
    extrinsic = compose_extrinsic(rvec, tvec)
    intrinsics = load_intrinsics(intrinsics_path)

    renderer = Renderer(model_path, intrinsics)
    rgb, depth = renderer.render_rgbd(extrinsic)
    print("[✓] 렌더링 이미지 생성 완료. 결과는 results/ 디렉토리에 저장됨.")
