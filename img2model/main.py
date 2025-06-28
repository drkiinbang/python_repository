# main_multi.py

import os
import json
from multi_photo_pipeline import load_image_sequence, match_between_images, refine_with_model_all_images
from main import load_initial_eop
from tkinter import filedialog, Tk

def ask_file(title, filetypes):
    root = Tk(); root.withdraw()
    path = filedialog.askopenfilename(title=title, filetypes=filetypes)
    root.destroy()
    return path

def ask_directory(title):
    root = Tk(); root.withdraw()
    path = filedialog.askdirectory(title=title)
    root.destroy()
    return path

if __name__ == '__main__':
    model_path = ask_file("3D 모델 OBJ 파일 선택", [("OBJ files", "*.obj")])
    image_dir = ask_directory("이미지 폴더 선택")
    eop_dir = ask_directory("EOP 텍스트 폴더 선택")
    intrinsics_path = ask_file("카메라 내부 파라미터 JSON 선택", [("JSON files", "*.json")])

    images, paths = load_image_sequence(image_dir)
    eops = [load_initial_eop(os.path.join(eop_dir, os.path.splitext(os.path.basename(p))[0] + ".txt")) for p in paths]

    with open(intrinsics_path, 'r') as f:
        intrinsics = json.load(f)

    print("[1] 모델-사진 정합 시작")
    refined_poses = refine_with_model_all_images(model_path, images, eops, intrinsics)

    print("[2] 인접 이미지 정합 시작")
    image_matches = match_between_images(images)

    print("[✓] 전체 처리 완료")