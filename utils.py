# utils.py
import json
import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """로깅 설정"""
    logger = logging.getLogger('OrderManagement')
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # 파일 핸들러 설정
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'order_management.log'),
            maxBytes=10*1024*1024,
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        
        # 콘솔 핸들러 설정
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 포맷터 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

def load_config(config_path=None):
    """설정 파일 로드"""
    logger = setup_logging()
    
    try:
        if config_path is None:
            # 기본 설정 파일 경로
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, '..', 'config.json')
        
        logger.debug(f"설정 파일 경로: {config_path}")
        
        if not os.path.exists(config_path):
            logger.error(f"설정 파일이 존재하지 않습니다: {config_path}")
            return None
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            logger.debug("설정 파일 로드 성공")
            return config
            
    except json.JSONDecodeError as e:
        logger.error(f"설정 파일 형식이 잘못되었습니다: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"설정 파일 로드 중 오류 발생: {str(e)}")
        return None
