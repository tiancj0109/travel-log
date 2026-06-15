import os
from datetime import datetime
from utils.db import fetch_one, fetch_all, insert, update, delete
from werkzeug.utils import secure_filename
import config

def create_trip(title, description, creator_id):
    """
    创建新旅行计划
    
    Args:
        title: 旅行标题
        description: 旅行描述
        creator_id: 创建者ID
    
    Returns:
        int: 旅行ID
    """
    trip_id = insert(
        'INSERT INTO trips (title, description, creator_id, status) VALUES (%s, %s, %s, %s)',
        (title, description, creator_id, 'pre')
    )
    
    # 自动将创建者添加为成员
    insert(
        'INSERT INTO trip_members (trip_id, user_id, role) VALUES (%s, %s, %s)',
        (trip_id, creator_id, 'creator')
    )
    
    return trip_id

def get_user_trips(user_id):
    """
    获取用户的所有旅行（创建的或参与的）
    
    Args:
        user_id: 用户ID
    
    Returns:
        list: 旅行列表
    """
    trips = fetch_all('''
        SELECT DISTINCT t.*, u.username as creator_name
        FROM trips t
        JOIN trip_members tm ON t.id = tm.trip_id
        JOIN users u ON t.creator_id = u.id
        WHERE tm.user_id = %s
        ORDER BY t.updated_at DESC
    ''', (user_id,))
    
    return trips or []

def get_trip_by_id(trip_id, user_id=None):
    """
    获取旅行详情
    
    Args:
        trip_id: 旅行ID
        user_id: 用户ID（用于权限验证）
    
    Returns:
        dict: 旅行信息
    """
    trip = fetch_one('''
        SELECT t.*, u.username as creator_name
        FROM trips t
        JOIN users u ON t.creator_id = u.id
        WHERE t.id = %s
    ''', (trip_id,))
    
    if not trip:
        return None
    
    # 如果提供了user_id，检查权限
    if user_id:
        is_member = fetch_one(
            'SELECT id FROM trip_members WHERE trip_id = %s AND user_id = %s',
            (trip_id, user_id)
        )
        if not is_member:
            return None
    
    return trip

def check_trip_permission(trip_id, user_id):
    """检查用户是否有权限访问旅行"""
    member = fetch_one(
        'SELECT id, role FROM trip_members WHERE trip_id = %s AND user_id = %s',
        (trip_id, user_id)
    )
    return member is not None, member

def update_trip_status(trip_id, new_status, user_id):
    """
    更新旅行状态
    
    Args:
        trip_id: 旅行ID
        new_status: 新状态 (pre/during/post)
        user_id: 操作用户ID
    
    Returns:
        bool: 是否成功
    """
    # 检查权限
    has_permission, member = check_trip_permission(trip_id, user_id)
    if not has_permission:
        return False
    
    update(
        'UPDATE trips SET status = %s WHERE id = %s',
        (new_status, trip_id)
    )
    return True

# ========== 前期计划相关 ==========

def save_pre_trip_plan(trip_id, timeline, location, supplies, notes):
    """保存或更新前期计划"""
    existing = fetch_one(
        'SELECT id FROM pre_trip_plans WHERE trip_id = %s',
        (trip_id,)
    )
    
    if existing:
        update('''
            UPDATE pre_trip_plans 
            SET timeline = %s, location = %s, supplies = %s, notes = %s
            WHERE trip_id = %s
        ''', (timeline, location, supplies, notes, trip_id))
    else:
        insert('''
            INSERT INTO pre_trip_plans (trip_id, timeline, location, supplies, notes)
            VALUES (%s, %s, %s, %s, %s)
        ''', (trip_id, timeline, location, supplies, notes))
    
    return True

def get_pre_trip_plan(trip_id):
    """获取前期计划"""
    return fetch_one(
        'SELECT * FROM pre_trip_plans WHERE trip_id = %s',
        (trip_id,)
    )

# ========== 旅行中记录相关 ==========

def add_during_trip_log(trip_id, log_date, notes, expense, interesting_notes):
    """添加旅行中的记录"""
    log_id = insert('''
        INSERT INTO during_trip_logs (trip_id, log_date, notes, expense, interesting_notes)
        VALUES (%s, %s, %s, %s, %s)
    ''', (trip_id, log_date, notes, expense or 0, interesting_notes))
    
    return log_id

def get_during_trip_logs(trip_id):
    """获取旅行中的所有记录"""
    logs = fetch_all(
        'SELECT * FROM during_trip_logs WHERE trip_id = %s ORDER BY log_date DESC, created_at DESC',
        (trip_id,)
    )
    return logs or []

def delete_during_trip_log(log_id, trip_id, user_id):
    """删除旅行记录"""
    has_permission, _ = check_trip_permission(trip_id, user_id)
    if not has_permission:
        return False
    
    # 先删除相关媒体文件
    delete('DELETE FROM trip_media WHERE log_id = %s', (log_id,))
    # 删除记录
    delete('DELETE FROM during_trip_logs WHERE id = %s AND trip_id = %s', (log_id, trip_id))
    return True

# ========== 成员管理相关 ==========

def get_trip_members(trip_id):
    """获取旅行成员列表"""
    members = fetch_all('''
        SELECT tm.*, u.username
        FROM trip_members tm
        JOIN users u ON tm.user_id = u.id
        WHERE tm.trip_id = %s
        ORDER BY tm.role DESC, tm.added_at ASC
    ''', (trip_id,))
    
    return members or []

def add_trip_member(trip_id, user_id, added_by_user_id):
    """
    添加旅行成员
    
    Args:
        trip_id: 旅行ID
        user_id: 要添加的用户ID
        added_by_user_id: 操作者ID
    
    Returns:
        tuple: (success, message)
    """
    # 检查操作者权限
    has_permission, _ = check_trip_permission(trip_id, added_by_user_id)
    if not has_permission:
        return False, '无权限添加成员'
    
    # 检查是否已经是成员
    existing = fetch_one(
        'SELECT id FROM trip_members WHERE trip_id = %s AND user_id = %s',
        (trip_id, user_id)
    )
    
    if existing:
        return False, '该用户已是成员'
    
    try:
        insert(
            'INSERT INTO trip_members (trip_id, user_id, role) VALUES (%s, %s, %s)',
            (trip_id, user_id, 'member')
        )
        return True, '添加成功'
    except Exception as e:
        return False, f'添加失败: {str(e)}'

def remove_trip_member(trip_id, user_id, removed_by_user_id):
    """
    移除旅行成员
    
    Args:
        trip_id: 旅行ID
        user_id: 要移除的用户ID
        removed_by_user_id: 操作者ID
    
    Returns:
        tuple: (success, message)
    """
    # 检查操作者权限
    has_permission, member_info = check_trip_permission(trip_id, removed_by_user_id)
    if not has_permission:
        return False, '无权限移除成员'
    
    # 获取旅行信息
    trip = fetch_one('SELECT creator_id FROM trips WHERE id = %s', (trip_id,))
    if not trip:
        return False, '旅行不存在'
    
    # 不能移除创建者
    if user_id == trip['creator_id']:
        return False, '不能移除旅行创建者'
    
    # 检查要移除的用户是否是成员
    target_member = fetch_one(
        'SELECT id FROM trip_members WHERE trip_id = %s AND user_id = %s',
        (trip_id, user_id)
    )
    
    if not target_member:
        return False, '该用户不是成员'
    
    try:
        delete(
            'DELETE FROM trip_members WHERE trip_id = %s AND user_id = %s',
            (trip_id, user_id)
        )
        return True, '移除成功'
    except Exception as e:
        return False, f'移除失败: {str(e)}'

# ========== 媒体文件相关 ==========

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

def get_media_type(filename):
    """根据文件扩展名判断媒体类型"""
    ext = filename.rsplit('.', 1)[1].lower()
    if ext in {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}:
        return 'image'
    elif ext in {'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv'}:
        return 'video'
    return None

def upload_media(trip_id, log_id, file, user_id):
    """
    上传媒体文件
    
    Args:
        trip_id: 旅行ID
        log_id: 记录ID（可选）
        file: 文件对象
        user_id: 用户ID
    
    Returns:
        tuple: (success, message, media_id)
    """
    # 检查权限
    has_permission, _ = check_trip_permission(trip_id, user_id)
    if not has_permission:
        return False, '无权限上传', None
    
    if not file or file.filename == '':
        return False, '没有选择文件', None
    
    if not allowed_file(file.filename):
        return False, '不支持的文件格式', None
    
    try:
        # 生成安全的文件名
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{trip_id}_{timestamp}_{filename}"
        
        filepath = os.path.join(config.UPLOAD_FOLDER, unique_filename)
        file.save(filepath)
        
        # 保存到数据库
        media_type = get_media_type(filename)
        media_id = insert('''
            INSERT INTO trip_media (trip_id, log_id, media_type, file_path, file_name)
            VALUES (%s, %s, %s, %s, %s)
        ''', (trip_id, log_id, media_type, unique_filename, filename))
        
        return True, '上传成功', media_id
    except Exception as e:
        return False, f'上传失败: {str(e)}', None

def get_trip_media(trip_id, log_id=None):
    """
    获取媒体文件列表
    
    Args:
        trip_id: 旅行ID
        log_id: 记录ID（可选，如果提供则只返回该记录的媒体）
    
    Returns:
        list: 媒体列表
    """
    if log_id:
        media = fetch_all(
            'SELECT * FROM trip_media WHERE trip_id = %s AND log_id = %s ORDER BY uploaded_at DESC',
            (trip_id, log_id)
        )
    else:
        media = fetch_all(
            'SELECT * FROM trip_media WHERE trip_id = %s ORDER BY uploaded_at DESC',
            (trip_id,)
        )
    
    return media or []

def delete_media(media_id, user_id):
    """
    删除媒体文件
    
    Args:
        media_id: 媒体ID
        user_id: 用户ID
    
    Returns:
        tuple: (success, message)
    """
    # 获取媒体信息
    media = fetch_one(
        'SELECT * FROM trip_media WHERE id = %s',
        (media_id,)
    )
    
    if not media:
        return False, '媒体不存在'
    
    # 检查权限
    has_permission, _ = check_trip_permission(media['trip_id'], user_id)
    if not has_permission:
        return False, '无权限删除'
    
    try:
        # 删除物理文件
        filepath = os.path.join(config.UPLOAD_FOLDER, media['file_path'])
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # 从数据库删除
        delete('DELETE FROM trip_media WHERE id = %s', (media_id,))
        
        return True, '删除成功'
    except Exception as e:
        return False, f'删除失败: {str(e)}'

# ========== 数据汇总相关 ==========

def get_trip_summary_data(trip_id):
    """
    获取旅行的完整数据用于AI总结
    
    Returns:
        dict: 包含所有旅行数据
    """
    trip = get_trip_by_id(trip_id)
    if not trip:
        return None
    
    members = get_trip_members(trip_id)
    pre_plan = get_pre_trip_plan(trip_id)
    logs = get_during_trip_logs(trip_id)
    media = get_trip_media(trip_id)
    
    # 计算总花销
    total_expense = sum(log['expense'] for log in logs)
    
    return {
        'trip': trip,
        'members': members,
        'pre_plan': pre_plan,
        'logs': logs,
        'media': media,
        'total_expense': total_expense
    }
