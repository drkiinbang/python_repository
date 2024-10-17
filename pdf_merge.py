import PyPDF2
import tkinter as tk
from tkinter import filedialog

def merge_pdfs(pdf_list, output_path):
    merger = PyPDF2.PdfMerger()
    for pdf in pdf_list:
        with open(pdf, 'rb') as f:
            merger.append(f)
    
    with open(output_path, 'wb') as output_file:
        merger.write(output_file)

# 파일 선택 및 저장 파일 이름 입력
def select_pdfs_and_merge():
    # Tkinter 초기화 및 숨김
    root = tk.Tk()
    root.withdraw()

    # 파일 다이얼로그에서 여러 개의 PDF 파일 선택
    pdf_files = filedialog.askopenfilenames(title="Select PDF files", filetypes=[("PDF files", "*.pdf")])
    
    if not pdf_files:
        print("No files selected. Exiting.")
        return
    
    # 사용자로부터 저장할 파일 경로 및 이름 선택 받기
    output_file = filedialog.asksaveasfilename(
        title="Save merged PDF as", 
        defaultextension=".pdf", 
        filetypes=[("PDF files", "*.pdf")],
        initialfile="merged_output.pdf"
    )
    
    if not output_file:
        print("No save location provided. Exiting.")
        return
    
    # PDF 병합
    merge_pdfs(pdf_files, output_file)

    print(f"{output_file} 생성 완료!")

# 프로그램 실행
if __name__ == "__main__":
    select_pdfs_and_merge()
