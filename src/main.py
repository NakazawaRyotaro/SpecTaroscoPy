import os
import subprocess

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__)) # 現在のファイルのpathを取得
LAUNCHER_PATH = os.path.join(CURRENT_PATH, 'launcher.py')
subprocess.call(['python', LAUNCHER_PATH])