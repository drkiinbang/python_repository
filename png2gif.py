import os
from tkinter import Tk, filedialog
from PIL import Image

def create_gif_from_pngs():
    # Tkinter 루트 창 숨기기
    Tk().withdraw()

    # PNG 파일 선택
    png_files = filedialog.askopenfilenames(
        title="PNG 파일 선택",
        filetypes=[("PNG files", "*.png")],
    )

    if not png_files:
        print("PNG 파일이 선택되지 않았습니다.")
        return

    # GIF 파일 저장 경로 및 이름 선택
    gif_file = filedialog.asksaveasfilename(
        title="GIF 파일 저장",
        defaultextension=".gif",
        filetypes=[("GIF files", "*.gif")],
    )

    if not gif_file:
        print("GIF 파일 저장 경로가 선택되지 않았습니다.")
        return

    # PNG 파일들을 GIF로 변환
    images = [Image.open(png) for png in png_files]
    
    # 첫 번째 이미지를 사용하여 GIF 생성
    images[0].save(
        gif_file,
        save_all=True,
        append_images=images[1:],
        duration=500,  # 각 프레임의 지속 시간 (밀리초)
        loop=0         # 무한 반복
    )

    print(f"GIF 파일이 생성되었습니다: {gif_file}")

if __name__ == "__main__":
    create_gif_from_pngs()
