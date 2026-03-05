import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, Scrollbar
from PIL import Image
import io
import os

class ImageToPdfConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("이미지 PDF 변환기 (순서 조정 가능)")
        self.root.geometry("500x400")
        
        # 파일 경로를 저장할 리스트
        self.image_paths = []

        # 상단 설명 레이블
        tk.Label(root, text="이미지를 추가하고 순서를 조정하세요.").pack(pady=5)

        # 이미지 리스트 표시창 (Listbox)
        self.frame = tk.Frame(root)
        self.frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        self.listbox = Listbox(self.frame, selectmode=tk.SINGLE)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = Scrollbar(self.frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.listbox.yview)

        # 버튼 영역
        self.btn_frame = tk.Frame(root)
        self.btn_frame.pack(pady=10)

        tk.Button(self.btn_frame, text="이미지 추가", command=self.add_images, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(self.btn_frame, text="위로", command=self.move_up, width=5).pack(side=tk.LEFT, padx=2)
        tk.Button(self.btn_frame, text="아래로", command=self.move_down, width=5).pack(side=tk.LEFT, padx=2)
        tk.Button(self.btn_frame, text="삭제", command=self.delete_image, width=5).pack(side=tk.LEFT, padx=5)
        
        # 변환 버튼
        self.convert_btn = tk.Button(root, text="PDF로 저장하기", command=self.convert_to_pdf, 
                                     bg="#28a745", fg="white", font=("Arial", 10, "bold"), height=2)
        self.convert_btn.pack(fill=tk.X, padx=10, pady=10)

    def add_images(self):
        files = filedialog.askopenfilenames(
            title="이미지들을 선택하세요",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
        )
        if files:
            for f in files:
                self.image_paths.append(f)
                # 리스트박스에는 파일명만 표시
                self.listbox.insert(tk.END, os.path.basename(f))

    def move_up(self):
        idx = self.listbox.curselection()
        if not idx or idx[0] == 0:
            return
        idx = idx[0]
        # 데이터 순서 변경
        self.image_paths[idx], self.image_paths[idx-1] = self.image_paths[idx-1], self.image_paths[idx]
        # 화면 표시 변경
        text = self.listbox.get(idx)
        self.listbox.delete(idx)
        self.listbox.insert(idx-1, text)
        self.listbox.selection_set(idx-1)

    def move_down(self):
        idx = self.listbox.curselection()
        if not idx or idx[0] == len(self.image_paths) - 1:
            return
        idx = idx[0]
        # 데이터 순서 변경
        self.image_paths[idx], self.image_paths[idx+1] = self.image_paths[idx+1], self.image_paths[idx]
        # 화면 표시 변경
        text = self.listbox.get(idx)
        self.listbox.delete(idx)
        self.listbox.insert(idx+1, text)
        self.listbox.selection_set(idx+1)

    def delete_image(self):
        idx = self.listbox.curselection()
        if not idx:
            return
        idx = idx[0]
        del self.image_paths[idx]
        self.listbox.delete(idx)

    def convert_to_pdf(self):
        if not self.image_paths:
            messagebox.showwarning("경고", "추가된 이미지가 없습니다.")
            return

        save_path = filedialog.asksaveasfilename(
            title="저장할 PDF 파일명을 입력하세요",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")]
        )
        if not save_path:
            return

        try:
            image_list = []
            for path in self.image_paths:
                # 한글 경로 및 공백 문제 방지를 위해 바이너리로 읽기
                with open(path, 'rb') as f:
                    img_data = f.read()
                    img = Image.open(io.BytesIO(img_data))
                    image_list.append(img.convert('RGB'))

            if image_list:
                image_list[0].save(save_path, save_all=True, append_images=image_list[1:])
                messagebox.showinfo("성공", f"PDF 파일이 생성되었습니다!\n{save_path}")
        except Exception as e:
            messagebox.showerror("오류", f"변환 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageToPdfConverter(root)
    root.mainloop()