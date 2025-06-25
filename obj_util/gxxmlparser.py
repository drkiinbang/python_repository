import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional

@dataclass
class Transform:
    """변환 정보를 저장하는 데이터 클래스"""
    tx: float  # X축 이동
    ty: float  # Y축 이동
    tz: float  # Z축 이동
    rx: float  # X축 회전
    ry: float  # Y축 회전
    rz: float  # Z축 회전
    sx: float  # X축 스케일
    sy: float  # Y축 스케일
    sz: float  # Z축 스케일
    srid: str  # 공간 참조 식별자

@dataclass
class Front:
    """전면 방향 정보를 저장하는 데이터 클래스"""
    forward_x: float
    forward_y: float
    forward_z: float
    up_x: float
    up_y: float
    up_z: float

@dataclass
class ModelCenter:
    """모델 중심점 정보를 저장하는 데이터 클래스"""
    x: float
    y: float
    z: float

@dataclass
class SceneNode:
    """장면 노드 정보를 저장하는 데이터 클래스"""
    transform: Transform
    front: Front
    model_center: ModelCenter

@dataclass
class GXXMLData:
    """전체 GXXML 데이터를 저장하는 데이터 클래스"""
    product: str
    scene_node: SceneNode

class GXXMLParser:
    """GXXML 파일을 파싱하는 클래스"""
    
    def __init__(self):
        pass
    
    def parse_transform(self, transform_element) -> Transform:
        """Transform 요소를 파싱"""
        return Transform(
            tx=float(transform_element.get('tx', 0)),
            ty=float(transform_element.get('ty', 0)),
            tz=float(transform_element.get('tz', 0)),
            rx=float(transform_element.get('rx', 0)),
            ry=float(transform_element.get('ry', 0)),
            rz=float(transform_element.get('rz', 0)),
            sx=float(transform_element.get('sx', 1)),
            sy=float(transform_element.get('sy', 1)),
            sz=float(transform_element.get('sz', 1)),
            srid=transform_element.get('srid', '')
        )
    
    def parse_front(self, front_element) -> Front:
        """Front 요소를 파싱"""
        return Front(
            forward_x=float(front_element.get('forwardx', 0)),
            forward_y=float(front_element.get('forwardy', 0)),
            forward_z=float(front_element.get('forwardz', 0)),
            up_x=float(front_element.get('upx', 0)),
            up_y=float(front_element.get('upy', 0)),
            up_z=float(front_element.get('upz', 0))
        )
    
    def parse_model_center(self, center_element) -> ModelCenter:
        """ModelCenter 요소를 파싱"""
        return ModelCenter(
            x=float(center_element.get('x', 0)),
            y=float(center_element.get('y', 0)),
            z=float(center_element.get('z', 0))
        )
    
    def parse_scene_node(self, scene_node_element) -> SceneNode:
        """SceneNode 요소를 파싱"""
        transform_elem = scene_node_element.find('Transform')
        front_elem = scene_node_element.find('Front')
        center_elem = scene_node_element.find('ModelCenter')
        
        if transform_elem is None or front_elem is None or center_elem is None:
            raise ValueError("필수 요소가 누락되었습니다: Transform, Front, ModelCenter")
        
        return SceneNode(
            transform=self.parse_transform(transform_elem),
            front=self.parse_front(front_elem),
            model_center=self.parse_model_center(center_elem)
        )
    
    def parse_file(self, file_path: str) -> GXXMLData:
        """GXXML 파일을 파싱하여 데이터 구조체로 반환"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # GIX 요소 찾기
            gix_element = root.find('GIX')
            if gix_element is None:
                raise ValueError("GIX 요소를 찾을 수 없습니다")
            
            # product 속성 가져오기
            product = gix_element.get('product', '')
            
            # SceneNode 요소 찾기
            scene_node_element = gix_element.find('SceneNode')
            if scene_node_element is None:
                raise ValueError("SceneNode 요소를 찾을 수 없습니다")
            
            scene_node = self.parse_scene_node(scene_node_element)
            
            return GXXMLData(
                product=product,
                scene_node=scene_node
            )
            
        except ET.ParseError as e:
            raise ValueError(f"XML 파싱 오류: {e}")
    
    def parse_string(self, xml_string: str) -> GXXMLData:
        """XML 문자열을 파싱하여 데이터 구조체로 반환"""
        try:
            root = ET.fromstring(xml_string)
            
            # GIX 요소 찾기
            gix_element = root.find('GIX')
            if gix_element is None:
                raise ValueError("GIX 요소를 찾을 수 없습니다")
            
            # product 속성 가져오기
            product = gix_element.get('product', '')
            
            # SceneNode 요소 찾기
            scene_node_element = gix_element.find('SceneNode')
            if scene_node_element is None:
                raise ValueError("SceneNode 요소를 찾을 수 없습니다")
            
            scene_node = self.parse_scene_node(scene_node_element)
            
            return GXXMLData(
                product=product,
                scene_node=scene_node
            )
            
        except ET.ParseError as e:
            raise ValueError(f"XML 파싱 오류: {e}")

def pretty_print_gxxml_data(data: GXXMLData):
    """GXXML 데이터를 보기 좋게 출력"""
    print("=== GXXML 파싱 결과 ===")
    print(f"제품: {data.product}")
    print()
    
    print("변환 정보:")
    t = data.scene_node.transform
    print(f"  위치: ({t.tx}, {t.ty}, {t.tz})")
    print(f"  회전: ({t.rx}°, {t.ry}°, {t.rz}°)")
    print(f"  스케일: ({t.sx}, {t.sy}, {t.sz})")
    print(f"  SRID: {t.srid}")
    print()
    
    print("전면 방향:")
    f = data.scene_node.front
    print(f"  전진 벡터: ({f.forward_x}, {f.forward_y}, {f.forward_z})")
    print(f"  상향 벡터: ({f.up_x}, {f.up_y}, {f.up_z})")
    print()
    
    print("모델 중심점:")
    c = data.scene_node.model_center
    print(f"  중심: ({c.x}, {c.y}, {c.z})")

def select_gxxml_file() -> Optional[str]:
    """파일 다이얼로그를 통해 GXXML 파일 선택"""
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        # tkinter 루트 윈도우 생성 (숨김)
        root = tk.Tk()
        root.withdraw()  # 메인 윈도우 숨기기
        
        # 파일 다이얼로그 열기
        file_path = filedialog.askopenfilename(
            title="GXXML 파일 선택",
            filetypes=[
                ("GXXML files", "*.gxxml"),
                ("XML files", "*.xml"),
                ("All files", "*.*")
            ],
            initialdir=os.getcwd()
        )
        
        return file_path if file_path else None
        
    except ImportError:
        print("tkinter 모듈을 사용할 수 없습니다. 파일 경로를 직접 입력해주세요.")
        return None

def get_file_path_from_input() -> Optional[str]:
    """사용자 입력을 통해 파일 경로 받기 (tkinter 사용 불가 시)"""
    print("GXXML 파일의 전체 경로를 입력해주세요:")
    file_path = input("파일 경로: ").strip()
    
    if not file_path:
        return None
    
    # 따옴표 제거 (드래그&드롭 시 자동으로 추가되는 경우)
    file_path = file_path.strip('"\'')
    
    return file_path if os.path.exists(file_path) else None

def main():
    """메인 실행 함수"""
    print("=== GXXML 파일 파서 ===")
    print("GXXML 파일을 선택하여 파싱합니다.\n")
    
    parser = GXXMLParser()
    file_path = None
    
    # 파일 선택 시도
    file_path = select_gxxml_file()
    
    # 파일 다이얼로그가 실패하거나 취소된 경우
    if not file_path:
        print("파일 다이얼로그를 사용할 수 없거나 취소되었습니다.")
        file_path = get_file_path_from_input()
    
    if not file_path:
        print("파일이 선택되지 않았습니다. 프로그램을 종료합니다.")
        return
    
    if not os.path.exists(file_path):
        print(f"파일을 찾을 수 없습니다: {file_path}")
        return
    
    try:
        print(f"선택된 파일: {file_path}")
        print("파일을 파싱 중...")
        
        # 파일 파싱
        data = parser.parse_file(file_path)
        
        print("\n파싱 완료!")
        pretty_print_gxxml_data(data)
        
        # 개별 데이터 접근 예제
        print("\n=== 주요 데이터 요약 ===")
        print(f"제품: {data.product}")
        t = data.scene_node.transform
        print(f"위치: ({t.tx:.2f}, {t.ty:.2f}, {t.tz:.2f})")
        print(f"회전 (X축): {t.rx:.3f}도")
        print(f"회전 (Y축): {t.ry:.3f}도")
        print(f"회전 (Z축): {t.rz:.3f}도")
        print(f"스케일: ({t.sx}, {t.sy}, {t.sz})")
        print(f"SRID: {t.srid}")
        f = data.scene_node.front
        print(f"전진 벡터: ({f.forward_x}, {f.forward_y}, {f.forward_z})")
        print(f"상향 벡터: ({f.up_x}, {f.up_y}, {f.up_z})")
        c = data.scene_node.model_center
        print(f"모델중심: ({c.x}, {c.y}, {c.z})")
    
    
    
        
        # 다른 파일 처리 여부 확인
        while True:
            print("\n다른 파일을 처리하시겠습니까? (y/n): ", end="")
            choice = input().strip().lower()
            
            if choice in ['n', 'no', '아니오', '아니요']:
                break
            elif choice in ['y', 'yes', '예', '네']:
                file_path = select_gxxml_file()
                if file_path and os.path.exists(file_path):
                    try:
                        print(f"\n선택된 파일: {file_path}")
                        data = parser.parse_file(file_path)
                        pretty_print_gxxml_data(data)
                    except Exception as e:
                        print(f"파일 파싱 중 오류 발생: {e}")
                else:
                    print("파일이 선택되지 않았거나 존재하지 않습니다.")
            else:
                print("'y' 또는 'n'을 입력해주세요.")
        
        print("\n프로그램을 종료합니다.")
        
    except Exception as e:
        print(f"파일 파싱 중 오류 발생: {e}")
        print(f"오류 유형: {type(e).__name__}")

# 사용 예제 및 테스트
if __name__ == "__main__":
    main()