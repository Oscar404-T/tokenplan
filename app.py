import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pymysql
pymysql.install_as_MySQLdb()

from app import app

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)