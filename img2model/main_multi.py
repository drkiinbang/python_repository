# main_multi.py

import argparse
import os
import json
from multi_photo_pipeline import load_image_sequence, match_between_images, refine_with_model_all_images
from main import load_initial_eop

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True)
    parser.add_argument('--image_dir', required=True)
    parser.add_argument('--eop_dir', required=True)
    parser.add_argument('--intrinsics', required=True)
    args = parser.parse_args()

    images, paths = load_image_sequence(args.image_dir)
    eops = [load_initial_eop(os.path.join(args.eop_dir, os.path.splitext(os.path.basename(p))[0] + ".txt")) for p in paths]

    with open(args.intrinsics, 'r') as f:
        intrinsics = json.load(f)

    print("[1] 모델-사진 정합 시작")
    refined_poses = refine_with_model_all_images(args.model, images, eops, intrinsics)

    print("[2] 인접 이미지 정합 시작")
    image_matches = match_between_images(images)

    print("[✓] 전체 처리 완료")