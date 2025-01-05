import tkinter as tk
from tkinter import filedialog, messagebox
import requests
import json
import re
import os
import numpy as np
import matplotlib.pyplot as plt
import librosa  # pip install librosa
from scipy.signal import butter, sosfilt
import noisereduce as nr  # pip install noisereduce
import threading
from PIL import Image, ImageTk  # pip install pillow

#############################################
# 1. Clova Speech API 사용 클래스
#############################################
class ClovaSpeechClient:
    invoke_url = 'https://clovaspeech-gw.ncloud.com/external/v1/9977/492e7b9f8c1f5c6a92daad42462a8c75d70f5889c0392801a1340df6ab89bfd7'
    secret = '383928b14ba9457d9d5d8451b27a15df'

    def req_upload(self,
                   file,
                   completion='sync',
                   callback=None,
                   userdata=None,
                   forbiddens=None,
                   boostings=None,
                   wordAlignment=True,
                   fullText=True,
                   diarization=None,
                   sed=None,
                   return_format='JSON',
                   timeout=30):
        request_body = {
            'language': 'ko-KR',
            'completion': completion,
            'callback': callback,
            'userdata': userdata,
            'wordAlignment': wordAlignment,
            'fullText': fullText,
            'forbiddens': forbiddens,
            'boostings': boostings,
            'diarization': diarization,
            'sed': sed,
            'format': return_format,
        }
        headers = {
            'Accept': 'application/json;UTF-8',
            'X-CLOVASPEECH-API-KEY': self.secret
        }

        with open(file, 'rb') as media_file:
            files = {
                'media': media_file,
                'params': (
                    None,
                    json.dumps(request_body, ensure_ascii=False).encode('UTF-8'),
                    'application/json'
                )
            }
            try:
                response = requests.post(
                    headers=headers,
                    url=self.invoke_url + '/recognizer/upload',
                    files=files,
                    timeout=timeout
                )
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                raise Exception(f"[ClovaSpeechClient 오류] API 요청 실패: {str(e)}")

#############################################
# 2. Band-Pass 필터 함수
#############################################
def bandpass_filter(y, sr, lowcut=80.0, highcut=300.0, order=4):
    sos = butter(order, [lowcut, highcut], btype='band', fs=sr, output='sos')
    return sosfilt(sos, y)

#############################################
# 3. RMS 기반 '유효 프레임' 판정 함수
#############################################
def detect_valid_frames(y, sr, frame_length=2048, hop_length=512,
                        min_amp=0.01, max_amp=0.5):
    rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
    return (rms >= min_amp) & (rms <= max_amp)

#############################################
# 4. 노이즈 감소 함수
#############################################
def reduce_noise_signal(y, sr):
    return nr.reduce_noise(y=y, sr=sr)

#############################################
# (추가) 전체 텍스트 내 음절 수 세는 함수
#############################################
def count_hangul_syllables(text):
    count = 0
    for ch in text:
        if '가' <= ch <= '힣':
            count += 1
    return count

#############################################
# (추가) 5초 단위로 "음절" 최댓값 구하기
#############################################
def compute_5sec_stats_syllables(y, sr, recognized_text,
                                 frame_length=2048, hop_length=512,
                                 min_amp=0.01, max_amp=0.5, chunk_sec=5):
    total_syllables = count_hangul_syllables(recognized_text)
    total_mask = detect_valid_frames(y, sr, frame_length=frame_length,
                                     hop_length=hop_length,
                                     min_amp=min_amp, max_amp=max_amp)
    total_voiced_frames = np.sum(total_mask)
    if total_voiced_frames == 0:
        return 0, 0

    chunk_size = int(sr * chunk_sec)
    num_samples = len(y)
    idx = 0

    max_syllables_5sec = 0
    no_speech_count = 0

    while idx < num_samples:
        end_idx = idx + chunk_size
        chunk = y[idx:end_idx]

        chunk_mask = detect_valid_frames(chunk, sr,
                                         frame_length=frame_length,
                                         hop_length=hop_length,
                                         min_amp=min_amp, max_amp=max_amp)
        chunk_voiced_frames = np.sum(chunk_mask)
        chunk_syllables_est = (chunk_voiced_frames / total_voiced_frames) * total_syllables

        if chunk_voiced_frames == 0:
            no_speech_count += 1

        if chunk_syllables_est > max_syllables_5sec:
            max_syllables_5sec = chunk_syllables_est

        idx += chunk_size

    max_syllables_5sec = int(round(max_syllables_5sec))
    return max_syllables_5sec, no_speech_count

#############################################
# 5. 텍스트 + 음성 분석 함수
#############################################
def analyze_text_and_pitch_variation(text: str,
                                     audio_file: str,
                                     res_json: dict,
                                     chart_path: str):
    duration_api = res_json.get('duration', 0)
    try:
        y, sr = librosa.load(audio_file, sr=None)
        duration_local = librosa.get_duration(y=y, sr=sr)
    except Exception as e:
        print("[librosa 에러]", e)
        y, sr = None, None
        duration_local = 0

    if duration_local > 0:
        audio_duration = duration_local
    else:
        audio_duration = duration_api

    sentences = re.findall(r'[^.?!]+[.?!]', text)
    question_count = 0
    statement_count = 0
    total_words = 0
    total_sentences_counted = 0

    for s in sentences:
        s = s.strip()
        words = s.split()
        total_words += len(words)

        if s.endswith('?'):
            if len(s) > 6:
                question_count += 1
                total_sentences_counted += 1
        elif s.endswith('.') or s.endswith('!'):
            statement_count += 1
            total_sentences_counted += 1

    if total_sentences_counted > 0:
        question_ratio = (question_count / total_sentences_counted) * 100
        statement_ratio = (statement_count / total_sentences_counted) * 100
        avg_words_per_sentence = total_words / total_sentences_counted
    else:
        question_ratio = 0
        statement_ratio = 0
        avg_words_per_sentence = 0

    total_chars = len(text.replace(" ", ""))  # 공백 제외
    if audio_duration > 0:
        speed_cps = total_chars / audio_duration
    else:
        speed_cps = 0

    speakers_info = res_json.get('speakers', [])
    if len(speakers_info) >= 2:
        student_participation = "학생 참여 있음(고)"
    else:
        student_participation = "학생 참여 낮음(단일 화자)"

    max_syllables_5sec = 0
    no_speech_5sec = 0
    if y is not None and sr is not None:
        y_reduced = reduce_noise_signal(y, sr)
        y_filtered = bandpass_filter(y_reduced, sr, lowcut=80.0, highcut=300.0, order=4)
        max_syllables_5sec, no_speech_5sec = compute_5sec_stats_syllables(
            y_filtered, sr, recognized_text=text
        )

    # 임시로 여담 비율 0
    yada_ratio = res_json.get('yada_ratio', 0)

    # 파이차트
    labels = ['Questions (?)', 'Statements (.!)']
    counts = [question_count, statement_count]
    try:
        fig, ax = plt.subplots()
        ax.pie(counts, labels=labels, autopct='%1.1f%%', startangle=140,
               colors=['#ff9999', '#66b3ff'])
        ax.axis('equal')
        plt.title('Question vs. Statement Distribution')
        plt.savefig(chart_path, dpi=150)
        plt.close()
    except Exception as e:
        print("[파이 차트 오류]", e)

    result = {
        'audio_duration': audio_duration,
        'total_sentences': total_sentences_counted,
        'question_count': question_count,
        'statement_count': statement_count,
        'question_ratio': question_ratio,
        'statement_ratio': statement_ratio,
        'avg_words_per_sentence': avg_words_per_sentence,
        'speed_cps': speed_cps,
        'student_participation': student_participation,
        'max_syllables_5sec': max_syllables_5sec,
        'no_speech_5sec': no_speech_5sec,
        'yada_ratio': yada_ratio,
        'chart_path': chart_path
    }
    return result

#############################################
# (추가) 유형 판별 함수
#############################################
def determine_types(analysis_result):
    types = []

    # 표의 평균값(예시)과 마진
    avg_speed = 3.99
    avg_no_speech = 55
    avg_question_ratio = 11.92
    avg_avg_words = 13.94
    avg_max_syllables = 40.85

    margin_speed = 0.3
    margin_question = 3.0
    margin_words = 2.0
    margin_nospeech = 10
    margin_syllables = 5

    if analysis_result['student_participation'] == "학생 참여 낮음(단일 화자)":
        participation = 0
    else:
        participation = 1

    speed_cps = analysis_result['speed_cps']
    no_speech_5sec = analysis_result['no_speech_5sec']
    question_ratio = analysis_result['question_ratio']
    avg_words_per_sentence = analysis_result['avg_words_per_sentence']
    max_syllables_5sec = analysis_result['max_syllables_5sec']
    yada_ratio = analysis_result['yada_ratio']

    is_speed_high = (speed_cps > (avg_speed + margin_speed))
    is_speed_low = (speed_cps < (avg_speed - margin_speed))
    is_nospeech_high = (no_speech_5sec > (avg_no_speech + margin_nospeech))
    is_question_high = (question_ratio > (avg_question_ratio + margin_question))
    is_words_high = (avg_words_per_sentence > (avg_avg_words + margin_words))
    is_maxsyll_high = (max_syllables_5sec > (avg_max_syllables + margin_syllables))

    # 느림의 미학,,,형
    if is_speed_low and is_nospeech_high and (participation == 0):
        types.append("느림의 미학,,,형")

    # tmi형 (여담비율 10% 이상)
    if yada_ratio >= 10:
        types.append("tmi형")

    # 물음표 살인마형
    if is_nospeech_high and (participation == 1):
        types.append("물음표 살인마형")

    # 교수님 진도가 너무 빨라요형
    if is_speed_high and (participation == 0):
        types.append("교수님 진도가 너무 빨라요형")

    # 박찬호형
    if is_speed_high and is_maxsyll_high and is_question_high and (participation == 0):
        types.append("박찬호형")

    # 주절주절형
    if is_words_high:
        types.append("주절주절형")

    if not types:
        types.append("특이 사항 없는 보통형(?)")

    return types

#############################################
# 6. GUI 클래스
#############################################
class LectureAnalysisGUI:
    def __init__(self, root):
        self.root = root
        # GUI 크기 설정
        self.root.geometry("1200x900")
        self.root.title("강의 분석 툴 (유형 판별 + 여러 이미지 표시)")
        self.root.configure(bg='#87CEEB')

        self.file_path = tk.StringVar(value="")
        self.analysis_result = None

        # Canvas + Scrollbar
        self.canvas = tk.Canvas(self.root, bg='#87CEEB')
        self.scrollbar = tk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # 내부에 표시할 메인 프레임
        self.main_frame = tk.Frame(self.canvas, bg='#87CEEB')
        self.canvas.create_window((0, 0), window=self.main_frame, anchor="nw")

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 메인 프레임이 변할 때마다 스크롤 영역 갱신
        self.main_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # 이미지 위젯 리스트
        self.image_widgets = []

        # 이미지가 저장된 폴더 경로
        self.images_folder = "./유형 사진"

        # 상단 타이틀 (중앙 정렬)
        top_frame = tk.Frame(self.main_frame, bg='#87CEEB')
        top_frame.pack(anchor="center", pady=20)

        lbl_title = tk.Label(
            top_frame,
            text="강의 음성 파일 분석 (유형 판별 + 여러 이미지 표시)",
            font=("맑은 고딕", 24, "bold"),
            bg='#87CEEB'
        )
        lbl_title.pack(anchor="center")

        # 파일 선택 영역 (중앙 정렬)
        file_frame = tk.Frame(self.main_frame, bg='#87CEEB')
        file_frame.pack(anchor="center", pady=20)

        btn_file = tk.Button(file_frame, text="음성 파일 선택", command=self.select_file, bg='white', font=("맑은 고딕", 12))
        btn_file.pack(side="left", padx=10)

        lbl_file_path = tk.Label(file_frame, textvariable=self.file_path, bg='#87CEEB',
                                 wraplength=600, font=("맑은 고딕", 12))
        lbl_file_path.pack(side="left", padx=10)

        # 분석/유형 버튼 (중앙 정렬)
        analyze_frame = tk.Frame(self.main_frame, bg='#87CEEB')
        analyze_frame.pack(anchor="center", pady=20)

        btn_analyze = tk.Button(analyze_frame, text="분석 시작", command=self.start_analysis, bg='white', font=("맑은 고딕", 12))
        btn_analyze.pack(side=tk.LEFT, padx=20)

        btn_type = tk.Button(analyze_frame, text="유형 확인하기", command=self.show_types, bg='white', font=("맑은 고딕", 12))
        btn_type.pack(side=tk.LEFT, padx=20)

        # 결과 표시 (텍스트) (중앙 정렬)
        result_frame = tk.Frame(self.main_frame, bg='#87CEEB')
        result_frame.pack(anchor="center", pady=20)

        lbl_result = tk.Label(result_frame, text="분석 결과:", bg='#87CEEB', font=("맑은 고딕", 14, "bold"))
        lbl_result.pack(anchor="center")

        self.result_text = tk.Text(result_frame, width=100, height=20, font=("맑은 고딕", 12))
        self.result_text.pack(anchor="center")

        # 이미지 표시용 프레임 (중앙 정렬)
        self.image_frame = tk.Frame(self.main_frame, bg='#87CEEB')
        self.image_frame.pack(anchor="center", pady=20)

    def select_file(self):
        selected_file = filedialog.askopenfilename(
            title="음성 파일 선택",
            filetypes=[("Audio Files", "*.wav *.mp3 *.m4a *.flac *.ogg"), ("All Files", "*.*")]
        )
        if selected_file:
            self.file_path.set(selected_file)

    def start_analysis(self):
        audio_file = self.file_path.get()
        if not audio_file or not os.path.isfile(audio_file):
            messagebox.showwarning("파일 오류", "유효한 음성 파일을 선택하세요.")
            return

        # 분석 시작 전, 기존 결과 초기화
        self.result_text.delete("1.0", tk.END)
        self.clear_images()
        self.analysis_result = None

        self.result_text.insert(tk.END, "분석을 시작합니다...\n")

        thread = threading.Thread(target=self.analysis_worker, args=(audio_file,))
        thread.start()

    def analysis_worker(self, audio_file):
        try:
            client = ClovaSpeechClient()
            resp = client.req_upload(file=audio_file, completion='sync', timeout=30)
            data_json = resp.json()

            if 'text' not in data_json:
                raise Exception("Clova API 응답에 text 필드가 없습니다.")

            recognized_text = data_json['text']

            chart_path = os.path.join(os.path.dirname(audio_file), "question_statement_chart.png")
            analysis_result = analyze_text_and_pitch_variation(
                text=recognized_text,
                audio_file=audio_file,
                res_json=data_json,
                chart_path=chart_path
            )

            self.analysis_result = analysis_result
            self.root.after(0, self.show_result, analysis_result)

        except Exception as e:
            err_msg = f"오류 발생: {str(e)}"
            self.root.after(0, lambda: self.result_text.insert(tk.END, "\n" + err_msg + "\n"))

    def show_result(self, analysis_result: dict):
        self.result_text.delete("1.0", tk.END)
        summary = (
            f"■ 음성 길이 (초)                   : {analysis_result['audio_duration']:.2f}\n"
            f"■ 전체 문장 수                    : {analysis_result['total_sentences']}\n"
            f"■ 의문문(?로 끝) 수               : {analysis_result['question_count']}\n"
            f"■ 평서문(. / !) 수                : {analysis_result['statement_count']}\n"
            f"■ 의문문 비율 (%)                : {analysis_result['question_ratio']:.2f}\n"
            f"■ 평서문 비율 (%)                : {analysis_result['statement_ratio']:.2f}\n"
            f"■ 한 문장당 평균 단어 개수        : {analysis_result['avg_words_per_sentence']:.2f}\n"
            f"■ 강의 속도 (글자/초)             : {analysis_result['speed_cps']:.2f}\n"
            f"■ 학생 참여도                    : {analysis_result['student_participation']}\n"
            f"■ 5초간 최대 발화량 (음절)        : {analysis_result['max_syllables_5sec']}\n"
            f"■ 5초간 아무 말도 안 한 횟수      : {analysis_result['no_speech_5sec']}\n"
            f"■ 여담 비율(%)                   : {analysis_result['yada_ratio']}\n"
            f"[파이 차트 파일] => {analysis_result['chart_path']}\n"
        )
        self.result_text.insert(tk.END, summary)

    def show_types(self):
        """
        '유형 확인하기' 버튼: 분석 결과 기반으로 유형 판정 후,
        해당 유형별 이미지를 모두 세로로 표시 + 해당 유형 이름 라벨(배경 검정, 글자 흰색)
        """
        if not self.analysis_result:
            messagebox.showinfo("안내", "먼저 '분석 시작'을 해주세요.")
            return

        types = determine_types(self.analysis_result)

        # 기존 이미지 제거
        self.clear_images()

        # 유형을 텍스트로 출력
        self.result_text.insert(tk.END, "\n[유형 판정 결과]\n")
        for t in types:
            self.result_text.insert(tk.END, f"{t}\n")

        # 유형별 이미지 로딩 & 표시 (세로 나열, 중앙 정렬)
        for t in types:
            img_path = self.find_image_file(t)
            if img_path:
                try:
                    pil_img = Image.open(img_path)
                    pil_img = self.resize_image(pil_img, (400, 300))

                    tk_img = ImageTk.PhotoImage(pil_img)
                    img_label = tk.Label(self.image_frame, image=tk_img, bg='#87CEEB')
                    img_label.image = tk_img  # 참조유지

                    # 이미지 표시 (중앙 정렬)
                    img_label.pack(side=tk.TOP, anchor="center", pady=10)
                    self.image_widgets.append(img_label)

                    # 이미지 아래에 유형 이름 표시 (검정 바탕/흰색 글씨)
                    type_label = tk.Label(self.image_frame, text=t,
                                          bg='black', fg='white', font=("맑은 고딕", 14, "bold"), width=30)
                    type_label.pack(side=tk.TOP, anchor="center", pady=5)
                    self.image_widgets.append(type_label)

                except Exception as e:
                    self.result_text.insert(tk.END, f" → [{t}] 유형 이미지 로드 오류: {str(e)}\n")
            else:
                self.result_text.insert(tk.END, f" → [{t}] 유형 이미지가 없습니다.\n")

    def find_image_file(self, type_name):
        possible_exts = [".jpg", ".jpeg", ".png"]
        for ext in possible_exts:
            candidate = os.path.join(self.images_folder, f"{type_name}{ext}")
            if os.path.exists(candidate):
                return candidate
        return None

    def clear_images(self):
        """
        이전 이미지 위젯 제거
        """
        if self.image_widgets:
            for w in self.image_widgets:
                w.destroy()
            self.image_widgets.clear()

    def resize_image(self, pil_img, size):
        """
        Pillow 버전에 따라 호환 가능한 이미지 리사이즈 함수
        """
        try:
            # Pillow 10.0 이상
            resample = Image.Resampling.LANCZOS
        except AttributeError:
            resample = Image.ANTIALIAS
        return pil_img.resize(size, resample)


#############################################
# 7. 메인 실행
#############################################
if __name__ == "__main__":
    root = tk.Tk()
    app = LectureAnalysisGUI(root)
    root.mainloop()
