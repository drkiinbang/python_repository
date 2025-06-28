import open3d as o3d
import numpy as np
import os

class Renderer:
    def __init__(self, model_path, intrinsics):
        self.model_path = model_path
        self.intrinsics = intrinsics

        self.width = int(intrinsics['width'])
        self.height = int(intrinsics['height'])
        self.fx = float(intrinsics['fx'])
        self.fy = float(intrinsics['fy'])
        self.cx = float(intrinsics['cx'])
        self.cy = float(intrinsics['cy'])

        self.intrinsic_o3d = o3d.camera.PinholeCameraIntrinsic(
            self.width, self.height, self.fx, self.fy, self.cx, self.cy)

        # 메시 로딩 및 검증
        self.mesh = o3d.io.read_triangle_mesh(model_path)
        if len(self.mesh.vertices) == 0:
            raise ValueError(f"메시를 로드할 수 없습니다: {model_path}")
        
        print(f"메시 로드 완료 - 정점: {len(self.mesh.vertices)}, 면: {len(self.mesh.triangles)}")
        
        # 법선 벡터 계산
        if not self.mesh.has_vertex_normals():
            self.mesh.compute_vertex_normals()
        
        # 기본 색상 설정 (색상이 없는 경우)
        if not self.mesh.has_vertex_colors():
            self.mesh.paint_uniform_color([0.7, 0.7, 0.7])

    def debug_render_setup(self):
        """렌더링 설정 디버깅 정보 출력"""
        bbox = self.mesh.get_axis_aligned_bounding_box()
        center = self.mesh.get_center()
        
        print("=== 렌더링 디버그 정보 ===")
        print(f"메시 경계상자: min={bbox.min_bound}, max={bbox.max_bound}")
        print(f"메시 중심: {center}")
        print(f"카메라 내부 파라미터: fx={self.fx}, fy={self.fy}")
        print(f"카메라 주점: cx={self.cx}, cy={self.cy}")
        print(f"이미지 크기: {self.width}x{self.height}")
        print("========================")

    def render_rgbd(self, extrinsic, debug=False):
        """RGBD 이미지 렌더링"""
        
        if debug:
            self.debug_render_setup()
        
        # Extrinsic 행렬 검증
        if not isinstance(extrinsic, np.ndarray) or extrinsic.shape != (4, 4):
            raise ValueError("Extrinsic 행렬은 4x4 numpy 배열이어야 합니다")
        
        # Visualizer 생성
        vis = o3d.visualization.Visualizer()
        vis.create_window(width=self.width, height=self.height, visible=False)
        
        try:
            # 메시 추가
            vis.add_geometry(self.mesh)
            
            # 렌더링 옵션 설정
            render_option = vis.get_render_option()
            render_option.show_coordinate_frame = False
            render_option.background_color = np.array([0, 0, 0])  # 검은 배경
            render_option.mesh_show_back_face = True              # 메시 뒷면 표시 여부
                        
            # 카메라 파라미터 설정
            ctr = vis.get_view_control()
            parameters = o3d.camera.PinholeCameraParameters()
            parameters.intrinsic = self.intrinsic_o3d
            parameters.extrinsic = extrinsic
            
            if debug:
                print("=== 생성된 Extrinsic 행렬 ===")
                print(extrinsic)
                print("============================")

            # 카메라 파라미터 적용
            ctr.convert_from_pinhole_camera_parameters(parameters)
            
            # 안정적인 렌더링을 위한 여러 번 업데이트
            for i in range(5):
                vis.poll_events()
                vis.update_renderer()
            
            # 이미지 캡처
            rgb_image = vis.capture_screen_float_buffer(do_render=True)
            depth_image = vis.capture_depth_float_buffer(do_render=True)
            
            # numpy 배열로 변환
            rgb_np = (np.asarray(rgb_image) * 255).astype(np.uint8)
            depth_np = np.asarray(depth_image)
            
            # depth 이미지를 mm 단위로 변환 (0이 아닌 값만)
            depth_np = np.where(depth_np > 0, depth_np * 1000, 0).astype(np.uint16)
            
            if debug:
                print(f"RGB 이미지 형태: {rgb_np.shape}, 타입: {rgb_np.dtype}")
                print(f"Depth 이미지 형태: {depth_np.shape}, 타입: {depth_np.dtype}")
                print(f"Depth 범위: {depth_np.min()} ~ {depth_np.max()}")
            
            # 결과 저장
            os.makedirs("results", exist_ok=True)
            o3d.io.write_image("results/render_color.png", o3d.geometry.Image(rgb_np))
            o3d.io.write_image("results/render_depth.png", o3d.geometry.Image(depth_np))
            
            print("렌더링 완료: results/render_color.png, results/render_depth.png")

            return rgb_np, depth_np
            
        finally:
            # 리소스 정리
            vis.destroy_window()

    def create_extrinsic_photogrammetric(self, X, Y, Z, omega, phi, kappa, angle_unit='degree'):
        """
        사진측량학적 EOP로부터 extrinsic 행렬 생성 (표준 사진측량 관례)
        
        Args:
            X, Y, Z: 카메라 위치 좌표 (월드 좌표계)
            omega, phi, kappa: 회전각 (사진측량학적 정의)
            angle_unit: 각도 단위 ('degree' 또는 'radian')
        
        Returns:
            4x4 extrinsic 행렬
        """
        
        # 각도를 라디안으로 변환
        if angle_unit.lower() == 'degree':
            omega = np.radians(omega)
            phi = np.radians(phi)
            kappa = np.radians(kappa)
        
        # 사진측량학적 회전 행렬 생성 (표준 관례)
        # omega: X축 회전 (primary rotation)
        # phi: Y축 회전 (secondary rotation) 
        # kappa: Z축 회전 (tertiary rotation)
        
        # X축 회전 (omega) - pitch
        Rx = np.array([
            [1, 0, 0],
            [0, np.cos(omega), -np.sin(omega)],
            [0, np.sin(omega), np.cos(omega)]
        ])
        
        # Y축 회전 (phi) - roll
        Ry = np.array([
            [np.cos(phi), 0, np.sin(phi)],
            [0, 1, 0],
            [-np.sin(phi), 0, np.cos(phi)]
        ])
        
        # Z축 회전 (kappa) - yaw
        Rz = np.array([
            [np.cos(kappa), -np.sin(kappa), 0],
            [np.sin(kappa), np.cos(kappa), 0],
            [0, 0, 1]
        ])
        
        # 사진측량학적 회전 순서: R = Rz * Ry * Rx
        R_photo = Rz @ Ry @ Rx
        
        """
        # 사진측량 좌표계에서 컴퓨터 비전 좌표계로 변환
        # 사진측량: Z위쪽, Y북쪽, X동쪽
        # 컴퓨터 비전: Z앞쪽, Y아래쪽, X오른쪽
        coord_transform = np.array([
            [1, 0, 0],      # X축 유지
            [0, -1, 0],     # Y축 뒤집기 (북쪽 -> 아래쪽)
            [0, 0, -1]      # Z축 뒤집기 (위쪽 -> 앞쪽)
        ])
        
        # 최종 회전 행렬
        R_final = coord_transform @ R_photo
        """
        R_final = R_photo

        # 카메라 위치를 카메라 좌표계 원점으로 변환
        camera_center = np.array([X, Y, Z])
        
        # Extrinsic 행렬 구성 (World to Camera 변환)
        extrinsic = np.eye(4)
        extrinsic[:3, :3] = R_final.T  # 회전 행렬의 전치 (월드->카메라)
        extrinsic[:3, 3] = -R_final.T @ camera_center  # 평행이동
        
        return extrinsic

    def create_extrinsic_alternative(self, X, Y, Z, omega, phi, kappa, angle_unit='degree'):
        """
        대안적인 EOP 변환 방식 (다른 좌표계 관례)
        """
        
        # 각도를 라디안으로 변환
        if angle_unit.lower() == 'degree':
            omega = np.radians(omega)
            phi = np.radians(phi)
            kappa = np.radians(kappa)
        
        # 직접적인 변환 (좌표계 변환 없이)
        cos_o, sin_o = np.cos(omega), np.sin(omega)
        cos_p, sin_p = np.cos(phi), np.sin(phi)
        cos_k, sin_k = np.cos(kappa), np.sin(kappa)
        
        # 회전 행렬 직접 계산
        R = np.array([
            [cos_p*cos_k, -cos_p*sin_k, sin_p],
            [cos_o*sin_k + sin_o*sin_p*cos_k, cos_o*cos_k - sin_o*sin_p*sin_k, -sin_o*cos_p],
            [sin_o*sin_k - cos_o*sin_p*cos_k, sin_o*cos_k + cos_o*sin_p*sin_k, cos_o*cos_p]
        ])
        
        # Extrinsic 행렬 구성
        extrinsic = np.eye(4)
        extrinsic[:3, :3] = R
        extrinsic[:3, 3] = np.array([X, Y, Z])
        
        return extrinsic

    def render_from_eop(self, X, Y, Z, omega, phi, kappa, angle_unit='degree', method='photogrammetric', debug=False):
        """
        EOP 파라미터를 사용하여 직접 렌더링
        
        Args:
            X, Y, Z: 카메라 위치
            omega, phi, kappa: 회전각
            angle_unit: 각도 단위 ('degree' 또는 'radian')
            method: 변환 방식 ('photogrammetric' 또는 'alternative')
            debug: 디버그 정보 출력 여부
        
        Returns:
            rgb_image, depth_image
        """
        
        if debug:
            print(f"EOP 파라미터:")
            print(f"  위치: X={X}, Y={Y}, Z={Z}")
            print(f"  회전: ω={omega}, φ={phi}, κ={kappa} ({angle_unit})")
            print(f"  변환 방식: {method}")
        
        # EOP로부터 extrinsic 행렬 생성
        if method == 'photogrammetric':
            extrinsic = self.create_extrinsic_photogrammetric(X, Y, Z, omega, phi, kappa, angle_unit)
        elif method == 'alternative':
            extrinsic = self.create_extrinsic_alternative(X, Y, Z, omega, phi, kappa, angle_unit)
        else:
            raise ValueError("method는 'photogrammetric' 또는 'alternative'이어야 합니다")
        
        if debug:
            print(f"생성된 Extrinsic 행렬 ({method}):")
            print(extrinsic)
        
        # 렌더링 실행
        return self.render_rgbd(extrinsic, debug=debug)

# 사용 예시 및 테스트
if __name__ == "__main__":
    # 카메라 내부 파라미터
    renderScale = 0.2
    intrinsics = {
        'width': (7952 * renderScale),
        'height': (5304 * renderScale),
        'fx': (7751.94 * renderScale),
        'fy': (7751.94 * renderScale),
        'cx': (3976 * renderScale),
        'cy': (2652 * renderScale)
    }
    
    # 렌더러 초기화
    #renderer = Renderer("F:\\Users\\bbarab\\Downloads\\미호천하행\\obj_transformed_merged\\merged_transformed.obj", intrinsics)
    renderer = Renderer("F:\\Users\\bbarab\\Downloads\\동산교\\merged_transformed.obj", intrinsics)
    
    # EOP 파라미터
    #X, Y, Z = 330261.338, 4076995.039, 60.787
    X, Y, Z = 330293.614777, 4076878.936974, 79.146873

    #omega, phi, kappa = 0.02438466, -0.2871388, 45.0
    omega, phi, kappa = 0.0, 0.0, 0.0
    
    print("=== 방법 1: 사진측량학적 변환 ===")
    rgb1, depth1 = renderer.render_from_eop(X, Y, Z, omega, phi, kappa, 
                                           method='photogrammetric', debug=True)
    
    # 결과를 다른 이름으로 저장
    os.replace("results/render_color.png", "results/render_color_photo.png")
    os.replace("results/render_depth.png", "results/render_depth_photo.png")
    
    print("\n=== 방법 2: 대안적 변환 ===")
    rgb2, depth2 = renderer.render_from_eop(X, Y, Z, omega, phi, kappa, 
                                           method='alternative', debug=True)
    
    os.replace("results/render_color.png", "results/render_color_alt.png")
    os.replace("results/render_depth.png", "results/render_depth_alt.png")
    
    print("\n두 가지 방법으로 렌더링 완료!")
    print("결과 비교:")
    print("- render_color_photo.png: 사진측량학적 변환")
    print("- render_color_alt.png: 대안적 변환")