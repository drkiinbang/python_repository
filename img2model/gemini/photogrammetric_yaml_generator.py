import numpy as np
import yaml
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import math
import os
from datetime import datetime

class PhotogrammetricYAMLGenerator:
    """
    Photogrammetric Orientation Parameters를 사용하여 YAML 설정파일을 생성하는 클래스
    
    Parameters:
    - X, Y, Z: 카메라 위치 (투영 중심)
    - omega (ω): X축 회전각 (roll)
    - phi (φ): Y축 회전각 (pitch) 
    - kappa (κ): Z축 회전각 (yaw)
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Photogrammetric YAML Generator")
        self.root.geometry("600x800")
        self.root.resizable(True, True)
        
        # 변수 초기화
        self.setup_variables()
        
        # GUI 구성
        self.create_widgets()
        
        # 기본 카메라 파라미터 설정
        self.load_default_values()
    
    def setup_variables(self):
        """GUI 변수들 초기화"""
        # Exterior Orientation Parameters
        self.var_x = tk.DoubleVar(value=0.0)
        self.var_y = tk.DoubleVar(value=0.0)
        self.var_z = tk.DoubleVar(value=5.0)
        self.var_omega = tk.DoubleVar(value=0.0)
        self.var_phi = tk.DoubleVar(value=0.0)
        self.var_kappa = tk.DoubleVar(value=0.0)
        
        # 각도 단위
        self.angle_unit = tk.StringVar(value="degrees")
        
        # 카메라 파라미터
        self.var_focal_length = tk.DoubleVar(value=50.0)  # mm
        self.var_sensor_width = tk.DoubleVar(value=35.0)  # mm
        self.var_sensor_height = tk.DoubleVar(value=24.0)  # mm
        
        # 렌더링 설정
        self.var_render_width = tk.IntVar(value=1920)
        self.var_render_height = tk.IntVar(value=1080)
        self.var_output_filename = tk.StringVar(value="photogrammetric_render.png")
        
        # Look-at 타겟
        self.var_target_x = tk.DoubleVar(value=0.0)
        self.var_target_y = tk.DoubleVar(value=0.0)
        self.var_target_z = tk.DoubleVar(value=0.0)
        
        # 자동 Look-at 계산 옵션
        self.auto_lookat = tk.BooleanVar(value=True)

        # Boresight offset (기본값: 0)
        self.var_boresight_omega = tk.DoubleVar(value=0.0)
        self.var_boresight_phi = tk.DoubleVar(value=0.0)
        self.var_boresight_kappa = tk.DoubleVar(value=0.0)
    
    def create_widgets(self):
        """GUI 위젯들 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 스크롤 가능한 프레임 설정
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 제목
        title_label = ttk.Label(scrollable_frame, text="Photogrammetric YAML Generator", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        row = 1
        
        # Exterior Orientation Parameters 섹션
        row = self.create_eop_section(scrollable_frame, row)
        
        # 카메라 파라미터 섹션
        row = self.create_camera_section(scrollable_frame, row)
        
        # Look-at 타겟 섹션
        row = self.create_lookat_section(scrollable_frame, row)
        
        # 렌더링 설정 섹션
        row = self.create_render_section(scrollable_frame, row)
        
        # 버튼 섹션
        self.create_button_section(scrollable_frame, row)
        
        # 스크롤바 설정
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
    
    def create_eop_section(self, parent, start_row):
        """Exterior Orientation Parameters 섹션 생성"""
        # 섹션 제목
        eop_frame = ttk.LabelFrame(parent, text="Exterior Orientation Parameters", padding="10")
        eop_frame.grid(row=start_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 위치 파라미터
        ttk.Label(eop_frame, text="Position (Projection Center):").grid(row=0, column=0, columnspan=3, sticky=tk.W)
        
        ttk.Label(eop_frame, text="X:").grid(row=1, column=0, sticky=tk.W, padx=(20, 5))
        ttk.Entry(eop_frame, textvariable=self.var_x, width=15).grid(row=1, column=1, padx=5)
        ttk.Label(eop_frame, text="(world units)").grid(row=1, column=2, sticky=tk.W)
        
        ttk.Label(eop_frame, text="Y:").grid(row=2, column=0, sticky=tk.W, padx=(20, 5))
        ttk.Entry(eop_frame, textvariable=self.var_y, width=15).grid(row=2, column=1, padx=5)
        ttk.Label(eop_frame, text="(world units)").grid(row=2, column=2, sticky=tk.W)
        
        ttk.Label(eop_frame, text="Z:").grid(row=3, column=0, sticky=tk.W, padx=(20, 5))
        ttk.Entry(eop_frame, textvariable=self.var_z, width=15).grid(row=3, column=1, padx=5)
        ttk.Label(eop_frame, text="(world units)").grid(row=3, column=2, sticky=tk.W)
        
        # 회전 파라미터
        ttk.Label(eop_frame, text="Rotation Angles:").grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=(10, 0))
        
        ttk.Label(eop_frame, text="ω (omega):").grid(row=5, column=0, sticky=tk.W, padx=(20, 5))
        ttk.Entry(eop_frame, textvariable=self.var_omega, width=15).grid(row=5, column=1, padx=5)
        ttk.Label(eop_frame, text="(X-axis rotation)").grid(row=5, column=2, sticky=tk.W)
        
        ttk.Label(eop_frame, text="φ (phi):").grid(row=6, column=0, sticky=tk.W, padx=(20, 5))
        ttk.Entry(eop_frame, textvariable=self.var_phi, width=15).grid(row=6, column=1, padx=5)
        ttk.Label(eop_frame, text="(Y-axis rotation)").grid(row=6, column=2, sticky=tk.W)
        
        ttk.Label(eop_frame, text="κ (kappa):").grid(row=7, column=0, sticky=tk.W, padx=(20, 5))
        ttk.Entry(eop_frame, textvariable=self.var_kappa, width=15).grid(row=7, column=1, padx=5)
        ttk.Label(eop_frame, text="(Z-axis rotation)").grid(row=7, column=2, sticky=tk.W)
        
        # 각도 단위 선택
        ttk.Label(eop_frame, text="Angle Unit:").grid(row=8, column=0, sticky=tk.W, pady=(10, 0))
        angle_combo = ttk.Combobox(eop_frame, textvariable=self.angle_unit, 
                                  values=["degrees", "radians"], state="readonly", width=12)
        angle_combo.grid(row=8, column=1, padx=5, pady=(10, 0), sticky=tk.W)

        # Boresight 보정 회전
        ttk.Label(eop_frame, text="Boresight Correction (Optional):").grid(row=9, column=0, columnspan=3, sticky=tk.W, pady=(10, 0))

        ttk.Label(eop_frame, text="ω_b:").grid(row=10, column=0, sticky=tk.W, padx=(20, 5))
        ttk.Entry(eop_frame, textvariable=self.var_boresight_omega, width=15).grid(row=10, column=1, padx=5)

        ttk.Label(eop_frame, text="φ_b:").grid(row=11, column=0, sticky=tk.W, padx=(20, 5))
        ttk.Entry(eop_frame, textvariable=self.var_boresight_phi, width=15).grid(row=11, column=1, padx=5)

        ttk.Label(eop_frame, text="κ_b:").grid(row=12, column=0, sticky=tk.W, padx=(20, 5))
        ttk.Entry(eop_frame, textvariable=self.var_boresight_kappa, width=15).grid(row=12, column=1, padx=5)
        
        return start_row + 1
    
    def create_camera_section(self, parent, start_row):
        """카메라 파라미터 섹션 생성"""
        camera_frame = ttk.LabelFrame(parent, text="Camera Parameters", padding="10")
        camera_frame.grid(row=start_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(camera_frame, text="Focal Length:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(camera_frame, textvariable=self.var_focal_length, width=15).grid(row=0, column=1, padx=5)
        ttk.Label(camera_frame, text="mm").grid(row=0, column=2, sticky=tk.W)
        
        ttk.Label(camera_frame, text="Sensor Width:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(camera_frame, textvariable=self.var_sensor_width, width=15).grid(row=1, column=1, padx=5)
        ttk.Label(camera_frame, text="mm").grid(row=1, column=2, sticky=tk.W)
        
        ttk.Label(camera_frame, text="Sensor Height:").grid(row=2, column=0, sticky=tk.W)
        ttk.Entry(camera_frame, textvariable=self.var_sensor_height, width=15).grid(row=2, column=1, padx=5)
        ttk.Label(camera_frame, text="mm").grid(row=2, column=2, sticky=tk.W)
        
        return start_row + 1
    
    def create_lookat_section(self, parent, start_row):
        """Look-at 타겟 섹션 생성"""
        lookat_frame = ttk.LabelFrame(parent, text="Look-at Target", padding="10")
        lookat_frame.grid(row=start_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Checkbutton(lookat_frame, text="Auto-calculate look-at direction", 
                       variable=self.auto_lookat, command=self.on_auto_lookat_change).grid(row=0, column=0, columnspan=3, sticky=tk.W)
        
        self.target_x_label = ttk.Label(lookat_frame, text="Target X:")
        self.target_x_label.grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.target_x_entry = ttk.Entry(lookat_frame, textvariable=self.var_target_x, width=15)
        self.target_x_entry.grid(row=1, column=1, padx=5, pady=(10, 0))
        
        self.target_y_label = ttk.Label(lookat_frame, text="Target Y:")
        self.target_y_label.grid(row=2, column=0, sticky=tk.W)
        self.target_y_entry = ttk.Entry(lookat_frame, textvariable=self.var_target_y, width=15)
        self.target_y_entry.grid(row=2, column=1, padx=5)
        
        self.target_z_label = ttk.Label(lookat_frame, text="Target Z:")
        self.target_z_label.grid(row=3, column=0, sticky=tk.W)
        self.target_z_entry = ttk.Entry(lookat_frame, textvariable=self.var_target_z, width=15)
        self.target_z_entry.grid(row=3, column=1, padx=5)
        
        return start_row + 1
    
    def create_render_section(self, parent, start_row):
        """렌더링 설정 섹션 생성"""
        render_frame = ttk.LabelFrame(parent, text="Render Settings", padding="10")
        render_frame.grid(row=start_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(render_frame, text="Width:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(render_frame, textvariable=self.var_render_width, width=15).grid(row=0, column=1, padx=5)
        ttk.Label(render_frame, text="pixels").grid(row=0, column=2, sticky=tk.W)
        
        ttk.Label(render_frame, text="Height:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(render_frame, textvariable=self.var_render_height, width=15).grid(row=1, column=1, padx=5)
        ttk.Label(render_frame, text="pixels").grid(row=1, column=2, sticky=tk.W)
        
        ttk.Label(render_frame, text="Output File:").grid(row=2, column=0, sticky=tk.W)
        ttk.Entry(render_frame, textvariable=self.var_output_filename, width=30).grid(row=2, column=1, columnspan=2, padx=5, sticky=(tk.W, tk.E))
        
        return start_row + 1
    
    def create_button_section(self, parent, start_row):
        """버튼 섹션 생성"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=start_row, column=0, columnspan=3, pady=20)
        
        ttk.Button(button_frame, text="Load Preset", command=self.load_preset).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Preview Settings", command=self.preview_settings).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Generate YAML", command=self.generate_yaml).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Exit", command=self.root.quit).grid(row=0, column=3, padx=5)
    
    def on_auto_lookat_change(self):
        """Auto look-at 체크박스 변경 시 호출"""
        if self.auto_lookat.get():
            # 비활성화
            self.target_x_entry.config(state='disabled')
            self.target_y_entry.config(state='disabled')
            self.target_z_entry.config(state='disabled')
        else:
            # 활성화
            self.target_x_entry.config(state='normal')
            self.target_y_entry.config(state='normal')
            self.target_z_entry.config(state='normal')
    
    def load_default_values(self):
        """기본값 로드"""
        self.on_auto_lookat_change()
    
    def load_preset(self):
        """프리셋 로드"""
        presets = {
            "Aerial Nadir": {
                "X": 0, "Y": 0, "Z": 100,
                "omega": 0, "phi": 0, "kappa": 0,
                "target": [0, 0, 0]
            },
            "Aerial Oblique": {
                "X": 50, "Y": 50, "Z": 80,
                "omega": -15, "phi": -20, "kappa": 45,
                "target": [0, 0, 0]
            },
            "Terrestrial": {
                "X": 10, "Y": 0, "Z": 2,
                "omega": 0, "phi": -5, "kappa": 0,
                "target": [0, 0, 0]
            },
            "Close Range": {
                "X": 2, "Y": 2, "Z": 2,
                "omega": -30, "phi": -30, "kappa": 0,
                "target": [0, 0, 0]
            }
        }
        
        # 프리셋 선택 창
        preset_window = tk.Toplevel(self.root)
        preset_window.title("Select Preset")
        preset_window.geometry("300x200")
        
        ttk.Label(preset_window, text="Choose a preset:").pack(pady=10)
        
        preset_var = tk.StringVar()
        for preset_name in presets.keys():
            ttk.Radiobutton(preset_window, text=preset_name, 
                           variable=preset_var, value=preset_name).pack(anchor=tk.W, padx=20)
        
        def apply_preset():
            selected = preset_var.get()
            if selected and selected in presets:
                preset = presets[selected]
                self.var_x.set(preset["X"])
                self.var_y.set(preset["Y"])
                self.var_z.set(preset["Z"])
                self.var_omega.set(preset["omega"])
                self.var_phi.set(preset["phi"])
                self.var_kappa.set(preset["kappa"])
                self.var_target_x.set(preset["target"][0])
                self.var_target_y.set(preset["target"][1])
                self.var_target_z.set(preset["target"][2])
                preset_window.destroy()
        
        ttk.Button(preset_window, text="Apply", command=apply_preset).pack(pady=20)
    
    def deg_to_rad(self, angle_deg):
        """도를 라디안으로 변환"""
        return math.radians(angle_deg)
    
    def get_rotation_angles(self):
        """각도 단위에 따라 회전각 반환"""
        omega = self.var_omega.get()
        phi = self.var_phi.get()
        kappa = self.var_kappa.get()
        
        if self.angle_unit.get() == "degrees":
            return self.deg_to_rad(omega), self.deg_to_rad(phi), self.deg_to_rad(kappa)
        else:
            return omega, phi, kappa
    
    def calculate_rotation_matrix(self, omega, phi, kappa):
        """회전 행렬 계산 (photogrammetric convention)"""
        # 회전 행렬: R = R_z(kappa) * R_y(phi) * R_x(omega)
        cos_o, sin_o = math.cos(omega), math.sin(omega)
        cos_p, sin_p = math.cos(phi), math.sin(phi)
        cos_k, sin_k = math.cos(kappa), math.sin(kappa)
        
        # X축 회전 (omega)
        R_x = np.array([
            [1, 0, 0],
            [0, cos_o, -sin_o],
            [0, sin_o, cos_o]
        ])
        
        # Y축 회전 (phi)
        R_y = np.array([
            [cos_p, 0, sin_p],
            [0, 1, 0],
            [-sin_p, 0, cos_p]
        ])
        
        # Z축 회전 (kappa)
        R_z = np.array([
            [cos_k, -sin_k, 0],
            [sin_k, cos_k, 0],
            [0, 0, 1]
        ])
        
        # 전체 회전 행렬
        R = R_z @ R_y @ R_x
        return R
    
    def calculate_camera_parameters(self):
        """카메라 파라미터 계산"""
        # 카메라 위치
        camera_pos = [self.var_x.get(), self.var_y.get(), self.var_z.get()]
        
        # 회전각 (라디안)
        omega, phi, kappa = self.get_rotation_angles()
        
        # 기본 회전 행렬
        R_main = self.calculate_rotation_matrix(omega, phi, kappa)

        # Boresight 회전 적용
        bo_omega = self.deg_to_rad(self.var_boresight_omega.get())
        bo_phi = self.deg_to_rad(self.var_boresight_phi.get())
        bo_kappa = self.deg_to_rad(self.var_boresight_kappa.get())
        R_boresight = self.calculate_rotation_matrix(bo_omega, bo_phi, bo_kappa)

        # 전체 회전 = photogrammetric R * boresight R
        R = R_main @ R_boresight
        
        if self.auto_lookat.get():
            # 카메라의 전방 벡터 계산 (카메라 좌표계의 -Z 방향)
            forward_vector = R @ np.array([0, 0, -1])
            look_at = np.array(camera_pos) + forward_vector
        else:
            look_at = [self.var_target_x.get(), self.var_target_y.get(), self.var_target_z.get()]
        
        # Up 벡터 계산 (카메라 좌표계의 Y 방향)
        up_vector = R @ np.array([0, 1, 0])
        
        # FOV 계산
        focal_length = self.var_focal_length.get()
        sensor_width = self.var_sensor_width.get()
        fov = 2 * math.atan(sensor_width / (2 * focal_length))
        fov_degrees = math.degrees(fov)
        
        return {
            'camera_pos': camera_pos,
            'look_at': look_at.tolist() if isinstance(look_at, np.ndarray) else look_at,
            'up_vector': up_vector.tolist(),
            'fov': fov_degrees
        }
    
    def preview_settings(self):
        """설정 미리보기"""
        try:
            params = self.calculate_camera_parameters()
            
            preview_text = f"""
Camera Position: {params['camera_pos']}
Look At: {params['look_at']}
Up Vector: {params['up_vector']}
FOV: {params['fov']:.2f}°

Photogrammetric Parameters:
X: {self.var_x.get()}
Y: {self.var_y.get()}
Z: {self.var_z.get()}
ω: {self.var_omega.get()}° 
φ: {self.var_phi.get()}°
κ: {self.var_kappa.get()}°
            """
            
            messagebox.showinfo("Camera Settings Preview", preview_text)
        except Exception as e:
            messagebox.showerror("Error", f"Error calculating parameters: {str(e)}")
    
    def generate_yaml(self):
        """YAML 파일 생성"""
        try:
            # 카메라 파라미터 계산
            params = self.calculate_camera_parameters()
            
            # YAML 구조 생성
            yaml_data = {
                'metadata': {
                    'generated_by': 'Photogrammetric YAML Generator',
                    'timestamp': datetime.now().isoformat(),
                    'photogrammetric_parameters': {
                        'position': {
                            'X': float(self.var_x.get()), 'Y': float(self.var_y.get()), 'Z': float(self.var_z.get())
                        },
                        'rotation': {
                            'omega': float(self.var_omega.get()),
                            'phi': float(self.var_phi.get()),
                            'kappa': float(self.var_kappa.get()),
                            'unit': self.angle_unit.get()
                        },
                        'camera': {
                            'focal_length_mm': float(self.var_focal_length.get()),
                            'sensor_width_mm': float(self.var_sensor_width.get()),
                            'sensor_height_mm': float(self.var_sensor_height.get())
                        }
                    }
                },
                'camera_settings': {
                    'position': params['camera_pos'],
                    'look_at': params['look_at'],
                    'up_vector': params['up_vector'],
                    'fov': float(params['fov'])
                },
                'render_width': int(self.var_render_width.get()),
                'render_height': int(self.var_render_height.get()),
                'output_filename': str(self.var_output_filename.get())
            }
            
            # 파일 저장 대화상자
            filename = filedialog.asksaveasfilename(
                title="Save YAML Configuration",
                defaultextension=".yaml",
                filetypes=[("YAML files", "*.yaml"), ("YML files", "*.yml"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    yaml.dump(yaml_data, f, default_flow_style=False, indent=2, sort_keys=False)
                
                messagebox.showinfo("Success", f"YAML configuration saved to:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error generating YAML: {str(e)}")
    
    def run(self):
        """GUI 실행"""
        self.root.mainloop()

def main():
    """메인 함수"""
    print("Starting Photogrammetric YAML Generator...")
    app = PhotogrammetricYAMLGenerator()
    app.run()

if __name__ == "__main__":
    main()