import os
from pydub import AudioSegment
import librosa
import numpy as np
import matplotlib.pyplot as plt

def convert_m4a_to_wav(m4a_path, wav_path):
    """
    .m4a 파일을 .wav 파일로 변환합니다.
    """
    try:
        audio = AudioSegment.from_file(m4a_path, format="m4a")
        audio.export(wav_path, format="wav")
        print(f"변환 완료: {wav_path}")
    except Exception as e:
        print(f"파일 변환 중 오류 발생: {e}")
        exit()

def main():
    # 파일 경로 설정
    m4a_path = 'C:/Users/USER/KHU_2024_2/숨겨진 패턴/로프 1118.m4a'  # 원본 m4a 파일 경로
    wav_path = 'C:/Users/USER/KHU_2024_2/숨겨진 패턴/로프.wav'   # 변환된 wav 파일 경로

    # .wav 파일 존재 여부 확인
    if not os.path.exists(wav_path):
        print(f"WAV 파일이 존재하지 않습니다. 변환을 시작합니다: {wav_path}")
        convert_m4a_to_wav(m4a_path, wav_path)
    else:
        print(f"WAV 파일이 이미 존재합니다: {wav_path}")

    # .wav 파일 로딩
    try:
        y, sr = librosa.load(wav_path, sr=None)  # sr=None은 원본 샘플레이트 유지
        print(f"오디오 로딩 성공, samplerate: {sr} Hz")
    except Exception as e:
        print(f"오디오 로딩 중 오류 발생: {e}")
        exit()

    # pYIN을 이용한 피치(억양) 추출
    try:
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y, 
            sr=sr,
            fmin=librosa.note_to_hz('C2'),  # 하한 주파수 (약 65.4Hz)
            fmax=librosa.note_to_hz('C7')   # 상한 주파수 (약 2093Hz)
        )
        print("피치 추출 완료")
    except Exception as e:
        print(f"피치 추출 중 오류 발생: {e}")
        exit()

    # 유효한 f0만 골라서 통계 내기
    valid_f0 = f0[~np.isnan(f0)]  # NaN이 아닌 값만 추출
    if len(valid_f0) > 0:
        mean_pitch = np.mean(valid_f0)
        min_pitch = np.min(valid_f0)
        max_pitch = np.max(valid_f0)
        
        print(f"평균 피치(Hz): {mean_pitch:.2f}")
        print(f"최소 피치(Hz): {min_pitch:.2f}")
        print(f"최대 피치(Hz): {max_pitch:.2f}")
    else:
        print("음성이 거의 없거나, 피치를 추출할 수 없습니다.")

    # 시간축에 따른 f0(피치) 시각화
    times = librosa.times_like(f0, sr=sr)

    plt.figure(figsize=(12, 6))
    plt.plot(times, f0, label="Pitch (pYIN)", color='red')
    plt.xlabel("Time (s)")
    plt.ylabel("Frequency (Hz)")
    plt.title("Pitch over Time")
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
