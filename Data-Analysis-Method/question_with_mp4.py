import requests
import json
import re
import os
import glob
import matplotlib.pyplot as plt

class ClovaSpeechClient:
    # Clova Speech invoke URL
    invoke_url = 'https://clovaspeech-gw.ncloud.com/external/v1/9934/6a962dd693702b263739eb81273ccc7859ccff6ed9c9f872611968edd8e4e034'
    # Clova Speech secret key
    secret = '5344b22c7dc64288ad6d137e4b2fffa4'

    def req_upload(self, file, completion='sync', callback=None, userdata=None, forbiddens=None, boostings=None,
                   wordAlignment=True, fullText=True, diarization=None, sed=None, return_format='JSON'):
        """
        file: 업로드할 음성 파일 경로
        completion: 'sync' | 'async' (결과 수신 방식)
        return_format: 'JSON', 'TEXT', 'SRT' 등
        """
        request_body = {
            'language': 'ko-KR',  # 언어: 한국어
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
        # 파일과 파라미터를 함께 전송
        with open(file, 'rb') as media_file:
            files = {
                'media': media_file,
                'params': (
                    None,
                    json.dumps(request_body, ensure_ascii=False).encode('UTF-8'),
                    'application/json'
                )
            }
            response = requests.post(
                headers=headers,
                url=self.invoke_url + '/recognizer/upload',
                files=files
            )
        return response

def analyze_text(text: str, output_png_path: str) -> None:
    """
    변환된 텍스트에서 (1) 의문문(?), (2) 평서문(.) 수를 세고,
    의문문 글자 수가 6글자 이하인 문장은 제외한 뒤,
    그 결과를 파이 차트(.png)로 저장.
    """
    # 1) 문장 단위로 분리 (정규표현식 사용: ?.!)
    sentences = re.findall(r'[^.?!]+[.?!]', text)

    # 2) 의문문과 평서문 카운팅
    question_count = 0
    statement_count = 0

    for s in sentences:
        s = s.strip()
        if s.endswith('?'):
            # 글자 수가 6글자 이하인 문장은 제외
            if len(s) > 6:
                question_count += 1
        elif s.endswith('.'):
            statement_count += 1

    # 총 문장 수
    total_sentences = question_count + statement_count

    if total_sentences > 0:
        question_ratio = (question_count / total_sentences) * 100
        statement_ratio = (statement_count / total_sentences) * 100
    else:
        question_ratio = 0
        statement_ratio = 0

    # 3) 결과 출력
    print("=" * 50)
    print("[분석 결과]")
    print(f"전체 문장 수       : {total_sentences}")
    print(f"의문문(?로 끝남) 수 : {question_count}")
    print(f"평서문(.으로 끝남) 수 : {statement_count}")
    print("-" * 50)
    print(f"의문문 비율         : {question_ratio:.2f}%")
    print(f"평서문 비율         : {statement_ratio:.2f}%")
    print("=" * 50)

    # 4) 파이 차트 생성 및 저장
    labels = ['Questions (?)', 'Statements (.)']
    counts = [question_count, statement_count]

    fig, ax = plt.subplots()
    ax.pie(counts, labels=labels, autopct='%1.1f%%', startangle=140)
    ax.axis('equal')  # 원형으로 보이게 설정
    plt.title('Question vs. Statement Distribution')

    # 그래프 저장
    plt.savefig(output_png_path, dpi=150)
    plt.close()

    print(f"[그래프 파일 저장 완료] => {output_png_path}\n")

def process_audio_and_save_chart(file_path: str, output_png_path: str) -> None:
    """
    음성 파일을 Clova Speech API로 변환한 후,
    의문문/평서문 비율 분석 결과를 파이 차트(.png)로 저장.
    """
    # 1) Clova API 호출
    client = ClovaSpeechClient()
    response = client.req_upload(file=file_path, completion='sync')
    # 2) 응답 처리
    if response.status_code != 200:
        print("[오류 발생] 상태 코드:", response.status_code)
        print("응답 내용:", response.text)
        return

    res_json = response.json()
    print(res_json)
    # API 응답에서 text 필드 확인
    recognized_text = res_json.get('text', '')

    print(f"[인식 결과: {os.path.basename(file_path)}]\n", recognized_text)

    # 3) 분석 및 파이 차트 저장
    analyze_text(recognized_text, output_png_path)

def main(input_dir: str, output_dir: str) -> None:
    """
    지정한 디렉토리(input_dir) 내의 모든 .m4a, .mp3 파일을 찾아
    ClovaSpeechClient로 텍스트 변환 후,
    의문문/평서문 비율을 분석해 .png 그래프를 output_dir에 저장
    """

    # 1) 확장자 목록
    extensions = ['.m4a', '.mp3']

    # 2) 파일 목록 수집
    audio_files = []
    for ext in extensions:
        audio_files.extend(glob.glob(os.path.join(input_dir, f'*{ext}')))

    # 변환할 파일이 없으면 종료
    if not audio_files:
        print(f"'{input_dir}' 경로에 {extensions} 파일이 없습니다.")
        return

    # output 디렉토리 준비
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 3) 각 파일 변환 및 결과 저장
    for audio_path in audio_files:
        # 예: 파일이름이 'lecture.m4a'라면 => 그래프: 'lecture.png'
        filename_wo_ext = os.path.splitext(os.path.basename(audio_path))[0]
        output_png = os.path.join(output_dir, f'{filename_wo_ext}.png')

        print(f"\n처리 중: {audio_path}")
        process_audio_and_save_chart(audio_path, output_png)

if __name__ == '__main__':
    # 1) 음성 파일들이 모여 있는 디렉토리
    input_directory = './hw'  # 실제 위치로 변경 가능

    # 2) 결과 파이 차트를 저장할 디렉토리
    output_directory = './output_charts'  # 실제 위치로 변경 가능

    # 메인 실행
    main(input_directory, output_directory)
