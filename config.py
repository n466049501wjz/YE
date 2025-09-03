import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# 基本配置
SECRET_KEY = 'your-secret-key-here-change-in-production'

# 数据库配置
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'private_equity.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# 文件上传配置
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB最大文件上传