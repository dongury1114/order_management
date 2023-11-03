# utils.py
import json
import os

def load_config():
    # 스크립트가 있는 디렉토리의 상위 디렉토리 경로를 구한다.
    dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    config_path = os.path.join(dir_path, 'config.json')
    
    # 상위 디렉토리의 config.json 파일을 로드한다.
    with open(config_path, "r") as f:
        config = json.load(f)
    return config
