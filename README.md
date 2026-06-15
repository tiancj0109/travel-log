# Travel Log

> 简约优雅的旅行日志与计划管理系统

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.x-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=flat-square&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Gemini](https://img.shields.io/badge/Gemini_API-Google-8E75C2?style=flat-square&logo=google-gemini&logoColor=white)](https://ai.google.dev/)

一个为旅行爱好者与团队设计的高颜值旅行规划与记录平台。从行前的灵感策划，到旅途中的图文随手记，再到智能的 AI 行程复盘，Travel Log 致力于用最纯粹的视觉与交互，珍藏您的每一次出发。

---

## 🌟 核心功能

*   **行前筹备 (Pre-Trip Planning)**
    *   结构化管理行前时间线、目的地、行李物资与备忘提示，省时省心。
*   **旅中记录 (During-Trip Journal)**
    *   以时间轴形式呈现图文日记，支持上传照片，记录沿途故事。
*   **费用账单 (Expense Tracking)**
    *   轻量级的日常支出记账，自动汇总旅行总开销，清晰掌控预算。
*   **团队协同 (Coop Companion)**
    *   支持添加同行旅伴，多人实时共享并编辑同一份旅行计划与记录。
*   **AI 智慧总结 (AI Summary)**
    *   基于 Google Gemini API，一键将您的旅行随笔和开销数据升华为精美的旅行复盘报告。

---

## 🛠️ 技术底座

*   **后端**：Python + Flask (轻量级 Web 框架)
*   **数据库**：MySQL (持久化存储)
*   **前端**：HTML5 + CSS3 (采用 Inter 字体、极简线条与流畅微交互)
*   **AI 接口**：Google Gemini API

---

## 🚀 快速开始

### 1. 环境准备
确保已安装 Python 3.8+ 及 MySQL 数据库。

### 2. 克隆项目与安装依赖
```bash
# 进入项目目录
cd travel_log

# 安装 Python 依赖
pip install -r requirements.txt
```

### 3. 数据库初始化
在 MySQL 中创建数据库 `travel_log`，并导入表结构：
```bash
mysql -u root -p -e "CREATE DATABASE travel_log DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p travel_log < schema.sql
```

### 4. 配置文件修改
编辑 `config.py`，配置您的数据库连接信息：
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_mysql_password',  # 替换为您的 MySQL 密码
    'database': 'travel_log',
    'charset': 'utf8mb4',
    'cursorclass': 'DictCursor'
}
```

### 5. 启动运行
```bash
python app.py
```
启动后在浏览器访问 `http://localhost:5000` 即可使用。
