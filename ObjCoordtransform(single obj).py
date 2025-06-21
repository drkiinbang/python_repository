import numpy as np
import tkinter as tk
from tkinter import filedialog
import xml.etree.ElementTree as ET

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
    o,p,k = np.deg2rad([rz, ry, rx])   # Z-Y-X
    co,cp,ck = np.cos([o,p,k])
    so,sp,sk = np.sin([o,p,k])
    return np.array([[ cp*ck,           -cp*sk,          sp     ],
                     [ so*sp*ck+co*sk,  -so*sp*sk+co*ck, -so*cp ],
                     [-co*sp*ck+so*sk,   co*sp*sk+so*ck,  co*cp ]])

# ----------------- 메인 처리 -----------------
def main():
    root = tk.Tk(); root.withdraw()
    gx   = filedialog.askopenfilename(title="gxxml 선택", filetypes=[("gxxml","*.gxxml")])
    obji = filedialog.askopenfilename(title="OBJ 입력",   filetypes=[("obj","*.obj")])
    objo = filedialog.asksaveasfilename(title="저장 위치", defaultextension=".obj",
                                        filetypes=[("obj","*.obj")])
    if not (gx and obji and objo): return print("필수 경로가 누락됐습니다.")

    m = extract_transform_values_from_gxxml(gx)
    if any(m[k] is None for k in ['sx','sy','sz','rx','ry','rz','tx','ty','tz']):
        return print("gxxml에서 변환정보를 읽을 수 없습니다.")

    S = np.array([m['sx'], m['sy'], m['sz']])
    T = np.array([m['tx'], m['ty'], m['tz']])
    R = euler_zyx(m['rx'], m['ry'], m['rz'])

    def transform(v):           # v: (3,) numpy array
        return (R @ (v * S)) + T

    with open(obji) as fi, open(objo,'w') as fo:
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
    print("변환 완료 →", objo)

if __name__ == "__main__":
    main()