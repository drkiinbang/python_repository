# render_optimized.py
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from PIL import Image
import numpy as np
import tkinter as tk
from tkinter import filedialog
import os
import yaml
import time

"""
성능 최적화 (compared to original render.py)

이전 코드는 이해하기 쉽고 OpenGL의 기본적인 렌더링 파이프라인을 잘 보여주지만, 성능 면에서는 다음과 같은 한계점을 가지고 있습니다.
즉시 모드(Immediate Mode) 사용: glBegin(), glEnd(), glVertex3fv(), glNormal3fv()와 같은 함수를 사용하는 방식을 "즉시 모드"라고 합니다. 이 방식은 각 정점(vertex) 데이터를 CPU에서 GPU로 하나씩 전송합니다. 모델이 복잡해져 수십만, 수백만 개의 정점이 존재할 경우, 이 통신 오버헤드는 렌더링 속도를 심각하게 저하시키는 주된 원인이 됩니다.
데이터 구조: 정점, 법선 데이터를 파이썬 기본 리스트(list)에 저장하고 있습니다. 이 데이터들은 렌더링 시점에 PyOpenGL에 의해 내부적으로 변환 과정이 필요하며, NumPy 배열에 비해 메모리 효율성과 접근 속도가 떨어집니다.
최적화 방향 및 전략
위의 병목 현상을 해결하고 고속 렌더링을 달성하기 위한 핵심 전략은 다음과 같습니다.
현대적인 OpenGL 방식 도입 (VBO 사용): 즉시 모드 대신 **VBO(Vertex Buffer Object)**를 사용하여 렌더링 성능을 극적으로 향상시킵니다. VBO는 정점, 법선, 색상 등 대량의 렌더링 데이터를 GPU 메모리에 미리 업로드해두고, 렌더링 시에는 간단한 그리기 명령(glDrawArrays)만 호출하는 방식입니다. 이를 통해 CPU와 GPU 간의 데이터 전송을 최소화하여 통신 병목을 제거할 수 있습니다.
NumPy 배열 활용: 모든 정점 및 법선 데이터를 파이썬 리스트 대신 NumPy 배열로 관리합니다. NumPy 배열은 메모리상에 연속적으로 데이터를 저장하여 접근 속도가 빠르며, PyOpenGL은 NumPy 배열을 매우 효율적으로 처리하도록 설계되었습니다. VBO에 데이터를 업로드할 때 NumPy 배열을 사용하면 추가적인 변환 없이 바로 GPU로 전송할 수 있습니다.
"""

def load_obj_optimized(filename):
    """
    Parses an OBJ file and loads vertex and normal data into NumPy arrays.
    It prepares data in a format suitable for VBOs (interleaved).
    """
    vertices = []
    normals = []
    v_indices = []
    n_indices = []

    try:
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
                    for v in values[1:]:
                        w = v.split('/')
                        # OBJ indices are 1-based, so subtract 1
                        v_indices.append(int(w[0]) - 1)
                        # Handle cases where normals might not be present in the face definition
                        if len(w) >= 3 and w[2]:
                            n_indices.append(int(w[2]) - 1)
                        else:
                            # If no normal index, we might need a placeholder or specific handling
                            # For this example, we'll assume normals are always present with vertices.
                            # A more robust solution might generate normals if they are missing.
                            pass 

    except FileNotFoundError:
        print(f"Error: Could not find '{filename}' file.")
        return None, 0
    except Exception as e:
        print(f"Error loading OBJ file: {e}")
        return None, 0

    if not v_indices:
        return None, 0

    # Create arrays based on face indices to ensure correct order
    # This creates the final flat array of vertex attributes for rendering
    final_vertices = np.array([vertices[i] for i in v_indices], dtype=np.float32)
    final_normals = np.array([normals[i] for i in n_indices], dtype=np.float32)

    # For interleaved VBO: [v1_x, v1_y, v1_z, n1_x, n1_y, n1_z, v2_x, ...]
    interleaved_data = np.hstack([final_vertices, final_normals]).flatten()

    return interleaved_data, len(v_indices)

def create_vbo(data):
    """
    Creates a Vertex Buffer Object (VBO) and loads the provided data into it.
    """
    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, GL_STATIC_DRAW)
    return vbo

def render_scene_vbo(vbo, vertex_count, camera_pos, camera_look_at, camera_up, fov, width, height):
    """
    Renders the scene using a VBO.
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

    # Bind the VBO
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    
    # Enable vertex and normal arrays
    glEnableClientState(GL_VERTEX_ARRAY)
    glEnableClientState(GL_NORMAL_ARRAY)

    # Define pointers to the vertex and normal data within the interleaved VBO
    # Stride is 6 * float_size because each vertex block has 3 vertex coords + 3 normal coords
    stride = 6 * 4  # 6 floats, 4 bytes each
    glVertexPointer(3, GL_FLOAT, stride, None)
    # Normals start after the 3 vertex floats (offset = 3 * float_size)
    glNormalPointer(GL_FLOAT, stride, ctypes.c_void_p(3 * 4))

    # Draw the primitives
    glDrawArrays(GL_TRIANGLES, 0, vertex_count)

    # Disable arrays and unbind VBO
    glDisableClientState(GL_VERTEX_ARRAY)
    glDisableClientState(GL_NORMAL_ARRAY)
    glBindBuffer(GL_ARRAY_BUFFER, 0)


def save_screenshot(filename, width, height):
    """
    Saves the content of the current OpenGL buffer to an image file.
    """
    pixels = glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE)
    image = Image.frombytes("RGB", (width, height), pixels)
    image = image.transpose(Image.FLIP_TOP_BOTTOM)
    image.save(filename)
    print(f"Rendered image saved to '{filename}'.")

def select_obj_file():
    """
    Opens a file dialog for the user to select an OBJ file.
    """
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select OBJ file to render",
        filetypes=[("OBJ files", "*.obj"), ("All files", "*.*")]
    )
    root.destroy()
    return file_path

def load_config_from_yaml(filepath):
    """
    Loads configuration parameters from a YAML file.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        print(f"Error: YAML configuration file '{filepath}' not found.")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file '{filepath}': {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while loading YAML: {e}")
        return None

def main():
    obj_filepath = select_obj_file()
    if not obj_filepath:
        print("OBJ file selection cancelled. Exiting program.")
        return

    print(f"Selected OBJ file: {obj_filepath}")

    root = tk.Tk()
    root.withdraw()
    yaml_filepath = filedialog.askopenfilename(
        title="Select YAML configuration file",
        filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")]
    )
    root.destroy()
    if not yaml_filepath:
        print("YAML configuration file selection cancelled. Exiting program.")
        return

    print(f"Selected YAML config file: {yaml_filepath}")

    total_start = time.time()

    config = load_config_from_yaml(yaml_filepath)
    if not config:
        print("Failed to load configuration from YAML. Exiting program.")
        return

    # Validate and extract configuration values
    try:
        camera_settings = config.get('camera_settings')
        if not camera_settings:
            raise ValueError("Missing 'camera_settings' in YAML.")

        camera_pos = tuple(camera_settings.get('position'))
        camera_look_at = tuple(camera_settings.get('look_at'))
        camera_up = tuple(camera_settings.get('up_vector'))
        fov = float(camera_settings.get('fov'))
        output_filename = config.get('output_filename')
        render_width = int(config.get('render_width', 800))
        render_height = int(config.get('render_height', 600))

        if not all([camera_pos, camera_look_at, camera_up, fov, output_filename]):
            raise ValueError("One or more required camera settings or output filename are missing in YAML.")
        if not (0 < fov < 180):
            raise ValueError("FOV must be between 0 and 180 degrees.")

    except (TypeError, ValueError, AttributeError) as e:
        print(f"Error validating YAML configuration: {e}")
        return

    # Use the optimized OBJ loader
    render_data, vertex_count = load_obj_optimized(obj_filepath)
    if render_data is None:
        print("Failed to load OBJ file or it contains no valid data.")
        return
    print(f"{os.path.basename(obj_filepath)} loaded successfully. Total vertices to render: {vertex_count}")

    pygame.init()
    screen = pygame.display.set_mode((render_width, render_height), DOUBLEBUF | OPENGL | HIDDEN)
    pygame.display.set_caption("OBJ Renderer (Optimized - Hidden)")

    vbo = None
    try:
        # Create VBO from the loaded data
        vbo = create_vbo(render_data)

        # Render the scene using the VBO
        render_scene_vbo(vbo, vertex_count, camera_pos, camera_look_at, camera_up, fov, render_width, render_height)

        # Save the screenshot
        save_screenshot(output_filename, render_width, render_height)
    except Exception as e:
        print(f"Error during rendering or saving: {e}")
    finally:
        # Clean up the VBO
        if vbo:
            glDeleteBuffers(1, [vbo])
        pygame.quit()
        print("Program finished.")
        total_time = time.time() - total_start
        print(f"Total execution time: {total_time:.3f}s")

if __name__ == "__main__":
    main()