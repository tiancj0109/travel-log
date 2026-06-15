import os

# Flask配置
SECRET_KEY = 'your-secret-key-here-change-in-production'
DEBUG = True

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # 请修改为您的MySQL密码
    'database': 'travel_log',
    'charset': 'utf8mb4',
    'cursorclass': 'DictCursor'
}

# 文件上传配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv'}
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
