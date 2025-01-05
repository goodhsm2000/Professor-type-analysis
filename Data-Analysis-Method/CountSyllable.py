import requests
import json
import os
import numpy as np


class ClovaSpeechClient:
    # Clova Speech invoke URL
    invoke_url = 'https://clovaspeech-gw.ncloud.com/external/v1/9934/6a962dd693702b263739eb81273ccc7859ccff6ed9c9f872611968edd8e4e034'
    # Clova Speech secret key
    secret = '5344b22c7dc64288ad6d137e4b2fffa4'

    def req_url(self, url, completion, callback=None, userdata=None, forbiddens=None, boostings=None, wordAlignment=True, fullText=True, diarization=None, sed=None, return_format='SRT'):
        request_body = {
            'url': url,
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
            'Content-Type': 'application/json;UTF-8',
            'X-CLOVASPEECH-API-KEY': self.secret
        }
        return requests.post(headers=headers,
                             url=self.invoke_url + '/recognizer/url',
                             data=json.dumps(request_body).encode('UTF-8'))

    def req_object_storage(self, data_key, completion, callback=None, userdata=None, forbiddens=None, boostings=None,
                           wordAlignment=True, fullText=True, diarization=None, sed=None, return_format='SRT'):
        request_body = {
            'dataKey': data_key,
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
            'Content-Type': 'application/json;UTF-8',
            'X-CLOVASPEECH-API-KEY': self.secret
        }
        return requests.post(headers=headers,
                             url=self.invoke_url + '/recognizer/object-storage',
                             data=json.dumps(request_body).encode('UTF-8'))

    def req_upload(self, file, completion, callback=None, userdata=None, forbiddens=None, boostings=None,
                   wordAlignment=True, fullText=True, diarization=None, sed=None, return_format='JSON'):
        request_body = {
            'language': 'ko-KR',  #enko
            'completion': completion,
            'callback': callback,
            'userdata': userdata,
            'wordAlignment': wordAlignment,
            'fullText': fullText,
            'forbiddens': forbiddens,  #전문용어 인식률 높이기 위한 인자/영한 지원/어레이 전달
            'boostings': boostings,
            'diarization': diarization,
            'sed': sed,
            'format': return_format,
        }
        headers = {
            'Accept': 'application/json;UTF-8',
            'X-CLOVASPEECH-API-KEY': self.secret
        }
        #print(json.dumps(request_body, ensure_ascii=False).encode('UTF-8'))
        files = {
            'media': open(file, 'rb'),
            'params': (None, json.dumps(request_body, ensure_ascii=False).encode('UTF-8'), 'application/json')
        }
        response = requests.post(headers=headers, url=self.invoke_url + '/recognizer/upload', files=files)
        return response

def counting(path,len_file):
    char_len = []
    for i in range(len_file):
        print("##########################\n{} of {}".format(i+1,len_file))
        res = ClovaSpeechClient().req_upload(file=path+'/output_{}.mp3'.format(i+1), completion='sync').json()
        print(res['text'])
        character_count = len(res['text'].replace(" ", "").replace('.',"").replace('?',"").replace('!',"").replace(',',"")) 
        print("글자수: ",character_count)
        char_len.append(character_count)
        if i%10 == 0:
            np.save('pre'+path[3:]+'_total_char.npy',np.array(char_len))
    np.save('pre'+path[3:]+'_total_char.npy',np.array(char_len))

if __name__ == '__main__':
    path = f'raw/sg/sg_2'
    len_file = len(os.listdir(path))
    counting(path, len_file)
