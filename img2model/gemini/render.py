import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from PIL import Image
import numpy as np
import tkinter as tk
from tkinter import filedialog
import os

def load_obj(filename):
    """
    OBJ 파일을 파싱하여 정점, 노멀, 면 정보를 로드합니다.
    (간단한 구현으로, UV 좌표나 복잡한 OBJ 특성은 다루지 않습니다.)
    """
    vertices = []
    normals = []
    faces = []

    try:
        # 여기에 encoding='utf-8'을 추가합니다.
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                if line.startswith('#'):
                    continue
                values = line.split()
                if not values:
                    continue

                if values[0] == 'v':
                    vertices.append([float(x) for x in values[1:4]])
                elif values[0] == 'vn':
                    normals.append([float(x) for x in values[1:4]])
                elif values[0] == 'f':
                    face = []
                    for v in values[1:]:
                        w = v.split('/')
                        # OBJ 인덱스는 1부터 시작하므로 -1
                        face.append(tuple(int(x) - 1 if x else None for x in w))
                    faces.append(face)
    except FileNotFoundError:
        print(f"오류: '{filename}' 파일을 찾을 수 없습니다.")
        return None, None, None
    except Exception as e:
        print(f"OBJ 파일 로드 중 오류 발생: {e}")
        return None, None, None
        
    return vertices, normals, faces

# 나머지 코드는 이전과 동일합니다.
# ... (render_scene, save_screenshot, select_obj_file, main 함수 등)

def render_scene(vertices, normals, faces, camera_pos, camera_look_at, camera_up, fov, width, height):
    """
    OpenGL을 사용하여 씬을 렌더링합니다.
    """
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fov, (width / float(height)), 0.1, 1000.0)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2],
              camera_look_at[0], camera_look_at[1], camera_look_at[2],
              camera_up[0], camera_up[1], camera_up[2])

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, (1, 1, 1, 0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.8, 0.8, 0.8, 1))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1))
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    glBegin(GL_TRIANGLES)
    for face in faces:
        for i, (v_idx, uv_idx, n_idx) in enumerate(face):
            if n_idx is not None and n_idx < len(normals):
                glNormal3fv(normals[n_idx])
            if v_idx is not None and v_idx < len(vertices):
                glVertex3fv(vertices[v_idx])
    glEnd()

def save_screenshot(filename, width, height):
    """
    현재 OpenGL 버퍼의 내용을 이미지 파일로 저장합니다.
    """
    pixels = glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE)
    image = Image.frombytes("RGB", (width, height), pixels)
    image = image.transpose(Image.FLIP_TOP_BOTTOM)  # OpenGL 텍스처는 뒤집혀 있으므로 뒤집어줍니다.
    image.save(filename)
    print(f"렌더링된 이미지를 '{filename}'으로 저장했습니다.")

def select_obj_file():
    """
    파일 다이얼로그를 열어 OBJ 파일을 선택하게 합니다.
    """
    root = tk.Tk()
    root.withdraw()  # Tkinter 기본 창 숨기기

    file_path = filedialog.askopenfilename(
        title="렌더링할 OBJ 파일 선택",
        filetypes=[("OBJ files", "*.obj"), ("All files", "*.*")]
    )
    root.destroy() # 다이얼로그 닫은 후 Tkinter 루트 창 파괴
    return file_path

def main():
    obj_filepath = select_obj_file()

    if not obj_filepath:
        print("OBJ 파일 선택을 취소했습니다. 프로그램을 종료합니다.")
        return

    print(f"선택된 OBJ 파일: {obj_filepath}")

    vertices, normals, faces = load_obj(obj_filepath)
    if vertices is None or not vertices or not faces:
        print("OBJ 파일 로드에 실패했거나 유효한 정보가 없습니다.")
        return
    print(f"{os.path.basename(obj_filepath)} 로드 성공. 정점: {len(vertices)}, 면: {len(faces)}")

    # 사용자 입력
    print("\n카메라 설정을 입력하세요:")
    try:
        cam_x = float(input("카메라 X 위치 (예: 0): "))
        cam_y = float(input("카메라 Y 위치 (예: 0): "))
        cam_z = float(input("카메라 Z 위치 (예: 5): "))
        camera_pos = (cam_x, cam_y, cam_z)

        look_x = float(input("카메라가 바라볼 X 위치 (예: 0): "))
        look_y = float(input("카메라가 바라볼 Y 위치 (예: 0): "))
        look_z = float(input("카메라가 바라볼 Z 위치 (예: 0): "))
        camera_look_at = (look_x, look_y, look_z)

        up_x = float(input("카메라 업 벡터 X (일반적으로 0): "))
        up_y = float(input("카메라 업 벡터 Y (일반적으로 1): "))
        up_z = float(input("카메라 업 벡터 Z (일반적으로 0): "))
        camera_up = (up_x, up_y, up_z)

        fov = float(input("시야각 (FOV, degrees, 예: 60): "))
        if not (0 < fov < 180):
            raise ValueError("시야각은 0에서 180 사이여야 합니다.")

        output_filename = input("저장할 이미지 파일 이름 (예: output.png): ")
        if not output_filename:
            print("파일 이름을 입력해야 합니다. 프로그램을 종료합니다.")
            return

    except ValueError as e:
        print(f"입력 오류: {e}")
        return

    # 렌더링 설정
    render_width, render_height = 800, 600

    pygame.init()
    # 파이게임 디스플레이를 초기화하지 않고, OpenGL 컨텍스트만 생성
    screen = pygame.display.set_mode((render_width, render_height), DOUBLEBUF | OPENGL | HIDDEN)
    pygame.display.set_caption("OBJ Renderer (Hidden)")

    try:
        # 렌더링
        render_scene(vertices, normals, faces, camera_pos, camera_look_at, camera_up, fov, render_width, render_height)

        # 스크린샷 저장
        save_screenshot(output_filename, render_width, render_height)
    except Exception as e:
        print(f"렌더링 또는 저장 중 오류 발생: {e}")
    finally:
        pygame.quit()
        print("프로그램 종료.")

if __name__ == "__main__":
    main()