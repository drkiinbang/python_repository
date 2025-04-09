import trimesh
import numpy as np
from sklearn.decomposition import PCA

# === 1. GLB 파일 로드 ===
mesh = trimesh.load("F:\\Users\\bbarab\\Downloads\\samsung_test\\glb2\\덕트_부속_1_0_W_15716653.glb")

# === 2. 면 법선 벡터 확인 및 계산 ===
if hasattr(mesh, 'face_normals') and mesh.face_normals is not None and len(mesh.face_normals) > 0:
    face_normals = mesh.face_normals
else:
    print("⚠️ face_normals가 없어 직접 계산합니다.")
    # vertices와 faces로부터 법선 계산
    triangles = mesh.triangles  # (M, 3, 3)
    v1 = triangles[:, 1] - triangles[:, 0]
    v2 = triangles[:, 2] - triangles[:, 0]
    normals = np.cross(v1, v2)
    # 정규화
    norms = np.linalg.norm(normals, axis=1, keepdims=True)
    face_normals = normals / (norms + 1e-8)  # 0 나눗셈 방지용 작은 수 추가

# === 3. PCA 수행 ===
pca = PCA(n_components=3)
pca.fit(face_normals)

# === 4. 결과 출력 ===
print("📌 주성분 벡터 (Principal Axes):")
print(pca.components_)  # 각 행: 주성분 방향 벡터

print("\n📈 고유값 (분산량):")
print(pca.explained_variance_)  # 각 방향의 분산 크기

print("\n🔁 설명된 분산 비율:")
print(pca.explained_variance_ratio_)  # 전체 분산에서 각 주성분이 차지하는 비율
