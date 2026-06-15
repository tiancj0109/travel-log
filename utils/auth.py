import re
from functools import wraps
from flask import session, redirect, url_for, flash
from utils.db import fetch_one, fetch_all, insert

def validate_username(username):
    """
    验证用户名格式：只允许中文、英文和数字
    
    Args:
        username: 用户名字符串
    
    Returns:
        bool: 是否合法
    """
    if not username or len(username) < 2 or len(username) > 50:
        return False
    
    # 正则：允许中文、英文字母、数字
    pattern = r'^[\u4e00-\u9fa5a-zA-Z0-9]+$'
    return bool(re.match(pattern, username))

def register_user(username, password):
    """
    注册新用户
    
    Args:
        username: 用户名
        password: 密码（明文）
    
    Returns:
        tuple: (success: bool, message: str, user_id: int or None)
    """
    # 验证用户名格式
    if not validate_username(username):
        return False, '用户名只能包含中文、英文和数字，长度2-50字符', None
    
    # 检查用户名是否已存在
    existing_user = fetch_one(
        'SELECT id FROM users WHERE username = %s',
        (username,)
    )
    
    if existing_user:
        return False, '用户名已存在', None
    
    # 插入新用户
    try:
        user_id = insert(
            'INSERT INTO users (username, password) VALUES (%s, %s)',
            (username, password)
        )
        return True, '注册成功', user_id
    except Exception as e:
        return False, f'注册失败: {str(e)}', None

def login_user(username, password):
    """
    用户登录
    
    Args:
        username: 用户名
        password: 密码
    
    Returns:
        tuple: (success: bool, message: str, user: dict or None)
    """
    user = fetch_one(
        'SELECT id, username, password FROM users WHERE username = %s',
        (username,)
    )
    
    if not user:
        return False, '用户名不存在', None
    
    # 明文密码比对
    if user['password'] != password:
        return False, '密码错误', None
    
    return True, '登录成功', user

def get_user_by_id(user_id):
    """根据ID获取用户信息"""
    return fetch_one(
        'SELECT id, username, created_at FROM users WHERE id = %s',
        (user_id,)
    )

def search_users(keyword, limit=10):
    """
    搜索用户
    
    Args:
        keyword: 搜索关键词
        limit: 返回数量限制
    
    Returns:
        list: 用户列表
    """
    if not keyword:
        return []
    
    users = fetch_all(
        'SELECT id, username FROM users WHERE username LIKE %s LIMIT %s',
        (f'%{keyword}%', limit)
    )
    
    return users or []

def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """获取当前登录用户"""
    if 'user_id' in session:
        return get_user_by_id(session['user_id'])
    return None
