import struct
import numpy as np
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import mmap

class FastBinaryFileViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("고속 3D 좌표 이진 파일 뷰어")
        self.root.geometry("400x300")

        # 파일 선택 버튼
        self.select_button = tk.Button(root, text="이진 파일 선택", command=self.show_file_contents)
        self.select_button.pack(expand=True, pady=10)

        # 진행률 프로그레스 바
        self.progress_label = tk.Label(root, text="")
        self.progress_label.pack(pady=5)

        self.progress_bar = ttk.Progressbar(root, orient='horizontal', length=300, mode='determinate')
        self.progress_bar.pack(pady=10)

    def read_binary_file_numpy(self, filename):
        try:
            with open(filename, 'rb') as file:
                # mmap 사용으로 파일 읽기 성능 향상
                mm = mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ)
                
                # 3개의 float offset 값 읽기 (12바이트)
                offset_x, offset_y, offset_z = struct.unpack('3f', mm[0:12])
                
                # 나머지 좌표를 NumPy로 빠르게 읽기
                coordinates = np.frombuffer(mm[12:], dtype=np.float32).reshape(-1, 3)
                
                mm.close()
                
                return offset_x, offset_y, offset_z, coordinates
        
        except Exception as e:
            messagebox.showerror("오류", f"파일을 읽는 중 오류 발생: {e}")
            return None

    def show_file_contents(self):
        # 진행률 초기화
        self.progress_bar['value'] = 0
        self.progress_label.config(text="")

        # 파일 선택 대화상자 열기
        filename = filedialog.askopenfilename(title="이진 파일 선택")
        if not filename:
            return
        
        # 파일 내용 읽기
        result = self.read_binary_file_numpy(filename)
        if result is None:
            return
        
        offset_x, offset_y, offset_z, coordinates = result
        
        # 진행 완료
        self.progress_bar['value'] = 100
        self.progress_label.config(text="진행률: 100%")
        
        # 창 생성
        details_window = tk.Toplevel(self.root)
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
app = FastBinaryFileViewer(root)
root.mainloop()