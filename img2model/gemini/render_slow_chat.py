import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from PIL import Image
import numpy as np
import tkinter as tk
from tkinter import filedialog
import os
import yaml # Import PyYAML library
import time

def load_obj(filename):
    """
    Parses an OBJ file to load vertex, normal, and face information.
    (Simple implementation, does not handle UV coordinates or complex OBJ features.)
    """
    vertices = []
    normals = []
    faces = []

    try:
        # Explicitly specify 'utf-8' encoding for reading the OBJ file
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
                        # OBJ indices are 1-based, so subtract 1
                        face.append(tuple(int(x) - 1 if x else None for x in w))
                    faces.append(face)
    except FileNotFoundError:
        print(f"Error: Could not find '{filename}' file.")
        return None, None, None
    except Exception as e:
        print(f"Error loading OBJ file: {e}")
        return None, None, None
        
    return vertices, normals, faces

def render_scene(vertices, normals, faces, camera_pos, camera_look_at, camera_up, fov, width, height):
    """
    Renders the scene using OpenGL.
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
    Saves the content of the current OpenGL buffer to an image file.
    """
    pixels = glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE)
    image = Image.frombytes("RGB", (width, height), pixels)
    image = image.transpose(Image.FLIP_TOP_BOTTOM)  # OpenGL textures are flipped vertically
    image.save(filename)
    print(f"Rendered image saved to '{filename}'.")

def select_obj_file():
    """
    Opens a file dialog for the user to select an OBJ file.
    """
    root = tk.Tk()
    root.withdraw()  # Hide the default Tkinter window

    file_path = filedialog.askopenfilename(
        title="Select OBJ file to render",
        filetypes=[("OBJ files", "*.obj"), ("All files", "*.*")]
    )
    root.destroy() # Destroy the Tkinter root window after dialog is closed
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

    # Prompt user to select YAML configuration file
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
        render_width = int(config.get('render_width', 800))  # Default to 800
        render_height = int(config.get('render_height', 600)) # Default to 600

        if not all([camera_pos, camera_look_at, camera_up, fov, output_filename]):
            raise ValueError("One or more required camera settings or output filename are missing in YAML.")
        if not (0 < fov < 180):
            raise ValueError("FOV must be between 0 and 180 degrees.")

    except (TypeError, ValueError, AttributeError) as e:
        print(f"Error validating YAML configuration: {e}")
        print("Please ensure your YAML file has the following structure:")
        print("""
camera_settings:
  position: [0.0, 0.0, 5.0]
  look_at: [0.0, 0.0, 0.0]
  up_vector: [0.0, 1.0, 0.0]
  fov: 60.0
output_filename: "rendered_image.png"
render_width: 800
render_height: 600
        """)
        return

    vertices, normals, faces = load_obj(obj_filepath)
    if vertices is None or not vertices or not faces:
        print("Failed to load OBJ file or it contains no valid data.")
        return
    print(f"{os.path.basename(obj_filepath)} loaded successfully. Vertices: {len(vertices)}, Faces: {len(faces)}")

    pygame.init()
    # Initialize Pygame display, hidden to create OpenGL context without showing a window
    screen = pygame.display.set_mode((render_width, render_height), DOUBLEBUF | OPENGL | HIDDEN)
    pygame.display.set_caption("OBJ Renderer (Hidden)")

    try:
        # Render the scene
        render_scene(vertices, normals, faces, camera_pos, camera_look_at, camera_up, fov, render_width, render_height)

        # Save the screenshot
        save_screenshot(output_filename, render_width, render_height)
    except Exception as e:
        print(f"Error during rendering or saving: {e}")
    finally:
        pygame.quit()
        print("Program finished.")
        total_time = time.time() - total_start
        print(f"Total execution time: {total_time:.3f}s")

if __name__ == "__main__":
    main()