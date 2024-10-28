import os
import json
import winreg
import datetime
from pathlib import Path

def get_environment_variables():
    """시스템 및 사용자 환경변수를 가져오는 함수"""
    # 시스템 환경변수
    system_env = {}
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

    # 사용자 환경변수
    user_env = {}
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

    return {
        "system": system_env,
        "user": user_env
    }

def backup_environment_variables(backup_dir="backups"):
    """환경변수를 JSON 파일로 백업하는 함수"""
    # 백업 디렉토리 생성
    backup_path = Path(backup_dir)
    backup_path.mkdir(exist_ok=True)
    
    # 현재 시간을 파일명에 포함
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_path / f"env_backup_{timestamp}.json"
    
    # 환경변수 가져오기
    env_vars = get_environment_variables()
    
    # JSON 파일로 저장
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(env_vars, f, indent=2, ensure_ascii=False)
    
    return backup_file

def restore_environment_variables(backup_file):
    """백업된 환경변수를 복원하는 함수"""
    if not os.path.exists(backup_file):
        raise FileNotFoundError(f"백업 파일을 찾을 수 없습니다: {backup_file}")
    
    # 백업 파일 읽기
    with open(backup_file, 'r', encoding='utf-8') as f:
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

if __name__ == "__main__":
    try:
        # 환경변수 백업
        backup_file = backup_environment_variables()
        print(f"환경변수가 성공적으로 백업되었습니다: {backup_file}")
        
        # 복원이 필요한 경우 아래 코드의 주석을 해제하고 백업 파일 경로를 지정하세요
        # restore_environment_variables("backups/env_backup_20240328_123456.json")
        # print("환경변수가 성공적으로 복원되었습니다.")
        
    except Exception as e:
        print(f"오류가 발생했습니다: {str(e)}")