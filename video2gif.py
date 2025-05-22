import moviepy.editor as mp
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

def convert_video_to_gif(video_path, start_time, end_time, output_path):
    try:
        # 동영상 파일 로드
        video = mp.VideoFileClip(video_path)
        
        # 지정된 구간 추출
        clip = video.subclip(start_time, end_time)
        
        # GIF로 저장
        clip.write_gif(output_path, fps=10)  # FPS는 10으로 설정 (필요에 따라 조정 가능)
        
        messagebox.showinfo("성공", f"GIF 파일이 성공적으로 저장되었습니다:\n{output_path}")
        
        # 리소스 해제
        clip.close()
        video.close()
        
    except Exception as e:
        messagebox.showerror("오류", f"오류 발생: {str(e)}")

def select_video_file():
    file_path = filedialog.askopenfilename(
        title="동영상 파일 선택",
        filetypes=[("Video files", "*.mp4 *.avi *.mkv *.mov"), ("All files", "*.*")]
    )
    if file_path:
        video_entry.delete(0, tk.END)
        video_entry.insert(0, file_path)

def select_output_file():
    file_path = filedialog.asksaveasfilename(
        title="GIF 파일 저장 위치 선택",
        defaultextension=".gif",
        filetypes=[("GIF files", "*.gif"), ("All files", "*.*")]
    )
    if file_path:
        output_entry.delete(0, tk.END)
        output_entry.insert(0, file_path)

def start_conversion():
    video_path = video_entry.get()
    output_path = output_entry.get()
    start_time = start_entry.get()
    end_time = end_entry.get()
    
    # 입력 검증
    if not video_path or not os.path.exists(video_path):
        messagebox.showerror("오류", "유효한 동영상 파일을 선택하세요.")
        return
    if not output_path:
        messagebox.showerror("오류", "GIF 저장 경로를 지정하세요.")
        return
    try:
        start_time = float(start_time)
        end_time = float(end_time)
    except ValueError:
        messagebox.showerror("오류", "시작 시간과 종료 시간은 숫자(초)로 입력해야 합니다.")
        return
    if end_time <= start_time:
        messagebox.showerror("오류", "종료 시간은 시작 시간보다 커야 합니다.")
        return
    
    # GIF 변환 실행
    convert_video_to_gif(video_path, start_time, end_time, output_path)

# GUI 생성
root = tk.Tk()
root.title("동영상에서 GIF로 변환")
root.geometry("500x300")

# 동영상 파일 선택
tk.Label(root, text="동영상 파일:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
video_entry = tk.Entry(root, width=40)
video_entry.grid(row=0, column=1, padx=10, pady=10)
tk.Button(root, text="파일 선택", command=select_video_file).grid(row=0, column=2, padx=10, pady=10)

# 출력 GIF 파일 선택
tk.Label(root, text="GIF 저장 경로:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
output_entry = tk.Entry(root, width=40)
output_entry.grid(row=1, column=1, padx=10, pady=10)
tk.Button(root, text="저장 위치 선택", command=select_output_file).grid(row=1, column=2, padx=10, pady=10)

# 시작 시간 입력
tk.Label(root, text="시작 시간(초):").grid(row=2, column=0, padx=10, pady=10, sticky="e")
start_entry = tk.Entry(root, width=10)
start_entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")

# 종료 시간 입력
tk.Label(root, text="종료 시간(초):").grid(row=3, column=0, padx=10, pady=10, sticky="e")
end_entry = tk.Entry(root, width=10)
end_entry.grid(row=3, column=1, padx=10, pady=10, sticky="w")

# 변환 버튼
tk.Button(root, text="GIF로 변환", command=start_conversion).grid(row=4, column=1, pady=20)

# GUI 실행
root.mainloop()