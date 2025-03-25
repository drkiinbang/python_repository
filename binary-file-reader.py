import struct
import pandas as pd
import tkinter as tk
from tkinter import filedialog, ttk

def read_binary_file(filename):
    try:
        with open(filename, 'rb') as file:
            # 3개의 float offset 값 읽기
            offset_x, offset_y, offset_z = struct.unpack('3f', file.read(12))
            
            # 좌표 데이터 읽기
            coordinates = []
            while True:
                coord_data = file.read(12)  # 3개의 float (x, y, z)
                if len(coord_data) < 12:
                    break
                
                x, y, z = struct.unpack('3f', coord_data)
                coordinates.append([x, y, z])
            
            return offset_x, offset_y, offset_z, coordinates
    except Exception as e:
        print(f"파일을 읽는 중 오류 발생: {e}")
        return None

def show_file_contents():
    # 파일 선택 대화상자 열기
    filename = filedialog.askopenfilename(title="이진 파일 선택")
    if not filename:
        return
    
    # 파일 내용 읽기
    result = read_binary_file(filename)
    if result is None:
        return
    
    offset_x, offset_y, offset_z, coordinates = result
    
    # 창 생성
    details_window = tk.Toplevel(root)
    details_window.title("이진 파일 내용")
    details_window.geometry("600x400")
    
    # Offset 정보 프레임
    offset_frame = tk.Frame(details_window)
    offset_frame.pack(pady=10)
    
    tk.Label(offset_frame, text=f"Offset X: {offset_x}").pack()
    tk.Label(offset_frame, text=f"Offset Y: {offset_y}").pack()
    tk.Label(offset_frame, text=f"Offset Z: {offset_z}").pack()
    
    # 좌표 테이블
    columns = ('Index', 'X', 'Y', 'Z')
    tree = ttk.Treeview(details_window, columns=columns, show='headings')
    
    # 각 열의 제목 설정
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor='center', width=100)
    
    # 좌표 데이터 추가
    for i, (x, y, z) in enumerate(coordinates, 1):
        tree.insert('', 'end', values=(i, x, y, z))
    
    # 스크롤바 추가
    scrollbar = ttk.Scrollbar(details_window, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    
    tree.pack(expand=True, fill='both', padx=10, pady=10)
    scrollbar.pack(side='right', fill='y')

# 메인 윈도우 생성
root = tk.Tk()
root.title("3D 좌표 이진 파일 뷰어")
root.geometry("300x200")

# 파일 선택 버튼
select_button = tk.Button(root, text="이진 파일 선택", command=show_file_contents)
select_button.pack(expand=True)

root.mainloop()
