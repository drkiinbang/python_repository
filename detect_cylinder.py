import open3d as o3d
import numpy as np
from scipy.spatial.transform import Rotation

def load_mesh(filename):
    """.obj 파일로부터 메쉬 데이터를 로드합니다."""
    mesh = o3d.io.read_triangle_mesh(filename)
    if not mesh.has_vertex_normals():
        mesh.compute_vertex_normals()
    return mesh

def fit_cylinder(vertices):
    """
    입력된 정점 집합을 통해 실린더를 감지합니다.ins
    원통을 찾기 위해 축 방향을 분석하고,
    정점이 특정 반경 내에 있는지 확인합니다.
    """
    # PCA(주성분 분석)로 축 방향 추출
    center = vertices.mean(axis=0)
    centered_vertices = vertices - center
    cov_matrix = np.cov(centered_vertices, rowvar=False)
    eigvals, eigvecs = np.linalg.eigh(cov_matrix)

    # 가장 큰 고유값을 가진 축을 실린더 축으로 가정
    axis = eigvecs[:, np.argmax(eigvals)]

    # 각 점들이 축에서 얼마나 떨어져 있는지 계산 (직교 거리)
    distances = np.linalg.norm(np.cross(centered_vertices, axis), axis=1)
    radius = np.mean(distances)

    # 원통성을 판단하는 임계값 설정
    tolerance = 0.01
    if np.all(np.abs(distances - radius) < tolerance):
        return axis, center, radius
    else:
        return None

def detect_cylinder_in_mesh(mesh):
    """메쉬의 정점에서 실린더를 탐지합니다."""
    vertices = np.asarray(mesh.vertices)
    result = fit_cylinder(vertices)
    if result:
        axis, center, radius = result
        print(f"실린더 감지됨: 축 방향={axis}, 중심={center}, 반경={radius}")
    else:
        print("실린더를 찾을 수 없습니다.")

def main():
    filename = "C:\\Users\\kiinb\\OneDrive\\Conworth since 2022\\Works\\현대오토에버_Auto Rigging\\제안서 작업 폴더\\참고자료\\현대오토에버 샘플 데이터\\Unnamed-MXP710L-A001_test.obj"  # 분석할 .obj 파일 경로
    mesh = load_mesh(filename)
    detect_cylinder_in_mesh(mesh)

if __name__ == "__main__":
    main()
