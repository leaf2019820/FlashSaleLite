from flask import request, render_template, jsonify, flash, redirect, url_for, Blueprint, current_app, send_file
from flask_login import current_user
from models import SeckillActivity, Goods, Category, Order, User, OrderStatusLog, OrderRemark, Address  
from utils.auth import admin_required, login_required  
from utils import time_utils  
from datetime import datetime, timedelta 
import os  
import uuid  
from utils.redis_client import redis_conn  
from werkzeug.utils import secure_filename  
from models import db
from sqlalchemy.sql import func
import time
from werkzeug.security import generate_password_hash
import pandas as pd
import io
import pdfkit
import logging

# 创建Blueprint对象
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# 管理员面板
@admin_bp.route('/')
@admin_required
def admin_dashboard():
    return render_template('admin/index.html')

# 管理员秒杀活动列表
@admin_bp.route('/seckill/list')
@admin_required
def admin_seckill_list():
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = 20  # 每页显示20条记录
    
    # 构建查询
    query = SeckillActivity.query
    
    # 获取总记录数
    total = query.count()
    
    # 计算总页数
    total_pages = (total + per_page - 1) // per_page
    
    # 获取当前页的数据
    seckill_activities = query.order_by(SeckillActivity.start_time.desc()).offset((page - 1) * per_page).limit(per_page).all()
    
    # 为每个活动添加格式化后的时间字符串
    for activity in seckill_activities:
        activity.start_time_str = activity.start_time.strftime("%Y-%m-%d %H:%M:%S")
        activity.end_time_str = activity.end_time.strftime("%Y-%m-%d %H:%M:%S")
    
    # 创建分页对象
    pagination = type('Pagination', (), {
        'page': page,
        'pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_num': page - 1 if page > 1 else None,
        'next_num': page + 1 if page < total_pages else None
    })
    
    return render_template('admin/seckill/list.html', 
                         activities=seckill_activities,
                         pagination=pagination)

# 管理员：创建秒杀活动
@admin_bp.route('/seckill/create', methods=['GET', 'POST'])
@admin_required
def admin_seckill_create():
    if request.method == 'GET':
        goods_list = Goods.query.all()
        return render_template('admin/seckill/create.html', goods_list=goods_list)
    
    data = request.get_json()
    
    try:
        # 1. 校验必需字段是否存在
        required_fields = ['goods_id', 'start_time', 'end_time', 'seckill_price', 'total_stock']
        for field in required_fields:
            if field not in data:
                return jsonify(code=400, msg=f"缺少必需字段：{field}")
        # 2. 校验商品是否存在
        goods = Goods.query.get(int(data['goods_id']))
        if not goods:
            return jsonify(code=400, msg="选择的商品不存在")
        # 3. 时间格式校验
        start_time = time_utils.parse_iso_datetime(data['start_time'])
        end_time = time_utils.parse_iso_datetime(data['end_time'])
        if not start_time or not end_time:
            return jsonify(code=400, msg="时间格式错误，请使用YYYY-MM-DDTHH:MM格式")
        if end_time <= start_time:
            return jsonify(code=400, msg="结束时间必须晚于开始时间")
        # 4. 基础字段校验
        if data['seckill_price'] <= 0:
            return jsonify(code=400, msg="秒杀价格必须大于0")
        if data['total_stock'] <= 0:
            return jsonify(code=400, msg="总库存必须大于0")
        # 5. 创建秒杀活动
        activity = SeckillActivity(
            goods_id=data['goods_id'],
            start_time=start_time,
            end_time=end_time,
            seckill_price=data['seckill_price'],
            total_stock=data['total_stock'],
            available_stock=data['total_stock']
        )
        db.session.add(activity)
        db.session.commit()
        # 6. Redis库存同步
        stock_key = f"seckill:stock:{activity.id}"
        try:
            redis_conn.hset(stock_key, mapping={
                'total': activity.total_stock,
                'available': activity.available_stock
            })
        except Exception as redis_e:
            db.session.delete(activity)
            db.session.commit()
            return jsonify(code=400, msg=f"Redis库存同步失败（{str(redis_e)}），活动已自动撤销")

        return jsonify(code=200, msg="秒杀活动创建成功")
    except ValueError as ve:
        return jsonify(code=400, msg=f"创建失败：{str(ve)}")
    except Exception as e:
        db.session.rollback()
        return jsonify(code=500, msg=f"系统异常：{str(e)}")

# 更新秒杀活动
@admin_bp.route('/seckill/update/<int:seckill_id>', methods=['GET', 'POST'])
@admin_required
def admin_seckill_update(seckill_id):
    activity = SeckillActivity.query.get_or_404(seckill_id)
    
    if request.method == 'GET':
        goods_list = Goods.query.all()
        return render_template('admin/seckill/update.html', 
                            activity=activity, 
                            goods_list=goods_list)
    
    data = request.form.to_dict()
    try:
        start_time = datetime.strptime(data['start_time'], "%Y-%m-%dT%H:%M")
        end_time = datetime.strptime(data['end_time'], "%Y-%m-%dT%H:%M")
        
        if end_time <= start_time:
            raise ValueError("结束时间必须晚于开始时间")
        if float(data['seckill_price']) <= 0:
            raise ValueError("秒杀价格必须大于0")
        if int(data['total_stock']) <= 0:
            raise ValueError("总库存必须大于0")

        # 计算已售出数量
        sold_quantity = activity.total_stock - activity.available_stock
        new_total_stock = int(data['total_stock'])
        
        # 确保新库存不小于已售出数量
        if new_total_stock < sold_quantity:
            raise ValueError(f"新库存不能小于已售出数量（{sold_quantity}件）")

        # 开始事务
        db.session.begin_nested()
        
        try:
            # 更新 MySQL 数据
            activity.goods_id = int(data['goods_id'])
            activity.start_time = start_time
            activity.end_time = end_time
            activity.seckill_price = float(data['seckill_price'])
            activity.total_stock = new_total_stock
            activity.available_stock = new_total_stock - sold_quantity
            
            # 更新 Redis 数据
            stock_key = f"seckill:stock:{activity.id}"
            try:
                redis_conn.hset(stock_key, mapping={
                    'total': new_total_stock,
                    'available': new_total_stock - sold_quantity
                })
                # 设置过期时间（7天）
                redis_conn.expire(stock_key, 86400 * 7)
            except Exception as redis_e:
                # Redis 更新失败，回滚 MySQL 事务
                db.session.rollback()
                logging.error(f"Redis库存更新失败: {str(redis_e)}")
                raise ValueError(f"Redis库存更新失败: {str(redis_e)}")
            
            # 提交 MySQL 事务
            db.session.commit()
            
            flash("秒杀活动更新成功~")
            return redirect(url_for('admin.admin_seckill_list'))
            
        except Exception as e:
            # 发生任何错误都回滚事务
            db.session.rollback()
            raise e
            
    except ValueError as ve:
        flash(f"参数错误：{str(ve)}")
        return redirect(url_for('admin.admin_seckill_update', seckill_id=seckill_id))
    except Exception as e:
        db.session.rollback()
        flash(f"更新失败：{str(e)}")
        return redirect(url_for('admin.admin_seckill_update', seckill_id=seckill_id))

# 管理员商品列表
@admin_bp.route('/goods/list')
@admin_required
def admin_goods_list():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    search = request.args.get('search', '')
    category_id = request.args.get('category', type=int)
    
    query = Goods.query
    
    if search:
        query = query.filter(Goods.name.like(f'%{search}%'))
    
    if category_id:
        query = query.filter(Goods.category_id == category_id)
    
    total = query.count()
    total_pages = (total + per_page - 1) // per_page
    
    goods_list = query.order_by(Goods.create_time.desc()).offset((page - 1) * per_page).limit(per_page).all()
    categories = Category.query.all()
    
    # 创建分页对象
    pagination = type('Pagination', (), {
        'page': page,
        'pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_num': page - 1 if page > 1 else None,
        'next_num': page + 1 if page < total_pages else None
    })
    
    return render_template('admin/goods/list.html',
                         goods_list=goods_list,
                         categories=categories,
                         pagination=pagination,
                         search=search,
                         current_category=category_id)

# 删除商品接口
@admin_bp.route('/goods/delete/<int:goods_id>', methods=['POST'])
@admin_required
def admin_goods_delete(goods_id):
    try:
        goods = Goods.query.get_or_404(goods_id)
        
        # 开始事务
        db.session.begin_nested()
        
        # 检查是否有相关的秒杀活动
        seckill_activities = SeckillActivity.query.filter_by(goods_id=goods_id).all()
        if seckill_activities:
            # 删除相关的秒杀活动
            for activity in seckill_activities:
                try:
                    # 删除Redis中的相关数据
                    stock_key = f"seckill:stock:{activity.id}"
                    queue_key = f"seckill:queue:{activity.id}"
                    success_key = f"seckill:success:{activity.id}"
                    redis_conn.delete(stock_key, queue_key, success_key)
                except Exception as redis_e:
                    print(f"删除Redis数据失败：{str(redis_e)}")
                finally:
                    # 删除秒杀活动
                    db.session.delete(activity)
        
        # 检查是否有相关的订单
        orders = Order.query.filter_by(goods_id=goods_id).all()
        if orders:
            # 删除相关的订单
            for order in orders:
                # 删除订单相关的备注记录
                OrderRemark.query.filter_by(order_id=order.id).delete()
                # 删除订单状态日志
                OrderStatusLog.query.filter_by(order_id=order.id).delete()
                # 删除订单
                db.session.delete(order)
        
        # 删除商品图片
        if goods.photo_url:
            try:
                os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], goods.photo_url))
            except Exception as e:
                print(f"删除商品图片失败：{str(e)}")
        
        # 删除商品
        db.session.delete(goods)
        
        # 提交事务
        db.session.commit()
        return jsonify({"code": 200, "msg": "商品删除成功"})
        
    except Exception as e:
        # 回滚事务
        db.session.rollback()
        print(f"删除商品失败：{str(e)}")
        return jsonify({"code": 500, "msg": f"删除失败：{str(e)}"})

# 商品编辑
@admin_bp.route('/goods/<int:goods_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_goods_edit(goods_id):
    goods = Goods.query.get_or_404(goods_id)
    
    if request.method == 'POST':
        try:
            goods.name = request.form.get('name')
            goods.description = request.form.get('description')
            goods.price = float(request.form.get('price'))
            goods.original_price = float(request.form.get('original_price'))
            goods.category_id = int(request.form.get('category_id'))
            goods.stock = int(request.form.get('stock'))
            
            goods.brand = request.form.get('brand')
            goods.model = request.form.get('model')
            weight = request.form.get('weight')
            goods.weight = float(weight) if weight else None
            goods.dimensions = request.form.get('dimensions')
            goods.material = request.form.get('material')
            goods.warranty = request.form.get('warranty')
            
            photo = request.files.get('photo')
            if photo and photo.filename:
                # 先删除旧图片
                if goods.photo_url:
                    try:
                        old_photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], goods.photo_url.replace('uploads/', ''))
                        if os.path.exists(old_photo_path):
                            os.remove(old_photo_path)
                    except Exception as e:
                        print(f"删除旧图片失败：{str(e)}")
                
                # 保存新图片
                filename = secure_filename(photo.filename)
                filename = f"{int(time.time())}_{filename}"
                photo.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                # 更新数据库中的路径
                goods.photo_url = f"uploads/{filename}"
            
            db.session.commit()
            flash('商品更新成功！', 'success')
            return redirect(url_for('admin.admin_goods_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败：{str(e)}', 'danger')
    
    categories = Category.query.all()
    return render_template('admin/goods/edit.html', goods=goods, categories=categories)

# 商品信息获取接口
@admin_bp.route('/goods/<int:goods_id>/info', methods=['GET'])
@admin_required
def admin_goods_info(goods_id):
    goods = Goods.query.get_or_404(goods_id)
    return jsonify({
        'id': goods.id,
        'name': goods.name,
        'photo_url': goods.photo_url,
        'original_price': goods.original_price
    })

# 管理员商品分类列表
@admin_bp.route('/category/list')
@admin_required
def admin_category_list():
    categories = Category.query.all()
    return render_template('admin/category/list.html', categories=categories)

# 管理员删除分类路由
@admin_bp.route('/category/delete/<int:category_id>')
@admin_required
def admin_category_delete(category_id):
    category = Category.query.get_or_404(category_id)
    
    if Goods.query.filter_by(category_id=category_id).first():
        flash("该分类下存在商品，无法删除")
        return redirect(url_for('admin.admin_category_list'))
    
    db.session.delete(category)
    db.session.commit()
    flash("分类删除成功~")
    return redirect(url_for('admin.admin_category_list'))

# 管理员创建路由
@admin_bp.route('/create', methods=['GET', 'POST'])
def admin_create():
    if User.query.filter_by(role="admin").first():
        flash("已存在管理员账号，禁止重复创建")
        return redirect(url_for('login'))
    
    if request.method == 'GET':
        return render_template('admin/create.html')
    
    username = request.form['username']
    password = request.form['password']
    
    if User.query.filter_by(username=username).first():
        flash("用户名已存在")
        return redirect(url_for('admin.admin_create'))
    
    password_hash = generate_password_hash(password)
    new_admin = User(username=username, password_hash=password_hash, role="admin")
    db.session.add(new_admin)
    db.session.commit()
    
    flash("管理员账号创建成功，请登录")
    return redirect(url_for('login'))

# 管理员删除秒杀活动
@admin_bp.route('/seckill/delete/<int:seckill_id>', methods=['POST'])
@admin_required
def admin_seckill_delete(seckill_id):
    activity = SeckillActivity.query.get_or_404(seckill_id)
    
    stock_key = f"seckill:stock:{seckill_id}"
    queue_key = f"seckill:queue:{seckill_id}"
    success_key = f"seckill:success:{seckill_id}"
    redis_conn.delete(stock_key, queue_key, success_key)
    
    try:
        db.session.delete(activity)
        db.session.commit()
        return jsonify({"code": 200, "msg": "秒杀活动删除成功"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"删除失败：{str(e)}"})

# 商品详情
@admin_bp.route('/goods/detail/<int:goods_id>')
@admin_required
def admin_goods_detail(goods_id):
    goods = Goods.query.get_or_404(goods_id)
    category = Category.query.get(goods.category_id) if goods.category_id else None
    return render_template('admin/goods/detail.html', goods=goods, category=category)

# 商品分类页
@admin_bp.route('/goods/category/<int:category_id>')
def admin_goods_category(category_id):
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    category = Category.query.get_or_404(category_id)
    total_goods = Goods.query.filter_by(category_id=category_id).count()
    total_pages = (total_goods + per_page - 1) // per_page
    
    goods_list = Goods.query.filter_by(category_id=category_id)\
        .order_by(Goods.create_time.desc())\
        .offset((page - 1) * per_page)\
        .limit(per_page)\
        .all()
        
    return render_template('goods/category.html', 
                         category=category, 
                         goods_list=goods_list,
                         current_page=page,
                         total_pages=total_pages)

# 商品分类创建接口
@admin_bp.route('/category/add', methods=['POST'])
@admin_required
def admin_category_add():
    name = request.form.get('name').strip()
    description = request.form.get('description', '').strip()

    if not name:
        flash('分类名称不能为空', 'danger')
        return redirect(url_for('admin.admin_category_list'))
    
    if Category.query.filter_by(name=name).first():
        flash('该分类名称已存在', 'danger')
        return redirect(url_for('admin.admin_category_list'))

    new_category = Category(name=name, description=description)
    db.session.add(new_category)
    db.session.commit()
    flash('分类创建成功~', 'success')
    return redirect(url_for('admin.admin_category_list'))

# 管理员编辑分类路由
@admin_bp.route('/category/edit/<int:category_id>', methods=['GET', 'POST'])
@admin_required
def admin_category_edit(category_id):
    category = Category.query.get_or_404(category_id)
    
    if request.method == 'GET':
        return render_template('admin/category/edit.html', category=category)
    
    new_name = request.form['name']
    new_description = request.form.get('description', '')
    
    if Category.query.filter(Category.id != category_id, Category.name == new_name).first():
        flash("分类名称已存在")
        return redirect(url_for('admin.admin_category_edit', category_id=category_id))
    
    category.name = new_name
    category.description = new_description
    db.session.commit()
    
    flash("分类更新成功~")
    return redirect(url_for('admin.admin_category_list'))

# 管理员创建分类
@admin_bp.route('/category/create', methods=['GET', 'POST'])
@admin_required
def admin_category_create():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        new_category = Category(name=name, description=description)
        db.session.add(new_category)
        db.session.commit()
        flash("分类创建成功~")
        return redirect(url_for('admin.admin_category_list'))

# 管理员：创建商品
@admin_bp.route('/goods/create', methods=['GET', 'POST'])
@admin_required
def admin_goods_create():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            description = request.form.get('description')
            price = float(request.form.get('price'))
            original_price = float(request.form.get('original_price'))
            category_id = int(request.form.get('category_id'))
            stock = int(request.form.get('stock'))
            
            brand = request.form.get('brand')
            model = request.form.get('model')
            weight = request.form.get('weight')
            dimensions = request.form.get('dimensions')
            material = request.form.get('material')
            warranty = request.form.get('warranty')
            
            photo = request.files.get('photo')
            photo_url = None
            if photo and photo.filename:
                filename = secure_filename(photo.filename)
                filename = f"{int(time.time())}_{filename}"
                # 修改：添加uploads前缀
                photo_url = f"uploads/{filename}"
                photo.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            
            goods = Goods(
                name=name,
                description=description,
                price=price,
                original_price=original_price,
                category_id=category_id,
                stock=stock,
                photo_url=photo_url,
                brand=brand,
                model=model,
                weight=float(weight) if weight else None,
                dimensions=dimensions,
                material=material,
                warranty=warranty
            )
            
            db.session.add(goods)
            db.session.commit()
            
            flash('商品创建成功！', 'success')
            return redirect(url_for('admin.admin_goods_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'创建失败：{str(e)}', 'danger')
    
    categories = Category.query.all()
    return render_template('admin/goods/create.html', categories=categories)

# 管理员订单列表
@admin_bp.route('/orders/list')
@login_required
@admin_required
def order_list():
    # 获取筛选参数
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status = request.args.get('status')
    keyword = request.args.get('keyword', '')
    
    # 构建查询
    query = Order.query
    
    # 应用筛选条件
    if status:
        query = query.filter(Order.status == status)
    
    # 关键词搜索（订单号或用户名）
    if keyword:
        query = query.filter(
            (Order.order_number.like(f'%{keyword}%')) |
            (Order.user.has(User.username.like(f'%{keyword}%')))
        )
    
    # 获取总记录数
    total = query.count()
    
    # 计算总页数
    total_pages = (total + per_page - 1) // per_page
    
    # 获取当前页的数据
    orders = query.order_by(Order.create_time.desc()).offset((page - 1) * per_page).limit(per_page).all()
    
    # 为每个订单添加格式化后的时间字符串
    for order in orders:
        order.create_time_str = order.create_time.strftime("%Y-%m-%d %H:%M:%S")
        if order.pay_time:
            order.pay_time_str = order.pay_time.strftime("%Y-%m-%d %H:%M:%S")
        if order.ship_time:
            order.ship_time_str = order.ship_time.strftime("%Y-%m-%d %H:%M:%S")
        if order.complete_time:
            order.complete_time_str = order.complete_time.strftime("%Y-%m-%d %H:%M:%S")
        if order.cancel_time:
            order.cancel_time_str = order.cancel_time.strftime("%Y-%m-%d %H:%M:%S")
    
    # 创建分页对象
    pagination = type('Pagination', (), {
        'page': page,
        'pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_num': page - 1 if page > 1 else None,
        'next_num': page + 1 if page < total_pages else None
    })

    # 获取统计数据
    today = datetime.now().date()
    month_start = today.replace(day=1)
    
    # 今日订单统计
    today_orders = Order.query.filter(
        db.func.date(Order.create_time) == today
    ).all()
    today_orders_count = len(today_orders)
    today_orders_amount = sum(order.total_amount for order in today_orders)
    
    # 本月订单统计
    month_orders = Order.query.filter(
        db.func.date(Order.create_time) >= month_start
    ).all()
    month_orders_count = len(month_orders)
    month_orders_amount = sum(order.total_amount for order in month_orders)
    
    # 待处理订单统计
    pending_orders = Order.query.filter(
        Order.status.in_(['pending', 'paid'])
    ).all()
    pending_orders_count = len(pending_orders)
    to_be_shipped_count = len([o for o in pending_orders if o.status == 'paid'])
    
    # 已取消订单统计
    cancelled_orders = Order.query.filter(
        Order.status == 'cancelled'
    ).all()
    cancelled_orders_count = len(cancelled_orders)
    
    return render_template('admin/orders/list.html',
                         orders=orders,
                         pagination=pagination,
                         status=status,
                         keyword=keyword,
                         today_orders_count=today_orders_count,
                         today_orders_amount=today_orders_amount,
                         month_orders_count=month_orders_count,
                         month_orders_amount=month_orders_amount,
                         pending_orders_count=pending_orders_count,
                         to_be_shipped_count=to_be_shipped_count,
                         cancelled_orders_count=cancelled_orders_count)

# 管理员订单详情
@admin_bp.route('/orders/<int:order_id>')
@login_required
@admin_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('admin/orders/detail.html', order=order)

# 管理员更新订单状态
@admin_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@login_required
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    new_status = data.get('status')
    
    if not new_status:
        return jsonify({'code': 400, 'msg': '请选择新的订单状态'})
    
    if new_status not in ['pending', 'paid', 'shipped', 'completed', 'cancelled']:
        return jsonify({'code': 400, 'msg': '无效的订单状态'})
    
    # 状态转换检查
    if new_status == 'shipped' and order.status != 'paid':
        return jsonify({'code': 400, 'msg': '只有已支付的订单才能发货'})
    if new_status == 'completed' and order.status != 'shipped':
        return jsonify({'code': 400, 'msg': '只有已发货的订单才能完成'})
    if new_status == 'cancelled' and order.status not in ['pending', 'paid']:
        return jsonify({'code': 400, 'msg': '只有待付款或已支付的订单才能取消'})
    
    try:
        # 记录状态变更日志
        log = OrderStatusLog(
            order_id=order.id,
            old_status=order.status,
            new_status=new_status,
            admin_id=current_user.id,
            remark=data.get('remark', '')
        )
        db.session.add(log)
        
        # 如果是取消订单，需要恢复库存
        if new_status == 'cancelled' and order.status in ['pending', 'paid']:
            if order.activity_id:
                # 如果是秒杀商品，恢复秒杀活动库存
                activity = SeckillActivity.query.get(order.activity_id)
                if activity:
                    activity.available_stock += order.quantity
                    # 同步更新 Redis 库存
                    try:
                        stock_key = f"seckill:stock:{activity.id}"
                        redis_conn.hincrby(stock_key, 'available', order.quantity)
                    except Exception as redis_e:
                        logging.error(f"Redis库存同步失败: {str(redis_e)}")
                        # Redis更新失败时回滚MySQL事务
                        db.session.rollback()
                        return jsonify({'code': 500, 'msg': f'Redis库存同步失败: {str(redis_e)}'})
            else:
                # 如果是普通商品，恢复商品库存
                goods = Goods.query.get(order.goods_id)
                if goods:
                    goods.stock += order.quantity
                    goods.sales -= order.quantity
        
        # 更新订单状态
        order.status = new_status
        if new_status == 'shipped':
            order.ship_time = datetime.now()
        elif new_status == 'completed':
            order.complete_time = datetime.now()
        elif new_status == 'cancelled':
            order.cancel_time = datetime.now()
        
        db.session.commit()
        return jsonify({'code': 200, 'msg': '订单状态更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'更新失败：{str(e)}'})

# 管理员添加订单备注
@admin_bp.route('/orders/remark', methods=['POST'])
@login_required
@admin_required
def add_order_remark():
    order_id = request.form.get('order_id')
    content = request.form.get('content')
    
    if not order_id or not content:
        return jsonify({'code': 400, 'msg': '请提供订单ID和备注内容'})
    
    try:
        remark = OrderRemark(
            order_id=order_id,
            content=content,
            admin_id=current_user.id
        )
        db.session.add(remark)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '备注添加成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'添加失败：{str(e)}'})

def register_admin_routes(app):
    app.register_blueprint(admin_bp)