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
#from concurrent.futures import ThreadPoolExecutor
import time
import ctypes

"""
✅ 주요 사항 요약
GLSL 셰이더 렌더링:
Vertex Shader (basic.vert)
Fragment Shader (basic.frag)
OpenGL 셰이더 컴파일 및 바인딩 함수:
compile_shader(), create_shader_program()

"""

VERTEX_SHADER_SRC = """
#version 120
attribute vec3 position;
attribute vec3 normal;
varying vec3 frag_normal;

uniform mat4 modelview;
uniform mat4 projection;

void main() {
    frag_normal = normalize(normal);
    gl_Position = projection * modelview * vec4(position, 1.0);
}
"""

FRAGMENT_SHADER_SRC = """
#version 120
varying vec3 frag_normal;

void main() {
    vec3 light_dir = normalize(vec3(0.5, 0.8, 1.0));
    float diff = max(dot(frag_normal, light_dir), 0.0);
    vec3 diffuse = diff * vec3(1.0, 1.0, 1.0);
    vec3 ambient = vec3(0.2, 0.2, 0.2);
    gl_FragColor = vec4(diffuse + ambient, 1.0);
}
"""

def compile_shader(source, shader_type):
    shader = glCreateShader(shader_type)
    glShaderSource(shader, source)
    glCompileShader(shader)
    if glGetShaderiv(shader, GL_COMPILE_STATUS) != GL_TRUE:
        raise RuntimeError(glGetShaderInfoLog(shader))
    return shader

def create_shader_program():
    vertex_shader = compile_shader(VERTEX_SHADER_SRC, GL_VERTEX_SHADER)
    fragment_shader = compile_shader(FRAGMENT_SHADER_SRC, GL_FRAGMENT_SHADER)
    program = glCreateProgram()
    glAttachShader(program, vertex_shader)
    glAttachShader(program, fragment_shader)
    glLinkProgram(program)
    if glGetProgramiv(program, GL_LINK_STATUS) != GL_TRUE:
        raise RuntimeError(glGetProgramInfoLog(program))
    return program


class OptimizedOBJRenderer:
    def __init__(self):
        self.vbo_vertices = None
        self.vbo_normals = None
        self.vertex_count = 0
        self.shader_program = None

    def load_obj_optimized(self, filename):
        mtime = os.path.getmtime(filename)
        content = self._cached_file_read(filename, mtime)
        if content is None:
            return None, None, None

        lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
        vertex_lines, normal_lines, face_lines = [], [], []
        for line in lines:
            if line.startswith('v '): vertex_lines.append(line)
            elif line.startswith('vn '): normal_lines.append(line)
            elif line.startswith('f '): face_lines.append(line)

        with ThreadPoolExecutor(max_workers=3) as executor:
            vertices = executor.submit(self._parse_vertices, vertex_lines).result()
            normals = executor.submit(self._parse_normals, normal_lines).result()
            faces = executor.submit(self._parse_faces, face_lines).result()
        return vertices, normals, faces

    def _parse_vertices(self, vertex_lines):
        return np.array([[float(x) for x in line.split()[1:4]] for line in vertex_lines], dtype=np.float32)

    def _parse_normals(self, normal_lines):
        return np.array([[float(x) for x in line.split()[1:4]] for line in normal_lines], dtype=np.float32)

    def _parse_faces(self, face_lines):
        faces = []
        for line in face_lines:
            face = []
            for vertex_data in line.split()[1:]:
                parts = vertex_data.split('/')
                v_idx = int(parts[0]) - 1 if parts[0] else None
                n_idx = int(parts[2]) - 1 if len(parts) > 2 and parts[2] else None
                face.append((v_idx, n_idx))
            faces.append(face)
        return faces

    @lru_cache(maxsize=128)
    def _cached_file_read(self, filename, mtime):
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()

    def setup_vbo(self, vertices, normals, faces):
        vertex_data, normal_data = [], []
        for face in faces:
            for i in range(1, len(face) - 1):
                for j in [0, i, i + 1]:
                    v_idx, n_idx = face[j]
                    vertex_data.append(vertices[v_idx])
                    normal_data.append(normals[n_idx] if n_idx is not None else [0, 0, 1])
        vertex_array = np.array(vertex_data, dtype=np.float32)
        normal_array = np.array(normal_data, dtype=np.float32)
        self.vbo_vertices = vbo.VBO(vertex_array)
        self.vbo_normals = vbo.VBO(normal_array)
        self.vertex_count = len(vertex_array)

    def render_scene_shader(self, camera_pos, camera_look_at, camera_up, fov, width, height):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)

        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(fov, width / float(height), 0.1, 1000.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(*camera_pos, *camera_look_at, *camera_up)

        modelview = glGetFloatv(GL_MODELVIEW_MATRIX)
        projection = glGetFloatv(GL_PROJECTION_MATRIX)

        if self.shader_program is None:
            self.shader_program = create_shader_program()

        glUseProgram(self.shader_program)

        loc_modelview = glGetUniformLocation(self.shader_program, 'modelview')
        loc_projection = glGetUniformLocation(self.shader_program, 'projection')
        glUniformMatrix4fv(loc_modelview, 1, GL_FALSE, modelview)
        glUniformMatrix4fv(loc_projection, 1, GL_FALSE, projection)

        pos_loc = glGetAttribLocation(self.shader_program, 'position')
        norm_loc = glGetAttribLocation(self.shader_program, 'normal')

        glEnableVertexAttribArray(pos_loc)
        glEnableVertexAttribArray(norm_loc)

        self.vbo_vertices.bind()
        glVertexAttribPointer(pos_loc, 3, GL_FLOAT, GL_FALSE, 0, self.vbo_vertices)
        self.vbo_vertices.unbind()

        self.vbo_normals.bind()
        glVertexAttribPointer(norm_loc, 3, GL_FLOAT, GL_FALSE, 0, self.vbo_normals)
        self.vbo_normals.unbind()

        glDrawArrays(GL_TRIANGLES, 0, self.vertex_count)

        glDisableVertexAttribArray(pos_loc)
        glDisableVertexAttribArray(norm_loc)
        glUseProgram(0)

    def save_screenshot(self, filename, width, height):
        glFinish()
        pixels = glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE)
        image = np.frombuffer(pixels, dtype=np.uint8).reshape((height, width, 3))
        image = np.flipud(image)
        Image.fromarray(image).save(filename, optimize=True)


def load_config(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def select_file(title, types):
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(title=title, filetypes=types)
    root.destroy()
    return path

def main():
    obj_path = select_file("OBJ 파일 선택", [("OBJ files", "*.obj")])
    if not obj_path: return
    config_path = select_file("YAML 설정 파일 선택", [("YAML files", "*.yaml")])
    if not config_path: return

    config = load_config(config_path)
    cam = config['camera_settings']
    camera_pos = tuple(cam['position'])
    camera_look_at = tuple(cam['look_at'])
    camera_up = tuple(cam['up_vector'])
    fov = float(cam['fov'])
    output_file = config['output_filename']
    w, h = int(config.get('render_width', 800)), int(config.get('render_height', 600))

    pygame.init()
    screen = pygame.display.set_mode((w, h), DOUBLEBUF | OPENGL | HIDDEN)
    renderer = OptimizedOBJRenderer()
    vertices, normals, faces = renderer.load_obj_optimized(obj_path)
    renderer.setup_vbo(vertices, normals, faces)

    renderer.render_scene_shader(camera_pos, camera_look_at, camera_up, fov, w, h)

    renderer.save_screenshot(output_file, w, h)
    pygame.quit()
    print("렌더링 완료")

if __name__ == '__main__':
    main()
