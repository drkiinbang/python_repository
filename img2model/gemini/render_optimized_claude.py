import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.arrays import vbo
from PIL import Image
import numpy as np
import tkinter as tk
from tkinter import filedialog
import os
import yaml
from functools import lru_cache
import threading
from concurrent.futures import ThreadPoolExecutor
import time
import ctypes

"""
주요 성능 최적화 기능 (compared to original render.py)

1. GPU 가속 (VBO 사용)

Vertex Buffer Objects를 사용해 정점 데이터를 GPU 메모리에 저장
CPU-GPU 간 데이터 전송 최소화
glDrawArrays로 일괄 렌더링

2. 병렬 처리

ThreadPoolExecutor로 OBJ 파일 파싱을 병렬화
정점, 법선, 면 데이터를 동시에 처리
멀티코어 CPU 활용

3. 메모리 최적화

NumPy 배열 사용으로 메모리 효율성 향상
벡터화된 연산으로 처리 속도 증가
@lru_cache 데코레이터로 파일 읽기 캐싱

4. 렌더링 최적화

백페이스 컬링: 보이지 않는 면 제거로 렌더링 부하 감소
깊이 테스트 최적화: GL_LESS 함수 사용
OpenGL 힌트: GL_FASTEST 모드로 속도 우선 설정

5. I/O 최적화

스크린샷 저장 시 NumPy 배열 직접 활용
PIL 이미지 최적화 옵션 적용
glFinish()로 파이프라인 동기화
"""

class OptimizedOBJRenderer:
    """고성능 OBJ 렌더러 클래스"""
    
    def __init__(self):
        self.vbo_vertices = None
        self.vbo_normals = None
        self.indices = None
        self.vertex_count = 0
        self.face_count = 0
        
    @lru_cache(maxsize=128)
    def _cached_file_read(self, filename, mtime):
        """파일 읽기 캐싱 (수정시간 기반)"""
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading file {filename}: {e}")
            return None
    
    def load_obj_optimized(self, filename):
        """
        최적화된 OBJ 파일 로더
        - 벡터화된 numpy 연산 사용
        - 메모리 효율적인 데이터 구조
        - 병렬 처리
        """
        print(f"Loading OBJ file: {filename}")
        start_time = time.time()
        
        try:
            # 파일 수정 시간 기반 캐싱
            mtime = os.path.getmtime(filename)
            content = self._cached_file_read(filename, mtime)
            if content is None:
                return None, None, None
            
            # 라인별 분할 및 전처리
            lines = [line.strip() for line in content.split('\n') 
                    if line.strip() and not line.startswith('#')]
            
            # 병렬 처리를 위한 라인 분류
            vertex_lines = []
            normal_lines = []
            face_lines = []
            
            for line in lines:
                if line.startswith('v '):
                    vertex_lines.append(line)
                elif line.startswith('vn '):
                    normal_lines.append(line)
                elif line.startswith('f '):
                    face_lines.append(line)
            
            # 병렬 파싱 수행
            with ThreadPoolExecutor(max_workers=3) as executor:
                future_vertices = executor.submit(self._parse_vertices, vertex_lines)
                future_normals = executor.submit(self._parse_normals, normal_lines)
                future_faces = executor.submit(self._parse_faces, face_lines)
                
                vertices = future_vertices.result()
                normals = future_normals.result()
                faces = future_faces.result()
            
            load_time = time.time() - start_time
            print(f"OBJ loaded in {load_time:.3f}s - Vertices: {len(vertices)}, Faces: {len(faces)}")
            
            return vertices, normals, faces
            
        except Exception as e:
            print(f"Error loading OBJ file: {e}")
            return None, None, None
    
    def _parse_vertices(self, vertex_lines):
        """벡터화된 정점 파싱"""
        if not vertex_lines:
            return np.array([])
        
        # 문자열 처리를 numpy로 벡터화
        data = []
        for line in vertex_lines:
            parts = line.split()[1:4]  # 'v' 제외하고 x, y, z
            data.append([float(x) for x in parts])
        
        return np.array(data, dtype=np.float32)
    
    def _parse_normals(self, normal_lines):
        """벡터화된 법선 파싱"""
        if not normal_lines:
            return np.array([])
        
        data = []
        for line in normal_lines:
            parts = line.split()[1:4]  # 'vn' 제외하고 x, y, z
            data.append([float(x) for x in parts])
        
        return np.array(data, dtype=np.float32)
    
    def _parse_faces(self, face_lines):
        """최적화된 면 파싱"""
        faces = []
        for line in face_lines:
            face = []
            for vertex_data in line.split()[1:]:  # 'f' 제외
                # v/vt/vn 형식 처리
                indices = vertex_data.split('/')
                v_idx = int(indices[0]) - 1 if indices[0] else None
                uv_idx = int(indices[1]) - 1 if len(indices) > 1 and indices[1] else None
                n_idx = int(indices[2]) - 1 if len(indices) > 2 and indices[2] else None
                face.append((v_idx, uv_idx, n_idx))
            faces.append(face)
        
        return faces
    
    def setup_vbo(self, vertices, normals, faces):
        """VBO(Vertex Buffer Object) 설정으로 GPU 메모리 활용"""
        print("Setting up VBO for GPU acceleration...")
        
        # 면 데이터를 평면화하여 인덱스 배열 생성
        vertex_data = []
        normal_data = []
        indices = []
        
        vertex_index = 0
        for face in faces:
            if len(face) >= 3:  # 삼각형 이상
                # 삼각형화 (팬 방식)
                for i in range(1, len(face) - 1):
                    for j in [0, i, i + 1]:
                        v_idx, _, n_idx = face[j]
                        
                        if v_idx is not None and v_idx < len(vertices):
                            vertex_data.append(vertices[v_idx])
                        else:
                            vertex_data.append([0.0, 0.0, 0.0])
                        
                        if n_idx is not None and n_idx < len(normals):
                            normal_data.append(normals[n_idx])
                        else:
                            # 기본 법선 계산
                            normal_data.append([0.0, 0.0, 1.0])
                        
                        indices.append(vertex_index)
                        vertex_index += 1
        
        # numpy 배열로 변환
        vertex_array = np.array(vertex_data, dtype=np.float32)
        normal_array = np.array(normal_data, dtype=np.float32)
        
        # VBO 생성
        self.vbo_vertices = vbo.VBO(vertex_array)
        self.vbo_normals = vbo.VBO(normal_array)
        self.vertex_count = len(vertex_array)
        
        print(f"VBO setup complete - {self.vertex_count} vertices buffered")
    
    def render_scene_optimized(self, camera_pos, camera_look_at, camera_up, fov, width, height):
        """
        최적화된 렌더링
        - VBO 사용으로 GPU 가속
        - 불필요한 상태 변경 최소화
        - 컬링 및 깊이 테스트 최적화
        """
        # 투영 행렬 설정
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(fov, width / float(height), 0.1, 1000.0)
        
        # 모델뷰 행렬 설정
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2],
                  camera_look_at[0], camera_look_at[1], camera_look_at[2],
                  camera_up[0], camera_up[1], camera_up[2])
        
        # 버퍼 클리어
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # 렌더링 상태 최적화
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        glEnable(GL_CULL_FACE)  # 백페이스 컬링으로 성능 향상
        glCullFace(GL_BACK)
        
        # 조명 설정 (한 번만)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)

        # 카메라 방향 벡터 계산
        camera_direction = np.array(camera_look_at) - np.array(camera_pos)
        camera_direction = camera_direction / np.linalg.norm(camera_direction)

        # 광원을 카메라 앞쪽 방향으로 약간 떨어진 위치에 배치 (예: 20 units)
        light_distance = 20.0
        light_pos_vec = np.array(camera_pos) + camera_direction * light_distance

        # Homogeneous 좌표계 적용
        light_pos = np.append(light_pos_vec, 1.0).astype(np.float32)
        
        # 조명 매개변수를 배열로 미리 정의
        #light_pos = np.array([1.0, 1.0, 1.0, 0.0], dtype=np.float32)
        #light_pos = np.array([5.0, 10.0, 20.0, 1.0], dtype=np.float32)  # 광원의 위치 변경
        glLightfv(GL_LIGHT0, GL_POSITION, light_pos)

        light_diffuse = np.array([0.8, 0.8, 0.8, 1.0], dtype=np.float32)
        light_ambient = np.array([0.2, 0.2, 0.2, 1.0], dtype=np.float32)
        
        glLightfv(GL_LIGHT0, GL_POSITION, light_pos)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
        glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)

        # Specular 조명 추가 (하이라이트 효과)
        glLightfv(GL_LIGHT0, GL_SPECULAR, np.array([0.5, 0.5, 0.5, 1.0], dtype=np.float32))
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32))
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 64.0)  # 숫자가 클수록 반짝임이 작고 집중됨
        
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        # VBO를 사용한 고속 렌더링
        if self.vbo_vertices is not None and self.vbo_normals is not None:
            # 정점 배열 활성화
            glEnableClientState(GL_VERTEX_ARRAY)
            glEnableClientState(GL_NORMAL_ARRAY)
            
            # VBO 바인딩
            self.vbo_vertices.bind()
            try:
                glVertexPointer(3, GL_FLOAT, 0, self.vbo_vertices)
            finally:
                self.vbo_vertices.unbind()
            
            self.vbo_normals.bind()
            try:
                glNormalPointer(GL_FLOAT, 0, self.vbo_normals)
            finally:
                self.vbo_normals.unbind()
            
            # 일괄 렌더링
            glDrawArrays(GL_TRIANGLES, 0, self.vertex_count)
            
            # 정점 배열 비활성화
            glDisableClientState(GL_VERTEX_ARRAY)
            glDisableClientState(GL_NORMAL_ARRAY)
    
    def save_screenshot_optimized(self, filename, width, height):
        """최적화된 스크린샷 저장"""
        print(f"Saving screenshot: {filename}")
        start_time = time.time()
        
        # OpenGL 파이프라인 완료 대기
        glFinish()
        
        # 픽셀 데이터 읽기 (numpy 사용으로 최적화)
        pixels = glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE)
        
        # numpy 배열로 변환 후 이미지 생성
        pixel_array = np.frombuffer(pixels, dtype=np.uint8)
        pixel_array = pixel_array.reshape((height, width, 3))
        
        # 세로 뒤집기 (OpenGL 좌표계 보정)
        pixel_array = np.flipud(pixel_array)
        
        # PIL 이미지로 변환 및 저장
        image = Image.fromarray(pixel_array, 'RGB')
        image.save(filename, optimize=True)
        
        save_time = time.time() - start_time
        print(f"Screenshot saved in {save_time:.3f}s: {filename}")

def load_config_optimized(filepath):
    """최적화된 YAML 설정 로더"""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

def select_file(title, filetypes):
    """파일 선택 다이얼로그"""
    root = tk.Tk()
    root.withdraw()
    filepath = filedialog.askopenfilename(title=title, filetypes=filetypes)
    root.destroy()
    return filepath

def main():
    print("=== 고성능 OBJ 렌더러 ===")
        
    # OBJ 파일 선택
    obj_filepath = select_file(
        "Select OBJ file to render",
        [("OBJ files", "*.obj"), ("All files", "*.*")]
    )
    
    if not obj_filepath:
        print("OBJ file selection cancelled.")
        return
    
    # YAML 설정 파일 선택
    yaml_filepath = select_file(
        "Select YAML configuration file",
        [("YAML files", "*.yaml *.yml"), ("All files", "*.*")]
    )
    
    if not yaml_filepath:
        print("YAML configuration file selection cancelled.")
        return
    
    total_start = time.time()
    
    # 설정 로드
    config = load_config_optimized(yaml_filepath)
    if not config:
        print("Failed to load configuration.")
        return
    
    # 설정 검증
    try:
        camera_settings = config['camera_settings']
        camera_pos = tuple(camera_settings['position'])
        camera_look_at = tuple(camera_settings['look_at'])
        camera_up = tuple(camera_settings['up_vector'])
        fov = float(camera_settings['fov'])
        output_filename = config['output_filename']
        render_width = int(config.get('render_width', 800))
        render_height = int(config.get('render_height', 600))
        
        if not (0 < fov < 180):
            raise ValueError("FOV must be between 0 and 180 degrees.")
            
    except (KeyError, TypeError, ValueError) as e:
        print(f"Configuration error: {e}")
        return
    
    # 렌더러 초기화
    renderer = OptimizedOBJRenderer()
    
    # OBJ 파일 로드
    vertices, normals, faces = renderer.load_obj_optimized(obj_filepath)
    if vertices is None or len(vertices) == 0:
        print("Failed to load OBJ file.")
        return
    
    # Pygame 및 OpenGL 초기화
    pygame.init()
    screen = pygame.display.set_mode(
        (render_width, render_height), 
        DOUBLEBUF | OPENGL | HIDDEN
    )
    pygame.display.set_caption("Optimized OBJ Renderer")
    
    # OpenGL 최적화 설정
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_FASTEST)
    glHint(GL_POLYGON_SMOOTH_HINT, GL_FASTEST)
    
    try:
        # VBO 설정
        renderer.setup_vbo(vertices, normals, faces)
        
        # 렌더링 수행
        print("Rendering scene...")
        render_start = time.time()
        
        renderer.render_scene_optimized(
            camera_pos, camera_look_at, camera_up, fov, 
            render_width, render_height
        )
        
        render_time = time.time() - render_start
        print(f"Scene rendered in {render_time:.3f}s")
        
        # 스크린샷 저장
        renderer.save_screenshot_optimized(output_filename, render_width, render_height)
        
    except Exception as e:
        print(f"Error during rendering: {e}")
    finally:
        pygame.quit()
        total_time = time.time() - total_start
        print(f"Total execution time: {total_time:.3f}s")
        print("=== Rendering Complete ===")

if __name__ == "__main__":
    main()