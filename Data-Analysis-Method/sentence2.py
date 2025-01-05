import os
import re
import json
import time
import threading
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from pydub import AudioSegment
from pydub.utils import which
import requests
import wave
import contextlib

# ============================
# 0. FFmpeg와 FFprobe 경로 설정 및 검증
# ============================

ffmpeg_bin_dir = r"C:\ffmpeg\ffmpeg-2025\bin"  # 실제 ffmpeg의 bin 디렉토리 경로로 변경
ffmpeg_path = os.path.join(ffmpeg_bin_dir, "ffmpeg.exe")
ffprobe_path = os.path.join(ffmpeg_bin_dir, "ffprobe.exe")

# 시스템 PATH에 ffmpeg bin 디렉토리 추가 (이미 PATH에 있다면 중복되어도 문제 없음)
os.environ["PATH"] += os.pathsep + ffmpeg_bin_dir

# pydub 설정
AudioSegment.converter = ffmpeg_path
AudioSegment.ffprobe = ffprobe_path

# 경로 존재 여부 확인
if not os.path.isfile(AudioSegment.converter):
    raise FileNotFoundError(f"FFmpeg executable not found at {AudioSegment.converter}")
if not os.path.isfile(AudioSegment.ffprobe):
    raise FileNotFoundError(f"FFprobe executable not found at {AudioSegment.ffprobe}")

print("FFmpeg and FFprobe paths are correctly set.")

# pydub이 ffmpeg와 ffprobe를 제대로 인식하고 있는지 확인
print("FFmpeg which:", which("ffmpeg"))
print("FFprobe which:", which("ffprobe"))

############################
# 1. ClovaSpeechClient 정의
############################
class ClovaSpeechClient:
    # Clova Speech invoke URL
    invoke_url = (
        "https://clovaspeech-gw.ncloud.com/external/v1/9934/"
        "6a962dd693702b263739eb81273ccc7859ccff6ed9c9f872611968edd8e4e034"
    )
    # Clova Speech secret key
    secret = "5344b22c7dc64288ad6d137e4b2fffa4"

    def req_upload(self, file, completion="sync", return_format="JSON"):
        """
        file: 업로드할 음성 파일 경로
        completion: 'sync' | 'async' 방식
        return_format: 'JSON', 'TEXT', 'SRT' 등
        """
        request_body = {
            "language": "ko-KR",
            "completion": completion,
            "wordAlignment": True,
            "fullText": True,
            "format": return_format,
        }
        headers = {
            "Accept": "application/json;UTF-8",
            "X-CLOVASPEECH-API-KEY": self.secret,
        }
        try:
            with open(file, "rb") as f:
                files = {
                    "media": f,
                    "params": (
                        None,
                        json.dumps(request_body, ensure_ascii=False).encode("UTF-8"),
                        "application/json",
                    ),
                }
                response = requests.post(
                    headers=headers,
                    url=self.invoke_url + "/recognizer/upload",
                    files=files,
                )
                response.raise_for_status()
        except requests.RequestException as e:
            print(f"HTTP Request failed: {e}")
            return None
        except Exception as e:
            print(f"Error uploading file: {e}")
            return None
        return response

############################
# 2. 평균 단어 수 계산 함수 정의
############################
def get_average_words_per_sentence(text: str) -> float:
    """
    전체 텍스트를 문장 단위로 분할하고, 각 문장의 단어 수를 계산하여 평균을 반환합니다.
    """
    # 마침표, 물음표, 느낌표 등을 기준으로 문장 분리
    sentences = re.split(r"[.?!]", text)
    # 공백 및 빈 문장 제거
    sentences = [s.strip() for s in sentences if s.strip() != ""]

    if not sentences:
        return 0.0

    word_counts = []
    for s in sentences:
        # 단어 분할(공백 기준)
        words = s.split()
        word_counts.append(len(words))

    # 전체 문장 단어 수 평균
    avg = sum(word_counts) / len(word_counts)
    return avg

############################
# 3. 음성 파일 분할 함수 정의
############################
def split_audio(file_path, chunk_length_ms=5000):
    """
    지정한 음성 파일을 일정 시간 단위로 분할하여 임시 파일로 저장합니다.
    
    Parameters:
    - file_path: 분할할 원본 음성 파일 경로 (M4A 등)
    - chunk_length_ms: 분할할 청크의 길이 (밀리초 단위)
    
    Returns:
    - chunks: 분할된 청크 파일 경로 리스트
    """
    print(f"Attempting to load audio file: {file_path}")
    print("Using FFmpeg at:", AudioSegment.converter)
    print("Using FFprobe at:", AudioSegment.ffprobe)

    # 1) 음성 파일 로딩 (에러 처리)
    try:
        audio = AudioSegment.from_file(file_path)
    except Exception as e:
        print(f"Error loading audio file: {e}")
        return []

    # 2) 일정 길이(5초)마다 슬라이싱하여 청크 파일 만들기
    chunks = []
    for i, chunk in enumerate(audio[::chunk_length_ms]):
        # MP4 형식으로 내보내도록 수정
        # 확장자는 .mp4로 권장 (내부 컨테이너는 mp4)
        chunk_filename = f"temp_chunk_{i+1}.mp4"
        try:
            # codec="aac"으로 지정. format="mp4" → -f mp4
            chunk.export(chunk_filename, format="mp4", codec="aac")
            chunks.append(chunk_filename)
            print(f"Created chunk: {chunk_filename}")
        except Exception as e:
            print(f"Error exporting chunk {chunk_filename}: {e}")
    return chunks

############################
# 4. 청크별 처리 및 그래프 업데이트
############################
def process_chunks(
    chunks, average_words_list, time_labels, client, chunk_length_sec=5, delay=1
):
    """
    분할된 음성 청크들을 순차적으로 처리하여 평균 단어 수를 계산하고 리스트에 저장합니다.
    
    Parameters:
    - chunks: 분할된 청크 파일 경로 리스트
    - average_words_list: 평균 단어 수를 저장할 리스트
    - time_labels: 시간 또는 인덱스를 저장할 리스트
    - client: ClovaSpeechClient 인스턴스
    - chunk_length_sec: 청크 길이 (초)
    - delay: 각 청크 처리 간의 대기 시간 (초)
    """
    start_time = time.time()

    for index, chunk in enumerate(chunks, start=1):
        print(f"Processing {chunk} ({index}/{len(chunks)})...")

        # Clova Speech API 업로드
        response = client.req_upload(file=chunk, completion="sync")
        if response is None:
            recognized_text = ""
        elif response.status_code != 200:
            print(f"Error processing {chunk}: {response.status_code}")
            recognized_text = ""
        else:
            try:
                res_json = response.json()
                recognized_text = res_json.get("text", "")
            except json.JSONDecodeError:
                print(f"Error decoding JSON response for {chunk}")
                recognized_text = ""

        print(f"Recognized Text: {recognized_text}")

        # 평균 단어 수 계산
        if recognized_text:
            avg_words = get_average_words_per_sentence(recognized_text)
        else:
            avg_words = 0.0
        print(f"Average Words per Sentence: {avg_words}\n")

        # 결과 리스트에 저장
        average_words_list.append(avg_words)
        elapsed_time = index * chunk_length_sec
        time_labels.append(elapsed_time)

        # 임시 파일 삭제
        try:
            if os.path.exists(chunk):
                os.remove(chunk)
        except Exception as e:
            print(f"Error deleting {chunk}: {e}")

        time.sleep(delay)  # 지정된 시간만큼 대기

############################
# 5. 실시간 그래프 설정
############################
def setup_realtime_plot(average_words_list, time_labels):
    """
    실시간으로 평균 단어 수를 업데이트하는 그래프를 설정합니다.
    """
    fig, ax = plt.subplots()
    line, = ax.plot([], [], "bo-", label="평균 단어 수")
    ax.set_xlabel("시간 (초)")
    ax.set_ylabel("평균 단어 수")
    ax.set_title("문장당 평균 단어 수 실시간 모니터링")
    ax.legend()
    ax.grid(True)

    def init():
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 20)
        return line,

    def update(frame):
        if not average_words_list:
            return line,

        x_data = time_labels
        y_data = average_words_list

        line.set_data(x_data, y_data)

        # x축과 y축의 범위를 동적으로 조정
        if x_data:
            ax.set_xlim(0, max(x_data) + 5)
        if y_data:
            ax.set_ylim(0, max(y_data) + 5)

        return line,

    ani = FuncAnimation(fig, update, init_func=init, interval=1000, blit=False)
    plt.show()

############################
# 6. 메인 함수
############################
def main():
    # 분석할 음성 파일 경로를 지정하세요 (기존 m4a 파일 등)
    audio_file_path = "./로프 1118_황효석_1.m4a"

    if not os.path.exists(audio_file_path):
        print(f"Audio file '{audio_file_path}' not found.")
        return

    # 청크 길이 설정 (밀리초 단위) - 5초
    chunk_length_ms = 60000

    # 음성 파일 분할
    print("Splitting audio file into chunks...")
    chunks = split_audio(audio_file_path, chunk_length_ms)
    if not chunks:
        print("No chunks created. Exiting.")
        return
    print(f"Total chunks created: {len(chunks)}\n")

    # ClovaSpeechClient 인스턴스 생성
    client = ClovaSpeechClient()

    # 결과 저장을 위한 리스트 초기화
    average_words_list = []
    time_labels = []

    # 청크 처리 스레드 시작
    processing_thread = threading.Thread(
        target=process_chunks,
        args=(chunks, average_words_list, time_labels, client, chunk_length_ms // 1000, 1),
        daemon=True
    )
    processing_thread.start()

    # 실시간 그래프 설정 및 실행
    setup_realtime_plot(average_words_list, time_labels)

    # 처리 스레드가 완료될 때까지 대기
    processing_thread.join()
    print("Processing completed.")

if __name__ == "__main__":
    main()
