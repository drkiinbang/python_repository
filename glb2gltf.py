#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GLB -> GLTF 변환 스크립트
- 기본: .gltf(JSON) + .bin + 텍스처 파일로 분리 저장
- 입력: 단일 파일 또는 폴더(폴더는 재귀적으로 .glb 검색)
- 우선순위: trimesh -> (실패 시) pygltflib
"""

import argparse
import os
import sys
from pathlib import Path

def convert_with_trimesh(src: Path, dst_dir: Path, basename: str) -> bool:
    try:
        import trimesh  # type: ignore
        # GLB를 장면으로 강제 로드 (단일 mesh도 scene로 포장)
        scene = trimesh.load(src.as_posix(), force='scene')
        out_path = (dst_dir / f"{basename}.gltf").as_posix()
        # trimesh는 out_path 확장자로 타입을 판단; .gltf면 분리 형태로 저장
        scene.export(out_path)
        return True
    except Exception as e:
        print(f"[trimesh] 변환 실패: {src.name} -> {e}")
        return False

def convert_with_pygltflib(src: Path, dst_dir: Path, basename: str) -> bool:
    """
    pygltflib를 이용한 대안 경로.
    주의: 확장/텍스처 포맷에 따라 일부 케이스에서는 완벽히 동작하지 않을 수 있음.
    """
    try:
        from pygltflib import GLTF2, BufferFormat, ImageFormat  # type: ignore
        gltf = GLTF2().load(src.as_posix())

        # 출력 리소스 디렉터리 준비
        dst_dir.mkdir(parents=True, exist_ok=True)

        # 버퍼/이미지를 외부 파일로 분리
        # (pygltflib는 convert_* 호출 뒤 save를 하면 지정한 디렉토리에 리소스가 풀림)
        gltf.convert_buffers(BufferFormat.BINARYFILE)
        gltf.convert_images(ImageFormat.FILE)

        out_path = (dst_dir / f"{basename}.gltf").as_posix()
        gltf.save(out_path)
        return True
    except Exception as e:
        print(f"[pygltflib] 변환 실패: {src.name} -> {e}")
        return False

def is_glb(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() == ".glb"

def find_glb_files(path: Path):
    if path.is_file() and is_glb(path):
        yield path
    elif path.is_dir():
        for p in path.rglob("*.glb"):
            if p.is_file():
                yield p

def unique_basename(dst_dir: Path, base: str) -> str:
    """동일 파일명 존재 시 _001 식으로 증분"""
    candidate = base
    i = 1
    while True:
        gltf_path = dst_dir / f"{candidate}.gltf"
        bin_path = dst_dir / f"{candidate}.bin"
        if not gltf_path.exists() and not bin_path.exists():
            return candidate
        i += 1
        candidate = f"{base}_{i:03d}"

def convert_one(src: Path, outdir: Path, keep_name: bool) -> bool:
    if keep_name:
        basename = src.stem
    else:
        basename = unique_basename(outdir, src.stem)

    # 1차: trimesh 시도
    ok = convert_with_trimesh(src, outdir, basename)
    if ok:
        print(f"[OK] {src.name} → {basename}.gltf (trimesh)")
        return True

    # 2차: pygltflib 시도
    ok = convert_with_pygltflib(src, outdir, basename)
    if ok:
        print(f"[OK] {src.name} → {basename}.gltf (pygltflib)")
        return True

    print(f"[FAIL] 변환 실패: {src}")
    return False

def main():
    parser = argparse.ArgumentParser(
        description="Convert GLB files to GLTF (.gltf + .bin + textures)"
    )
    parser.add_argument(
        "input",
        help="입력 경로(파일 또는 폴더). 폴더면 재귀적으로 .glb를 모두 변환."
    )
    parser.add_argument(
        "-o", "--outdir",
        default=None,
        help="출력 폴더(기본: 입력 파일/폴더 기준 하위 'gltf_out')"
    )
    parser.add_argument(
        "--keep-name",
        action="store_true",
        help="같은 이름의 .gltf가 있어도 덮어쓰지 않음(기본은 중복 시 _001 등 증분)."
    )
    args = parser.parse_args()

    in_path = Path(args.input).expanduser().resolve()
    if not in_path.exists():
        print(f"입력 경로를 찾을 수 없습니다: {in_path}")
        sys.exit(1)

    outdir = Path(args.outdir).expanduser().resolve() if args.outdir else (in_path if in_path.is_dir() else in_path.parent) / "gltf_out"
    outdir.mkdir(parents=True, exist_ok=True)

    glb_list = list(find_glb_files(in_path))
    if not glb_list:
        print("변환할 .glb 파일이 없습니다.")
        sys.exit(1)

    total = 0
    success = 0
    for src in glb_list:
        total += 1
        ok = convert_one(src, outdir, keep_name=args.keep_name)
        if ok:
            success += 1

    print(f"\n완료: {success}/{total} 파일 변환 성공")
    if success < total:
        print("일부 파일은 확장/포맷 이슈로 실패할 수 있습니다. 최신 trimesh/pygltflib 버전을 사용해 보세요.")

if __name__ == "__main__":
    main()
