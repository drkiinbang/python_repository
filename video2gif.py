import moviepy.editor as mp
import os

def convert_video_to_gif(video_path, start_time, end_time, output_path):
    try:
        # 동영상 파일 로드
        video = mp.VideoFileClip(video_path)
        
        # 지정된 구간 추출
        clip = video.subclip(start_time, end_time)
        
        # GIF로 저장
        clip.write_gif(output_path, fps=10)  # FPS는 10으로 설정 (필요에 따라 조정 가능)
        
        print(f"GIF 파일이 성공적으로 저장되었습니다: {output_path}")
        
        # 리소스 해제
        clip.close()
        video.close()
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")

def main():
    # 사용자 입력 받기
    video_path = input("동영상 파일 경로를 입력하세요 (예: video.mp4): ")
    start_time = float(input("GIF로 변환할 시작 시간(초)을 입력하세요: "))
    end_time = float(input("GIF로 변환할 종료 시간(초)을 입력하세요: "))
    output_path = input("저장할 GIF 파일 경로를 입력하세요 (예: output.gif): ")
    
    # 파일 존재 여부 확인
    if not os.path.exists(video_path):
        print("입력한 동영상 파일이 존재하지 않습니다.")
        return
    
    # 종료 시간이 시작 시간보다 큰지 확인
    if end_time <= start_time:
        print("종료 시간은 시작 시간보다 커야 합니다.")
        return
    
    # GIF 변환 실행
    convert_video_to_gif(video_path, start_time, end_time, output_path)

if __name__ == "__main__":
    main()