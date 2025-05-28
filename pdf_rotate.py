import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from pypdf import PdfReader, PdfWriter

def rotate_pdf():
    # Tkinter GUI 숨기기
    root = tk.Tk()
    root.withdraw()

    # 1. PDF 파일 선택
    file_path = filedialog.askopenfilename(
        title="PDF 파일 선택",
        filetypes=[("PDF files", "*.pdf")]
    )

    if not file_path:
        print("파일을 선택하지 않았습니다.")
        return

    # 2. 사용자로부터 회전 각도 입력 받기
    angle = simpledialog.askinteger("회전 각도", "시계방향으로 몇 도 회전할까요? (90, 180, 270)", minvalue=0, maxvalue=360)
    if angle not in [90, 180, 270]:
        messagebox.showerror("오류", "90, 180, 270도 중 하나만 입력 가능합니다.")
        return

    # 3. PDF 읽고 회전 처리
    try:
        reader = PdfReader(file_path)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page.rotate(angle))

        # 4. 새 파일로 저장
        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="저장할 파일 이름을 지정하세요"
        )

        if output_path:
            with open(output_path, "wb") as f:
                writer.write(f)
            messagebox.showinfo("완료", f"PDF가 성공적으로 저장되었습니다:\n{output_path}")
        else:
            print("저장을 취소했습니다.")

    except Exception as e:
        messagebox.showerror("오류 발생", str(e))

# 실행
if __name__ == "__main__":
    rotate_pdf()
