# renderer.py (Visualizer 기반으로 extrinsic 적용 렌더러)

import open3d as o3d
import numpy as np
import os

class Renderer:
    def __init__(self, model_path, intrinsics):
        self.intrinsics = intrinsics
        self.width = int(intrinsics['width'])
        self.height = int(intrinsics['height'])
        self.fx = float(intrinsics['fx'])
        self.fy = float(intrinsics['fy'])
        self.cx = float(intrinsics['cx'])
        self.cy = float(intrinsics['cy'])

        self.intrinsic_o3d = o3d.camera.PinholeCameraIntrinsic(
            self.width, self.height, self.fx, self.fy, self.cx, self.cy)

        self.mesh = o3d.io.read_triangle_mesh(model_path)
        if not self.mesh.has_vertex_normals():
            self.mesh.compute_vertex_normals()

    def render_rgbd(self, extrinsic):
        vis = o3d.visualization.Visualizer()
        vis.create_window(width=self.width, height=self.height, visible=True)
        vis.add_geometry(self.mesh)

        ctr = vis.get_view_control()
        parameters = o3d.camera.PinholeCameraParameters()
        parameters.intrinsic = self.intrinsic_o3d
        parameters.extrinsic = extrinsic
        ctr.convert_from_pinhole_camera_parameters(parameters)

        vis.poll_events()
        vis.update_renderer()

        rgb = vis.capture_screen_float_buffer(False)
        depth = vis.capture_depth_float_buffer(False)
        vis.destroy_window()

        rgb_np = (np.asarray(rgb) * 255).astype(np.uint8)
        depth_np = (np.asarray(depth) * 1000).astype(np.uint16)

        os.makedirs("results", exist_ok=True)
        o3d.io.write_image("results/render_color.png", o3d.geometry.Image(rgb_np))
        o3d.io.write_image("results/render_depth.png", o3d.geometry.Image(depth_np))

        return rgb_np, depth_np
