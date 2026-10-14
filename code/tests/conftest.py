import os
import sys

# tests/ 에서 code/ 의 모듈을 불러올 수 있게
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
