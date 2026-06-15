from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename
import config
from utils.auth import (
    register_user, login_user, login_required, 
    get_current_user, search_users
)
from utils.trip import (
    create_trip, get_user_trips, get_trip_by_id, 
    update_trip_status, save_pre_trip_plan, get_pre_trip_plan,
    add_during_trip_log, get_during_trip_logs, delete_during_trip_log,
    get_trip_members, add_trip_member, remove_trip_member,
    upload_media, get_trip_media, delete_media,
    check_trip_permission
)
from utils.ai_summary import generate_ai_summary
import os

app = Flask(__name__)
app.config.from_object(config)

# ========== 首页和认证路由 ==========

@app.route('/')
@login_required
def index():
    """旅行列表页面"""
    user = get_current_user()
    trips = get_user_trips(user['id'])
    return render_template('index.html', trips=trips, user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        success, message, user_id = register_user(username, password)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        success, message, user = login_user(username, password)
        
        if success:
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(message, 'success')
            return redirect(url_for('index'))
        else:
            flash(message, 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """用户登出"""
    session.clear()
    flash('已退出登录', 'info')
    return redirect(url_for('login'))

# ========== 旅行管理路由 ==========

@app.route('/trip/create', methods=['GET', 'POST'])
@login_required
def trip_create():
    """创建新旅行"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        
        if not title:
            flash('请填写旅行标题', 'error')
            return redirect(url_for('trip_create'))
        
        user = get_current_user()
        trip_id = create_trip(title, description, user['id'])
        
        # 保存前期计划（如果有填写）
        timeline = request.form.get('timeline', '').strip()
        location = request.form.get('location', '').strip()
        supplies = request.form.get('supplies', '').strip()
        notes = request.form.get('notes', '').strip()
        
        if any([timeline, location, supplies, notes]):
            save_pre_trip_plan(trip_id, timeline, location, supplies, notes)
        
        flash('旅行计划创建成功', 'success')
        return redirect(url_for('trip_detail', trip_id=trip_id))
    
    user = get_current_user()
    return render_template('trip_create.html', user=user)

@app.route('/trip/<int:trip_id>')
@login_required
def trip_detail(trip_id):
    """旅行详情页面"""
    user = get_current_user()
    trip = get_trip_by_id(trip_id, user['id'])
    
    if not trip:
        flash('旅行不存在或无权访问', 'error')
        return redirect(url_for('index'))
    
    # 获取相关数据
    members = get_trip_members(trip_id)
    pre_plan = get_pre_trip_plan(trip_id)
    logs = get_during_trip_logs(trip_id) if trip['status'] in ['during', 'post'] else []
    media = get_trip_media(trip_id) if trip['status'] in ['during', 'post'] else []
    
    # 为每个log获取对应的媒体
    logs_with_media = []
    for log in logs:
        log_media = get_trip_media(trip_id, log['id'])
        logs_with_media.append({
            'log': log,
            'media': log_media
        })
    
    return render_template('trip_detail.html', 
                         trip=trip, 
                         user=user,
                         members=members,
                         pre_plan=pre_plan,
                         logs_with_media=logs_with_media,
                         all_media=media)

@app.route('/trip/<int:trip_id>/update-status', methods=['POST'])
@login_required
def trip_update_status(trip_id):
    """更新旅行状态"""
    user = get_current_user()
    new_status = request.form.get('status')
    
    if new_status not in ['pre', 'during', 'post']:
        flash('无效的状态', 'error')
        return redirect(url_for('trip_detail', trip_id=trip_id))
    
    success = update_trip_status(trip_id, new_status, user['id'])
    
    if success:
        status_names = {'pre': '前期准备', 'during': '旅行中', 'post': '已结束'}
        flash(f'状态已更新为：{status_names[new_status]}', 'success')
    else:
        flash('更新失败', 'error')
    
    return redirect(url_for('trip_detail', trip_id=trip_id))

@app.route('/trip/<int:trip_id>/pre-plan', methods=['POST'])
@login_required
def trip_save_pre_plan(trip_id):
    """保存前期计划"""
    user = get_current_user()
    
    # 检查权限
    has_permission, _ = check_trip_permission(trip_id, user['id'])
    if not has_permission:
        flash('无权限操作', 'error')
        return redirect(url_for('index'))
    
    timeline = request.form.get('timeline', '').strip()
    location = request.form.get('location', '').strip()
    supplies = request.form.get('supplies', '').strip()
    notes = request.form.get('notes', '').strip()
    
    save_pre_trip_plan(trip_id, timeline, location, supplies, notes)
    flash('前期计划已保存', 'success')
    
    return redirect(url_for('trip_detail', trip_id=trip_id))

@app.route('/trip/<int:trip_id>/during-log', methods=['POST'])
@login_required
def trip_add_during_log(trip_id):
    """添加旅行中记录"""
    user = get_current_user()
    
    # 检查权限
    has_permission, _ = check_trip_permission(trip_id, user['id'])
    if not has_permission:
        flash('无权限操作', 'error')
        return redirect(url_for('index'))
    
    log_date = request.form.get('log_date')
    notes = request.form.get('notes', '').strip()
    expense = request.form.get('expense', 0)
    interesting_notes = request.form.get('interesting_notes', '').strip()
    
    if not log_date:
        flash('请选择日期', 'error')
        return redirect(url_for('trip_detail', trip_id=trip_id))
    
    try:
        expense = float(expense) if expense else 0
    except ValueError:
        expense = 0
    
    log_id = add_during_trip_log(trip_id, log_date, notes, expense, interesting_notes)
    
    # 处理上传的媒体文件
    if 'media_files' in request.files:
        files = request.files.getlist('media_files')
        for file in files:
            if file and file.filename:
                upload_media(trip_id, log_id, file, user['id'])
    
    flash('记录已添加', 'success')
    return redirect(url_for('trip_detail', trip_id=trip_id))

@app.route('/trip/<int:trip_id>/delete-log/<int:log_id>', methods=['POST'])
@login_required
def trip_delete_log(trip_id, log_id):
    """删除旅行记录"""
    user = get_current_user()
    success = delete_during_trip_log(log_id, trip_id, user['id'])
    
    if success:
        flash('记录已删除', 'success')
    else:
        flash('删除失败', 'error')
    
    return redirect(url_for('trip_detail', trip_id=trip_id))

@app.route('/trip/<int:trip_id>/upload-media', methods=['POST'])
@login_required
def trip_upload_media(trip_id):
    """上传媒体文件（不关联到特定log）"""
    user = get_current_user()
    
    if 'file' not in request.files:
        flash('没有文件', 'error')
        return redirect(url_for('trip_detail', trip_id=trip_id))
    
    file = request.files['file']
    success, message, media_id = upload_media(trip_id, None, file, user['id'])
    
    flash(message, 'success' if success else 'error')
    return redirect(url_for('trip_detail', trip_id=trip_id))

@app.route('/trip/<int:trip_id>/delete-media/<int:media_id>', methods=['POST'])
@login_required
def trip_delete_media(trip_id, media_id):
    """删除媒体文件"""
    user = get_current_user()
    success, message = delete_media(media_id, user['id'])
    
    flash(message, 'success' if success else 'error')
    return redirect(url_for('trip_detail', trip_id=trip_id))

# ========== 成员管理路由 ==========

@app.route('/search-users')
@login_required
def search_users_api():
    """搜索用户API"""
    keyword = request.args.get('q', '').strip()
    
    if not keyword:
        return jsonify([])
    
    users = search_users(keyword)
    return jsonify([{'id': u['id'], 'username': u['username']} for u in users])

@app.route('/trip/<int:trip_id>/add-member', methods=['POST'])
@login_required
def trip_add_member(trip_id):
    """添加旅行成员"""
    user = get_current_user()
    member_id = request.form.get('member_id')
    
    if not member_id:
        flash('请选择要添加的用户', 'error')
        return redirect(url_for('trip_detail', trip_id=trip_id))
    
    try:
        member_id = int(member_id)
    except ValueError:
        flash('无效的用户ID', 'error')
        return redirect(url_for('trip_detail', trip_id=trip_id))
    
    success, message = add_trip_member(trip_id, member_id, user['id'])
    flash(message, 'success' if success else 'error')
    
    return redirect(url_for('trip_detail', trip_id=trip_id))

@app.route('/trip/<int:trip_id>/remove-member', methods=['POST'])
@login_required
def trip_remove_member(trip_id):
    """移除旅行成员"""
    user = get_current_user()
    member_id = request.form.get('member_id')
    
    if not member_id:
        flash('请选择要移除的用户', 'error')
        return redirect(url_for('trip_detail', trip_id=trip_id))
    
    try:
        member_id = int(member_id)
    except ValueError:
        flash('无效的用户ID', 'error')
        return redirect(url_for('trip_detail', trip_id=trip_id))
    
    success, message = remove_trip_member(trip_id, member_id, user['id'])
    flash(message, 'success' if success else 'error')
    
    return redirect(url_for('trip_detail', trip_id=trip_id))

# ========== AI总结路由 ==========

@app.route('/trip/<int:trip_id>/summary')
@login_required
def trip_summary(trip_id):
    """生成并显示AI总结"""
    user = get_current_user()
    trip = get_trip_by_id(trip_id, user['id'])
    
    if not trip:
        flash('旅行不存在或无权访问', 'error')
        return redirect(url_for('index'))
    
    summary = generate_ai_summary(trip_id)
    
    return render_template('trip_summary.html', 
                         trip=trip, 
                         user=user,
                         summary=summary)

# ========== 错误处理 ==========

@app.errorhandler(404)
def not_found(error):
    flash('页面不存在', 'error')
    return redirect(url_for('index'))

@app.errorhandler(500)
def internal_error(error):
    flash('服务器错误，请稍后重试', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
