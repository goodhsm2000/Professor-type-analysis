import requests
import json
import re

class ClovaSpeechClient:
    # Clova Speech invoke URL
    invoke_url = 'https://clovaspeech-gw.ncloud.com/external/v1/9934/6a962dd693702b263739eb81273ccc7859ccff6ed9c9f872611968edd8e4e034'
    # Clova Speech secret key
    secret = '5344b22c7dc64288ad6d137e4b2fffa4'

    def req_upload(self, file, completion, callback=None, userdata=None, forbiddens=None, boostings=None,
                   wordAlignment=True, fullText=True, diarization=None, sed=None, return_format='JSON'):
        """
        file: 업로드할 음성 파일 경로
        completion: 'sync' | 'async' 방식
        return_format: 'JSON', 'TEXT', 'SRT' 등
        """
        request_body = {
            'language': 'ko-KR',  # 'enko' 등도 사용 가능
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
        files = {
            'media': open(file, 'rb'),
            'params': (None, json.dumps(request_body, ensure_ascii=False).encode('UTF-8'), 'application/json')
        }
        response = requests.post(headers=headers, url=self.invoke_url + '/recognizer/upload', files=files)
        return response

def get_average_words_per_sentence(text: str) -> float:
    """
    전체 텍스트를 문장 단위로 분할한 뒤,
    각 문장의 단어(word) 수를 계산하여 평균을 반환.
    """
    # 문장 분할(마침표, 물음표, 느낌표 기준으로 분할)
    # re.split을 사용하면 다양한 문장부호를 기준으로 분할 가능
    sentences = re.split(r'[.?!]', text)
    
    # 공백/빈 문장 제외
    sentences = [s.strip() for s in sentences if s.strip() != '']
    
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

def process_audio_and_print_average(file_path: str):
    """
    음성 파일 하나를 Clova Speech API로 업로드해 텍스트 변환 후,
    한 문장 안에 들어있는 단어 개수의 평균을 계산해 출력한다.
    """
    client = ClovaSpeechClient()
    
    # Clova Speech API에 음성 파일 업로드(동기 방식)
    response = client.req_upload(file=file_path, completion='sync')
    res_json = response.json()
    
    # 인식된 전체 텍스트
    recognized_text = res_json.get('text', '')
    
    print("[인식 결과]\n", recognized_text)
    
    # 평균 단어 수 계산
    avg_word_count = get_average_words_per_sentence(recognized_text)
    
    print("\n[한 문장 당 평균 단어 수]:", avg_word_count)

if __name__ == '__main__':
    # 테스트할 음성 파일 경로
    test_file_path = './컴비_이승규_2.m4a'
    # test_file_path = './hw_2.mp3'
    
    # 함수 실행
    process_audio_and_print_average(test_file_path)

# 황효석_1: 12.29
# 황효석_2: 13.08
# 생명_1: 18.58
# 생명_2: 16.83
# 자연언어_1: 14.26
# 자연언어_2: 13.91
# 천물_1: 13.61
# 천물_2: 15.259
# 확랜_1: 11.54
# 확랜_2: 12.47
# 컴네_1: 21.52
# 컴네_2: 14.27
# 반응공학_1: 8.44
# 반응공학_2: 9.87
# 웹파_1: 13.11
# 웹파_2: 10.76
# 컴비_1: 12.78
# 컴비_2: 13.61
# hw_1: 14.84
# hw_2: 17.81

