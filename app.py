from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_migrate import Migrate  # 新增导入
from models import db, User, PrivateFund, DueDiligence, DueDiligenceComment  # 更新导入
from datetime import datetime
import os
import json

app = Flask(__name__)
app.config.from_pyfile('config.py')

# 初始化数据库
db.init_app(app)

# 初始化 Flask-Migrate
migrate = Migrate(app, db)  # 新增

# 初始化登录管理
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# 文件上传配置
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# 路由定义
@app.route('/')
@login_required
def dashboard():
    # 获取统计数据
    total_funds = PrivateFund.query.count()
    user_updates = DueDiligence.query.filter_by(user_id=current_user.id).count()

    # 获取地区分布数据
    regions = db.session.query(
        PrivateFund.region,
        db.func.count(PrivateFund.id)
    ).group_by(PrivateFund.region).all()

    region_data = {region: count for region, count in regions if region}

    # 最近更新
    recent_updates = DueDiligence.query.order_by(
        DueDiligence.created_at.desc()
    ).limit(5).all()

    return render_template(
        'dashboard.html',
        total_funds=total_funds,
        user_updates=user_updates,
        region_data=json.dumps(region_data),
        recent_updates=recent_updates
    )


@app.route('/funds')
@login_required
def funds():
    # 处理筛选参数
    management_scale_min = request.args.get('management_scale_min', type=float)
    management_scale_max = request.args.get('management_scale_max', type=float)
    strategy = request.args.get('strategy')
    region = request.args.get('region')
    keyword = request.args.get('keyword')

    # 构建查询
    query = PrivateFund.query

    if management_scale_min is not None:
        query = query.filter(PrivateFund.management_scale >= management_scale_min)
    if management_scale_max is not None:
        query = query.filter(PrivateFund.management_scale <= management_scale_max)
    if strategy:
        query = query.filter(PrivateFund.strategy_tags.like(f'%{strategy}%'))
    if region:
        query = query.filter(PrivateFund.region == region)
    if keyword:
        query = query.filter(PrivateFund.keywords.like(f'%{keyword}%'))

    # 处理排序
    sort_by = request.args.get('sort_by', 'name')
    order = request.args.get('order', 'asc')

    if sort_by and hasattr(PrivateFund, sort_by):
        if order == 'desc':
            query = query.order_by(getattr(PrivateFund, sort_by).desc())
        else:
            query = query.order_by(getattr(PrivateFund, sort_by))

    funds = query.all()

    # 获取所有地区和策略标签用于筛选
    all_regions = db.session.query(PrivateFund.region).distinct().all()
    all_regions = [r[0] for r in all_regions if r[0]]

    # 获取所有策略标签
    all_strategies = set()
    for fund in PrivateFund.query.all():
        if fund.strategy_tags:
            tags = [tag.strip() for tag in fund.strategy_tags.split(',')]
            all_strategies.update(tags)

    return render_template(
        'funds.html',
        funds=funds,
        all_regions=all_regions,
        all_strategies=sorted(all_strategies),
        sort_by=sort_by,
        order=order
    )


@app.route('/fund/<int:fund_id>')
@login_required
def fund_detail(fund_id):
    fund = PrivateFund.query.get_or_404(fund_id)
    due_diligences = DueDiligence.query.filter_by(fund_id=fund_id).order_by(
        DueDiligence.date.desc()
    ).all()

    # 确保每个尽调记录的批注都被加载
    for dd in due_diligences:
        dd.comments  # 这会触发批注的加载

    return render_template(
        'fund_detail.html',
        fund=fund,
        due_diligences=due_diligences,
        now=datetime.now()
    )


@app.route('/add_due_diligence/<int:fund_id>', methods=['POST'])
@login_required
def add_due_diligence(fund_id):
    fund = PrivateFund.query.get_or_404(fund_id)

    content = request.form.get('content')
    date_str = request.form.get('date')

    if not content:
        flash('尽调内容不能为空', 'error')
        return redirect(url_for('fund_detail', fund_id=fund_id))

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.utcnow()
    except ValueError:
        flash('日期格式不正确', 'error')
        return redirect(url_for('fund_detail', fund_id=fund_id))

    # 处理文件上传
    file_path = None
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_folder = app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            # 只保存文件名，不保存完整路径
            file_path = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            full_path = os.path.join(upload_folder, file_path)
            file.save(full_path)

    due_diligence = DueDiligence(
        fund_id=fund_id,
        user_id=current_user.id,
        date=date,
        content=content,
        file_path=file_path
    )

    db.session.add(due_diligence)
    db.session.commit()

    flash('尽调记录已添加', 'success')
    return redirect(url_for('fund_detail', fund_id=fund_id))


@app.route('/add_fund', methods=['GET', 'POST'])
@login_required
def add_fund():
    if request.method == 'POST':
        name = request.form.get('name')
        establishment_date_str = request.form.get('establishment_date')
        management_scale = request.form.get('management_scale', type=float)
        team_size = request.form.get('team_size', type=int)
        strategy_tags = request.form.get('strategy_tags')
        region = request.form.get('region')
        keywords = request.form.get('keywords')

        if not name:
            flash('私募名称不能为空', 'error')
            return render_template('add_fund.html')

        # 检查是否已存在同名私募
        if PrivateFund.query.filter_by(name=name).first():
            flash('已存在同名私募', 'error')
            return render_template('add_fund.html')

        try:
            establishment_date = datetime.strptime(establishment_date_str,
                                                   '%Y-%m-%d') if establishment_date_str else None
        except ValueError:
            flash('成立日期格式不正确', 'error')
            return render_template('add_fund.html')

        fund = PrivateFund(
            name=name,
            establishment_date=establishment_date,
            management_scale=management_scale,
            team_size=team_size,
            strategy_tags=strategy_tags,
            region=region,
            keywords=keywords
        )

        db.session.add(fund)
        db.session.commit()

        flash('私募信息已添加', 'success')
        return redirect(url_for('funds'))

    return render_template('add_fund.html')


@app.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    # 确保文件名不包含路径分隔符，防止目录遍历攻击
    if '..' in filename or filename.startswith('/'):
        abort(404)

    # 直接从上传目录提供文件
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('用户名或密码错误', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        flash('无权访问管理员页面', 'error')
        return redirect(url_for('dashboard'))

    users = User.query.all()
    return render_template('admin.html', users=users)


@app.route('/update_user_role', methods=['POST'])
@login_required
def update_user_role():
    if current_user.role != 'admin':
        return jsonify({'error': '无权操作'}), 403

    user_id = request.form.get('user_id')
    new_role = request.form.get('role')

    user = User.query.get(user_id)
    if user:
        user.role = new_role
        db.session.commit()
        return jsonify({'success': True})

    return jsonify({'error': '用户不存在'}), 404


@app.route('/create_user', methods=['POST'])
@login_required
def create_user():
    if current_user.role != 'admin':
        return jsonify({'error': '无权操作'}), 403

    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role', 'user')

    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': '用户名已存在'}), 400

    user = User(
        username=username,
        password=generate_password_hash(password),
        role=role
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({'success': True})


# 添加初始化数据库的命令
@app.cli.command("init-db")
def init_db_command():
    """初始化数据库"""
    db.create_all()

    # 创建默认管理员账户（如果不存在）
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            username='admin',
            password=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin_user)
        db.session.commit()
        print('已创建默认管理员账户: admin/admin123')

    print('数据库初始化完成')


# 在现有路由后添加以下路由

@app.route('/edit_fund/<int:fund_id>', methods=['GET', 'POST'])
@login_required
def edit_fund(fund_id):
    fund = PrivateFund.query.get_or_404(fund_id)

    if request.method == 'POST':
        fund.name = request.form.get('name')
        establishment_date_str = request.form.get('establishment_date')
        fund.management_scale = request.form.get('management_scale', type=float)
        fund.team_size = request.form.get('team_size', type=int)
        fund.strategy_tags = request.form.get('strategy_tags')
        fund.region = request.form.get('region')
        fund.keywords = request.form.get('keywords')

        try:
            fund.establishment_date = datetime.strptime(establishment_date_str,
                                                        '%Y-%m-%d') if establishment_date_str else None
        except ValueError:
            flash('成立日期格式不正确', 'error')
            return render_template('edit_fund.html', fund=fund)

        db.session.commit()
        flash('私募信息已更新', 'success')
        return redirect(url_for('fund_detail', fund_id=fund.id))

    return render_template('edit_fund.html', fund=fund)


@app.route('/delete_fund/<int:fund_id>', methods=['POST'])
@login_required
def delete_fund(fund_id):
    fund = PrivateFund.query.get_or_404(fund_id)

    # 删除相关的尽调记录和文件
    due_diligences = DueDiligence.query.filter_by(fund_id=fund_id).all()
    for dd in due_diligences:
        if dd.file_path and os.path.exists(dd.file_path):
            os.remove(dd.file_path)
        # 删除批注
        DueDiligenceComment.query.filter_by(due_diligence_id=dd.id).delete()
        db.session.delete(dd)

    db.session.delete(fund)
    db.session.commit()
    flash('私募信息已删除', 'success')
    return redirect(url_for('funds'))


@app.route('/edit_due_diligence/<int:dd_id>', methods=['GET', 'POST'])
@login_required
def edit_due_diligence(dd_id):
    dd = DueDiligence.query.get_or_404(dd_id)

    # 检查权限：只有记录创建者或管理员可以编辑
    if current_user.id != dd.user_id and current_user.role != 'admin':
        flash('无权编辑此记录', 'error')
        return redirect(url_for('fund_detail', fund_id=dd.fund_id))

    if request.method == 'POST':
        dd.content = request.form.get('content')
        date_str = request.form.get('date')

        try:
            dd.date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.utcnow()
        except ValueError:
            flash('日期格式不正确', 'error')
            return render_template('edit_due_diligence.html', dd=dd)

        # 处理文件重新上传
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename != '' and allowed_file(file.filename):
                # 删除旧文件
                if dd.file_path:
                    old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], dd.file_path)
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)

                filename = secure_filename(file.filename)
                upload_folder = app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                # 只保存文件名，不保存完整路径
                dd.file_path = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                full_path = os.path.join(upload_folder, dd.file_path)
                file.save(full_path)

        db.session.commit()
        flash('尽调记录已更新', 'success')
        return redirect(url_for('fund_detail', fund_id=dd.fund_id))

    return render_template('edit_due_diligence.html', dd=dd)


@app.route('/delete_due_diligence/<int:dd_id>', methods=['POST'])
@login_required
def delete_due_diligence(dd_id):
    dd = DueDiligence.query.get_or_404(dd_id)
    fund_id = dd.fund_id

    # 检查权限：只有记录创建者或管理员可以删除
    if current_user.id != dd.user_id and current_user.role != 'admin':
        flash('无权删除此记录', 'error')
        return redirect(url_for('fund_detail', fund_id=fund_id))

    # 删除文件和批注
    if dd.file_path and os.path.exists(dd.file_path):
        os.remove(dd.file_path)

    # 删除相关批注
    DueDiligenceComment.query.filter_by(due_diligence_id=dd_id).delete()

    db.session.delete(dd)
    db.session.commit()
    flash('尽调记录已删除', 'success')
    return redirect(url_for('fund_detail', fund_id=fund_id))


@app.route('/add_comment/<int:dd_id>', methods=['POST'])
@login_required
def add_comment(dd_id):
    dd = DueDiligence.query.get_or_404(dd_id)
    content = request.form.get('content')

    if not content:
        flash('批注内容不能为空', 'error')
        return redirect(url_for('fund_detail', fund_id=dd.fund_id))

    comment = DueDiligenceComment(
        due_diligence_id=dd_id,  # 确保使用正确的字段名
        user_id=current_user.id,
        content=content
    )

    db.session.add(comment)
    db.session.commit()
    flash('批注已添加', 'success')
    return redirect(url_for('fund_detail', fund_id=dd.fund_id))


@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = DueDiligenceComment.query.get_or_404(comment_id)
    due_diligence_id = comment.due_diligence_id
    dd = DueDiligence.query.get(due_diligence_id)

    # 检查权限：只有批注创建者或管理员可以删除
    if current_user.id != comment.user_id and current_user.role != 'admin':
        flash('无权删除此批注', 'error')
        return redirect(url_for('fund_detail', fund_id=dd.fund_id))

    db.session.delete(comment)
    db.session.commit()
    flash('批注已删除', 'success')
    return redirect(url_for('fund_detail', fund_id=dd.fund_id))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # 创建默认管理员账户（如果不存在）
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()

    app.run(debug=True)

# 在文件末尾添加以下代码
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'PrivateFund': PrivateFund,
        'DueDiligence': DueDiligence,
        'DueDiligenceComment': DueDiligenceComment
    }

# 设置 shell 上下文处理器
@app.shell_context_processor
def shell_context():

    return make_shell_context()
