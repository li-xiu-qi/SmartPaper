from src.utils.download_models import  download_and_modify_json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == '__main__':
    download_and_modify_json()

