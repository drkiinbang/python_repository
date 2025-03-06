import os
import numpy as np
from PIL import Image
import torch
import trimesh
import torch.nn.functional as F
from pytorch3d.structures import Meshes
from pytorch3d.renderer import TexturesVertex
from pytorch3d.renderer import (
    look_at_view_transform,
    FoVPerspectiveCameras,
    PointLights,
    RasterizationSettings,
    MeshRenderer,
    MeshRasterizer,
    SoftPhongShader,
)

class GaussianSplatting:
    def __init__(self, device=None):
        if device is None:
            self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        else:
            self.device = device
        
        print(f"Using device: {self.device}")

    def load_mesh_from_file(self, file_path):
        """
        다양한 3D 메시 파일 로드 지원
        지원 포맷: .obj, .gltf, .glb
        """
        # 파일 확장자 확인
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Trimesh로 메시 로드
        try:
            mesh = trimesh.load_mesh(file_path)
        except Exception as e:
            print(f"메시 로드 중 오류 발생: {e}")
            return None
        
        # 정점(vertices)과 면(faces) 추출
        vertices = torch.tensor(mesh.vertices, dtype=torch.float32)
        faces = torch.tensor(mesh.faces, dtype=torch.int64)
        
        # 색상 처리
        if mesh.visual.kind == 'vertex':
            # 버텍스 컬러가 있는 경우
            colors = torch.tensor(mesh.visual.vertex_colors[:, :3] / 255.0, dtype=torch.float32)
        else:
            # 기본 색상 (회색)
            colors = torch.ones_like(vertices) * 0.5
        
        # Meshes 객체 생성
        pytorch3d_mesh = Meshes(
            verts=[vertices],
            faces=[faces],
            textures=TexturesVertex(verts_features=[colors])
        )
        
        return pytorch3d_mesh
        
    def load_mesh(self, vertices, faces, colors=None):
        # vertices와 faces를 torch 텐서로 변환
        verts = torch.tensor(vertices, dtype=torch.float32)
        faces_tensor = torch.tensor(faces, dtype=torch.int64)
        
        # 색상 처리
        if colors is not None:
            verts_rgb = torch.tensor(colors, dtype=torch.float32)
            # 색상 값이 0-1 범위인지 확인 (RGB 값)
            if verts_rgb.max() > 1:
                verts_rgb = verts_rgb / 255.0
            
            # Meshes 생성자에 맞게 colors 전달
            mesh = Meshes(
                verts=[verts], 
                faces=[faces_tensor], 
                textures=TexturesVertex(verts_features=[verts_rgb])
            )
        else:
            # 색상 없는 경우
            mesh = Meshes(
                verts=[verts], 
                faces=[faces_tensor]
            )
        
        return mesh
    
    def convert_mesh_to_gaussians(self, mesh):
        """
        메시를 가우시안 스플랫으로 변환합니다.
        
        Args:
            mesh: Meshes 객체
            
        Returns:
            centers: 가우시안 중심점 좌표
            scales: 가우시안 스케일
            rotations: 가우시안 회전
            colors: 가우시안 색상
            opacities: 가우시안 불투명도
        """        
        # 정점 추출
        verts = mesh.verts_packed()
        
        # 텍스처(색상) 처리
        if mesh.textures is not None:
            # verts_features_packed() 메서드 사용
            vertex_colors = mesh.textures.verts_features_packed()
            
            # 색상 값이 0-1 범위가 아니라면 정규화
            if vertex_colors.max() > 1:
                vertex_colors = vertex_colors / 255.0
        else:
            # 기본 색상 (흰색)
            vertex_colors = torch.ones_like(verts)

        # 랜덤한 스케일과 회전 생성
        num_points = verts.shape[0]
        scales = torch.ones(num_points, 3, dtype=torch.float32) * 0.1
        rotations = torch.zeros(num_points, 4, dtype=torch.float32)
        rotations[:, 0] = 1.0  # 항등 쿼터니언

        # 불투명도 설정
        opacities = torch.ones(num_points, 1, dtype=torch.float32)

        return verts, scales, rotations, vertex_colors, opacities
    
    def interpolate_gaussians(self, centers1, scales1, rotations1, colors1, opacities1,
                             centers2, scales2, rotations2, colors2, opacities2,
                             t):
        """
        두 가우시안 세트 사이를 보간합니다.
        
        Args:
            centers1, centers2: 가우시안 중심점 좌표
            scales1, scales2: 가우시안 스케일
            rotations1, rotations2: 가우시안 회전(쿼터니언)
            colors1, colors2: 가우시안 색상
            opacities1, opacities2: 가우시안 불투명도
            t: 보간 계수 (0~1)
            
        Returns:
            보간된 가우시안 속성들
        """
        # 중심점과 스케일은 선형 보간
        centers = (1 - t) * centers1 + t * centers2
        scales = (1 - t) * scales1 + t * scales2
        colors = (1 - t) * colors1 + t * colors2
        opacities = (1 - t) * opacities1 + t * opacities2
        
        # 쿼터니언 회전은 slerp로 보간
        dot_product = torch.sum(rotations1 * rotations2, dim=1, keepdim=True)
        
        # 내적이 음수면 한쪽 쿼터니언의 부호를 반전하여 최단경로로 보간
        rotations2_adj = torch.where(dot_product < 0, -rotations2, rotations2)
        dot_product = torch.abs(dot_product)
        
        # 두 쿼터니언이 거의 평행한 경우 선형 보간 사용
        linear_interp_mask = dot_product > 0.9995
        
        # SLERP 보간 계산
        theta = torch.acos(dot_product.clamp(-1, 1))
        sin_theta = torch.sin(theta)
        
        s1 = torch.sin((1 - t) * theta) / sin_theta
        s2 = torch.sin(t * theta) / sin_theta
        
        # 마스크에 따라 선형 또는 SLERP 보간 적용
        rotations = torch.where(
            linear_interp_mask,
            (1 - t) * rotations1 + t * rotations2_adj,
            s1 * rotations1 + s2 * rotations2_adj
        )
        
        # 정규화
        rotations = F.normalize(rotations, p=2, dim=1)
        
        return centers, scales, rotations, colors, opacities
    
    def render_gaussians(self, centers, scales, rotations, colors, opacities, 
                         image_size=512, fov=60.0, camera_distance=2.0):
        """
        가우시안 스플래팅을 사용하여 렌더링합니다 (간소화된 버전).
        실제 렌더링은 더 복잡합니다.
        
        이 함수는 개념적인 구현이며, 실제로는 pytorch3d나 다른 차등 렌더러가 필요합니다.
        """
        # 간소화된 렌더링 로직 (실제 구현은 더 복잡할 수 있음)
        # 여기서는 PyTorch3D를 사용한 메시 렌더링의 기본 골격만 제공합니다
        
        # 카메라 설정
        R, T = look_at_view_transform(camera_distance, 0, 0)
        cameras = FoVPerspectiveCameras(device=self.device, R=R, T=T, fov=fov)
        
        # 라이트 설정
        lights = PointLights(
            device=self.device,
            location=[[0.0, 0.0, -3.0]],
            ambient_color=[[0.5, 0.5, 0.5]],
            diffuse_color=[[0.3, 0.3, 0.3]],
            specular_color=[[0.2, 0.2, 0.2]]
        )
        
        # 가우시안을 사용한 실제 렌더링은 여기에 구현해야 합니다
        # 이 예제에서는 개념만 설명하고 전체 구현은 생략합니다
        
        # 목 렌더링 결과 반환
        image = torch.zeros((image_size, image_size, 3), device=self.device)
        return image

    def interpolate_meshes(self, mesh1, mesh2, num_frames=30):
        """
        두 메시 사이를 가우시안 스플래팅을 사용하여 보간합니다.
        
        Args:
            mesh1, mesh2: 보간할 두 Meshes 객체
            num_frames: 생성할 프레임 수
            
        Returns:
            frames: 보간된 프레임 리스트
        """
        # 메시를 가우시안으로 변환
        centers1, scales1, rotations1, colors1, opacities1 = self.convert_mesh_to_gaussians(mesh1)
        centers2, scales2, rotations2, colors2, opacities2 = self.convert_mesh_to_gaussians(mesh2)
        
        frames = []
        
        for i in range(num_frames):
            t = i / (num_frames - 1)
            
            # 가우시안 보간
            centers, scales, rotations, colors, opacities = self.interpolate_gaussians(
                centers1, scales1, rotations1, colors1, opacities1,
                centers2, scales2, rotations2, colors2, opacities2,
                t
            )
            
            # 렌더링
            frame = self.render_gaussians(centers, scales, rotations, colors, opacities)
            frames.append(frame)
            
        return frames

def save_frames_as_images(frames, output_dir='output_frames'):
    # 출력 디렉토리 생성 (없으면)
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # 프레임 이미지로 저장
    for i, frame in enumerate(frames):
        # 파일명 포맷: frame_0000.png, frame_0001.png 등
        filename = os.path.join(output_dir, f'frame_{i:04d}.png')
        
        # 프레임을 넘파이 배열로 변환 및 이미지로 저장
        import numpy as np
        from PIL import Image
        
        # 텐서를 넘파이 배열로 변환 및 스케일링
        frame_np = frame.detach().cpu().numpy()
        frame_np = (frame_np * 255).astype(np.uint8)
        
        # 이미지 저장
        Image.fromarray(frame_np).save(filename)
    
    print(f"총 {len(frames)}개의 프레임을 {output_dir} 디렉토리에 저장했습니다.")

def save_frames_as_gif(frames, output_path='output_animation.gif', duration=50):
    """
    프레임들을 GIF 애니메이션으로 저장합니다.
    
    Parameters:
    - frames: 보간된 프레임들
    - output_path: 저장할 GIF 파일 경로
    - duration: 각 프레임 사이의 지속 시간 (밀리초)
    """
    import numpy as np
    from PIL import Image
    
    # 이미지 리스트 생성
    gif_images = []
    
    for frame in frames:
        # 텐서를 넘파이 배열로 변환 및 스케일링
        frame_np = frame.detach().cpu().numpy()
        frame_np = (frame_np * 255).astype(np.uint8)
        
        # PIL 이미지로 변환
        pil_image = Image.fromarray(frame_np)
        gif_images.append(pil_image)
    
    # 첫 번째 이미지로 GIF 저장 (후속 프레임들 추가)
    gif_images[0].save(
        output_path, 
        save_all=True, 
        append_images=gif_images[1:], 
        duration=duration, 
        loop=0  # 무한 반복
    )
    
    print(f"GIF 애니메이션을 {output_path}에 저장했습니다.")

# 사용 예시
def main():
    """
    # 샘플 메시 데이터 (실제로는 파일에서 로드)
    # 간단한 큐브 메시 예시
    vertices1 = np.array([
        [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
        [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]
    ], dtype=np.float32)
    
    faces = np.array([
        [0, 1, 2], [0, 2, 3], [4, 5, 6], [4, 6, 7],
        [0, 1, 5], [0, 5, 4], [2, 3, 7], [2, 7, 6],
        [0, 3, 7], [0, 7, 4], [1, 2, 6], [1, 6, 5]
    ], dtype=np.int64)
    
    # 두 번째 메시는 첫 번째 메시를 약간 변형
    vertices2 = vertices1.copy()
    vertices2[:, 0] *= 1.5  # x 방향으로 늘리기
    vertices2[:, 1] += 0.5  # y 방향으로 이동
    
    # 색상 추가
    colors1 = np.ones_like(vertices1) * 0.5
    colors2 = np.ones_like(vertices2) * 0.7
    
    # 가우시안 스플래팅 객체 생성
    gs = GaussianSplatting()
    
    # 메시 로드
    mesh1 = gs.load_mesh(vertices1, faces, colors1)
    mesh2 = gs.load_mesh(vertices2, faces, colors2)
    """
    
    # GaussianSplatting 클래스 인스턴스 생성
    gs = GaussianSplatting()
    
    # OBJ 또는 GLTF 파일에서 메시 로드
    mesh1 = gs.load_mesh_from_file('path/to/first/mesh.obj')
    mesh2 = gs.load_mesh_from_file('path/to/second/mesh.gltf')
    
    # 프레임 보간
    frames = gs.interpolate_meshes(mesh1, mesh2, num_frames=30)
    
    print(f"생성된 프레임 수: {len(frames)}")
    
    # 프레임을 이미지로 저장
    save_frames_as_images(frames)
    
    # GIF로 저장 (옵션: 출력 경로, 프레임 지속 시간 커스터마이징 가능)
    save_frames_as_gif(frames, 'mesh_interpolation.gif', duration=50)    
    
if __name__ == "__main__":
    main()
