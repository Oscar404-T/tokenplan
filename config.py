import os
from urllib.parse import quote_plus as url_quote

class Config:
    # 优先使用 DATABASE_URL 环境变量（推荐用于生产或远程数据库）
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if DATABASE_URL:
        # 使用 DATABASE_URL（会自动处理特殊字符）
        # 例如：mysql+pymysql://user:pass%40word@host/db -> 正确解析
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # 降级到基于环境变量的配置
        env = os.environ.get('FLASK_ENV', 'development')
        
        if env == 'production':
            raise ValueError("生产环境中必须设置 DATABASE_URL 环境变量")

        # 开发模式：支持本地 MySQL 或 SQLite
        if os.environ.get('MYSQL_HOST'):
            MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
            MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
            MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
            MYSQL_DB = os.environ.get('MYSQL_DB', 'tokenplan')
            MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))

            password_quoted = url_quote(MYSQL_PASSWORD)
            SQLALCHEMY_DATABASE_URI = (
                f"mysql+pymysql://{MYSQL_USER}:{password_quoted}"
                f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
            )
        else:
            # 默认使用 SQLite，适用于本地开发
            SQLALCHEMY_DATABASE_URI = 'sqlite:///tokenplan.db'

    # 全局数据库配置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 安全密钥：建议在生产中设置 SECRET_KEY
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-secret-key')
    
    # 会话过期时间：30 分钟
    PERMANENT_SESSION_LIFETIME = 1800  # 秒