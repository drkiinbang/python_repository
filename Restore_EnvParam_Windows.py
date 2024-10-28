import tkinter as tk
from tkinter import filedialog, messagebox
import json
import winreg
from pathlib import Path
import os
import datetime

class EnvRestoreApp:
    def __init__(self, root):
        self.root = root
        self.root.title("환경변수 복원 프로그램")
        self.root.geometry("600x400")
        
        # 메인 프레임
        self.main_frame = tk.Frame(self.root, padx=20, pady=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 백업 파일 선택
        self.file_frame = tk.Frame(self.main_frame)
        self.file_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.file_path = tk.StringVar()
        self.file_entry = tk.Entry(self.file_frame, textvariable=self.file_path, width=50)
        self.file_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        self.browse_button = tk.Button(self.file_frame, text="파일 선택", command=self.browse_file)
        self.browse_button.pack(side=tk.LEFT)
        
        # 미리보기 영역
        self.preview_frame = tk.Frame(self.main_frame)
        self.preview_frame.pack(fill=tk.BOTH, expand=True)
        
        self.preview_label = tk.Label(self.preview_frame, text="환경변수 미리보기")
        self.preview_label.pack()
        
        self.preview_text = tk.Text(self.preview_frame, height=15, width=60)
        self.preview_text.pack(pady=10)
        
        # 복원 버튼
        self.restore_button = tk.Button(self.main_frame, text="환경변수 복원", command=self.restore_variables)
        self.restore_button.pack(pady=10)
        
        # 상태 표시
        self.status_var = tk.StringVar()
        self.status_label = tk.Label(self.main_frame, textvariable=self.status_var, wraplength=500)
        self.status_label.pack(pady=10)

    def browse_file(self):
        """백업 파일 선택"""
        filename = filedialog.askopenfilename(
            title="백업 파일 선택",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.file_path.set(filename)
            self.load_preview()
    
    def load_preview(self):
        """선택된 백업 파일의 내용을 미리보기"""
        try:
            with open(self.file_path.get(), 'r', encoding='utf-8') as f:
                env_vars = json.load(f)
            
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, "시스템 환경변수:\n")
            for name, value in env_vars["system"].items():
                self.preview_text.insert(tk.END, f"{name} = {value}\n")
            
            self.preview_text.insert(tk.END, "\n사용자 환경변수:\n")
            for name, value in env_vars["user"].items():
                self.preview_text.insert(tk.END, f"{name} = {value}\n")
                
            self.status_var.set("백업 파일을 불러왔습니다. 복원하시려면 '환경변수 복원' 버튼을 클릭하세요.")
        
        except Exception as e:
            messagebox.showerror("오류", f"파일을 불러오는 중 오류가 발생했습니다: {str(e)}")
            self.status_var.set("파일 로드 실패")
    
    def backup_current_variables(self):
        """현재 환경변수를 백업"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        system_env = {}
        user_env = {}
        
        # 시스템 환경변수 백업
        with winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE) as hkey:
            with winreg.OpenKey(hkey, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment") as key:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        system_env[name] = value
                        i += 1
                    except WindowsError:
                        break
        
        # 사용자 환경변수 백업
        with winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER) as hkey:
            with winreg.OpenKey(hkey, "Environment") as key:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        user_env[name] = value
                        i += 1
                    except WindowsError:
                        break
        
        backup_data = {
            "system": system_env,
            "user": user_env
        }
        
        backup_file = backup_dir / f"env_backup_before_restore_{timestamp}.json"
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
        return backup_file
    
    def restore_variables(self):
        """환경변수 복원"""
        if not self.file_path.get():
            messagebox.showwarning("경고", "복원할 백업 파일을 선택해주세요.")
            return
            
        if not messagebox.askyesno("확인", "환경변수를 복원하시겠습니까?\n현재 환경변수는 자동으로 백업됩니다."):
            return
            
        try:
            # 현재 환경변수 백업
            current_backup = self.backup_current_variables()
            
            # 백업 파일에서 환경변수 읽기
            with open(self.file_path.get(), 'r', encoding='utf-8') as f:
                env_vars = json.load(f)
            
            # 시스템 환경변수 복원
            with winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE) as hkey:
                with winreg.OpenKey(hkey, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment", 0, winreg.KEY_ALL_ACCESS) as key:
                    for name, value in env_vars["system"].items():
                        winreg.SetValueEx(key, name, 0, winreg.REG_EXPAND_SZ, value)
            
            # 사용자 환경변수 복원
            with winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER) as hkey:
                with winreg.OpenKey(hkey, "Environment", 0, winreg.KEY_ALL_ACCESS) as key:
                    for name, value in env_vars["user"].items():
                        winreg.SetValueEx(key, name, 0, winreg.REG_EXPAND_SZ, value)
            
            messagebox.showinfo("성공", f"환경변수가 성공적으로 복원되었습니다.\n현재 환경변수는 다음 위치에 백업되었습니다:\n{current_backup}")
            self.status_var.set("환경변수 복원 완료")
            
        except Exception as e:
            messagebox.showerror("오류", f"환경변수 복원 중 오류가 발생했습니다: {str(e)}")
            self.status_var.set("복원 실패")

if __name__ == "__main__":
    root = tk.Tk()
    app = EnvRestoreApp(root)
    root.mainloop()