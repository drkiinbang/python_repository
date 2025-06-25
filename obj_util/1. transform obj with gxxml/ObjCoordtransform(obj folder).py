import os
import numpy as np
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import filedialog

# ----------------- 공통 유틸 -----------------
def extract_transform_values_from_gxxml(path):
    keys = ['tx','ty','tz','rx','ry','rz','sx','sy','sz',
            'forwardx','forwardy','forwardz','upx','upy','upz','x','y','z']
    vals = {k:None for k in keys}

    root = ET.parse(path).getroot()
    def walk(elem):
        for k in keys:
            if k in elem.attrib: vals[k] = float(elem.attrib[k])
        for c in elem: walk(c)
    walk(root);  return vals

def euler_zyx(rx, ry, rz):
    """deg → rad → 3×3 회전행렬"""
    o,p,k = np.deg2rad([rx, ry, rz])   # X-Y-Z
    co,cp,ck = np.cos([o,p,k])
    so,sp,sk = np.sin([o,p,k])
    return np.array([[ cp*ck,           -cp*sk,          sp     ],
                     [ so*sp*ck+co*sk,  -so*sp*sk+co*ck, -so*cp ],
                     [-co*sp*ck+so*sk,   co*sp*sk+so*ck,  co*cp ]])
    
def transform_obj(obj_path, gxxml_path, output_path):
    if not (gxxml_path and obj_path and output_path): return print("필수 경로가 누락됐습니다.")

    m = extract_transform_values_from_gxxml(gxxml_path)
    if any(m[k] is None for k in ['sx','sy','sz','rx','ry','rz','tx','ty','tz']):
        return print("gxxml에서 변환정보를 읽을 수 없습니다.")

    S = np.array([m['sx'], m['sy'], m['sz']])
    T = np.array([m['tx'], m['ty'], m['tz']])
    R = euler_zyx(m['rx'], m['ry'], m['rz'])
    
    def transform(v):           # v: (3,) numpy array
        return (R @ (v * S)) + T
    
    with open(obj_path) as fi, open(output_path,'w') as fo:
        for line in fi:
            if   line.startswith('v '):      # vertex
                v = np.fromstring(line[2:], sep=' ')
                v2 = transform(v)
                fo.write(f"v  {v2[0]:.6f} {v2[1]:.6f} {v2[2]:.6f}\n")
            elif line.startswith('vn '):     # normal
                n = np.fromstring(line[3:], sep=' ')
                n2 = R @ n                   # 회전만 적용
                fo.write(f"vn {n2[0]:.6f} {n2[1]:.6f} {n2[2]:.6f}\n")
            else:
                fo.write(line)
    print("변환 완료 →", output_path)
    print(f"[완료] {os.path.basename(output_path)} 저장됨")

def main():
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="변환할 obj 파일들이 있는 폴더를 선택하세요")

    if not folder_path:
        print("폴더를 선택하지 않았습니다.")
        return

    for file in os.listdir(folder_path):
        if file.lower().endswith(".obj"):
            obj_path = os.path.join(folder_path, file)
            base_name = os.path.splitext(file)[0]
            gxxml_path = os.path.join(folder_path, base_name + ".gxxml")
            if os.path.exists(gxxml_path):
                output_path = os.path.join(folder_path, base_name + "_Transformed.obj")
                transform_obj(obj_path, gxxml_path, output_path)
            else:
                print(f"[스킵] {file}: {base_name}.gxxml 없음")

if __name__ == "__main__":
    main()
