import sys
from pathlib import Path

# 保证从任意目录执行 pytest 都能 import 到 app 包
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
