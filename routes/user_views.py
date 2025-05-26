from flask import request, session, redirect, render_template, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import User, Address, Order, Goods, Category, SeckillActivity, OrderStatusLog, OrderRemark
from utils.auth import admin_required 
from werkzeug.security import check_password_hash, generate_password_hash  
from utils.helpers import is_safe_url  
from models import db
from sqlalchemy import func
import random
import time
from utils import time_utils
from datetime import datetime
import logging
from utils.redis_client import redis_conn

def register_user_routes(app):
    # 商品详情接口
    @app.route('/goods/detail/<int:goods_id>')
    def goods_detail(goods_id):
        # 查询商品详情
        goods = Goods.query.get_or_404(goods_id)
        # 获取商品分类
        category = Category.query.get(goods.category_id) if goods.category_id else None
        
        # 查询推荐商品（随机推荐4个其他商品）
        recommended_goods = Goods.query.filter(
            Goods.id != goods_id  # 排除当前商品
        ).order_by(
            func.rand()  # 随机排序
        ).limit(4).all()
        
        return render_template('goods/detail.html', 
                            goods=goods, 
                            recommended_goods=recommended_goods,
                            category=category)

    # 用户登录接口
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'GET':
            next_url = request.args.get('next')
            return render_template('login.html', next=next_url)
        
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if not user:
            return jsonify({
                'code': 400,
                'msg': '用户不存在，请先注册'
            })
        
        if not check_password_hash(user.password_hash, password):
            return jsonify({
                'code': 400,
                'msg': '密码错误，请重试'
            })
        
        # 检查账户状态
        if user.is_active == 0:
            return jsonify({
                'code': 403,
                'msg': '该账户已被封禁，请联系管理员'
            })
        
        # 使用 Flask-Login 的 login_user 函数
        login_user(user)
        
        # 获取重定向URL
        next_url = request.form.get('next')
        if next_url and is_safe_url(next_url):
            redirect_url = next_url
        else:
            redirect_url = url_for('index')
            
        return jsonify({
            'code': 200,
            'msg': '登录成功',
            'redirect': redirect_url
        })

    # 注册路由
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'GET':
            return render_template('register.html')
        
        username = request.form['username']
        password = request.form['password']
        email = request.form.get('email')
        phone = request.form.get('phone')
        
        if not email and not phone:
            flash("请至少提供邮箱或手机号")
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash("用户名已存在")
            return redirect(url_for('register'))
        
        if email and User.query.filter_by(email=email).first():
            flash("该邮箱已被注册")
            return redirect(url_for('register'))
            
        if phone and User.query.filter_by(phone=phone).first():
            flash("该手机号已被注册")
            return redirect(url_for('register'))
        
        password_hash = generate_password_hash(password)
        new_user = User(
            username=username, 
            password_hash=password_hash,
            email=email,
            phone=phone,
            is_active=1  # 设置默认状态为正常
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash("注册成功，请登录")
        return redirect(url_for('login'))

    # 退出登录路由
    @app.route('/logout')
    def logout():
        logout_user()
        flash("已成功退出登录~")
        return redirect(url_for('index'))

    # 商品购买确认
    @app.route('/goods/<int:goods_id>/purchase/confirm', methods=['GET'])
    @login_required
    def goods_purchase_confirm(goods_id):
        goods = Goods.query.get_or_404(goods_id)
        addresses = Address.query.filter_by(user_id=current_user.id).all()
        return render_template('goods/purchase_confirm.html', goods=goods, addresses=addresses)

    # 提交商品购买
    @app.route('/goods/<int:goods_id>/purchase/submit', methods=['POST'])
    @login_required
    def goods_purchase_submit(goods_id):
        goods = Goods.query.get_or_404(goods_id)
        quantity = int(request.form['quantity'])
        address_id = request.form['address_id']
        payment_method = request.form['payment_method']
        activity_id = request.form.get('activity_id')  # 获取活动ID

        if quantity > goods.stock:
            return jsonify({
                'code': 400,
                'msg': f'购买数量超过库存，当前库存：{goods.stock}件'
            })

        try:
            # 如果是秒杀商品，检查用户是否已经参与过该活动
            if activity_id:
                # 检查用户是否有该活动的未取消订单
                existing_order = Order.query.filter_by(
                    user_id=current_user.id,
                    activity_id=activity_id
                ).filter(
                    Order.status != 'cancelled'  # 排除已取消的订单
                ).first()
                
                if existing_order:
                    return jsonify({
                        'code': 400,
                        'msg': '您已经参与过该秒杀活动，不能重复参与'
                    })
                
                # 检查秒杀活动库存
                activity = SeckillActivity.query.get(activity_id)
                if not activity or activity.available_stock < quantity:
                    return jsonify({
                        'code': 400,
                        'msg': '秒杀商品库存不足'
                    })
                
                # 更新秒杀活动库存
                activity.available_stock -= quantity
                db.session.add(activity)
            else:
                # 普通商品库存检查
                affected_rows = Goods.query.filter_by(id=goods_id, stock=goods.stock).update({
                    'stock': goods.stock - quantity,
                    'sales': goods.sales + quantity
                })
                if affected_rows == 0:
                    return jsonify({
                        'code': 400,
                        'msg': '库存已被其他用户抢购，请刷新后重试'
                    })
            
            address = Address.query.get_or_404(address_id)
            
            # 生成订单号：时间戳 + 用户ID + 随机数
            order_number = f"{int(time.time())}{current_user.id}{random.randint(1000, 9999)}"
            
            new_order = Order(
                order_number=order_number,  # 添加订单号
                user_id=current_user.id,
                goods_id=goods_id,
                quantity=quantity,
                address_id=address_id,
                payment_method=payment_method,
                status='pending',
                total_amount=goods.price * quantity,
                activity_id=activity_id,  # 设置活动ID
                # 添加地址信息
                receiver_name=address.receiver_name,
                phone=address.phone,
                province=address.province,
                city=address.city,
                district=address.district,
                detail_address=address.detail_address
            )
            db.session.add(new_order)
            db.session.commit()
            
            return jsonify({
                'code': 200,
                'msg': '下单成功，请尽快完成支付',
                'redirect': url_for('order_detail', order_id=new_order.id)
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'code': 500,
                'msg': f'下单失败：{str(e)}'
            })
        
    # 订单详情
    @app.route('/order/detail/<int:order_id>')
    @login_required
    def order_detail(order_id):
        order = Order.query.get_or_404(order_id)
        if order.user_id != current_user.id:
            flash('无权查看此订单')
            return redirect(url_for('order_list'))
        return render_template('order/detail.html', order=order)

    # 订单列表
    @app.route('/order/list')
    @login_required
    def order_list():
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = 10  # 每页显示10条记录
        
        # 构建查询
        query = Order.query.filter_by(user_id=current_user.id)
        
        # 获取总记录数
        total = query.count()
        
        # 计算总页数
        total_pages = (total + per_page - 1) // per_page
        
        # 获取当前页的数据
        orders = query.order_by(Order.create_time.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        # 为每个订单添加格式化后的时间字符串
        for order in orders:
            order.create_time_str = order.create_time.strftime("%Y-%m-%d %H:%M:%S")
        
        return render_template('order/list.html', 
                            orders=orders, 
                            current_page=page,
                            total_pages=total_pages,
                            total=total)

    # 删除订单
    @app.route('/order/delete/<int:order_id>', methods=['DELETE'])
    @login_required
    def delete_order(order_id):
        order = Order.query.get_or_404(order_id)
        if order.user_id != current_user.id:
            return jsonify({'code': 403, 'msg': '无权操作此订单'})
            
        if order.status not in ['cancelled', 'completed']:
            return jsonify({'code': 400, 'msg': '只能删除已取消或已完成的订单'})
            
        try:
            # 先删除订单相关的备注记录
            OrderRemark.query.filter_by(order_id=order_id).delete()
            
            # 删除订单状态日志
            OrderStatusLog.query.filter_by(order_id=order_id).delete()
            
            # 再删除订单
            db.session.delete(order)
            db.session.commit()
            return jsonify({'code': 200, 'msg': '订单删除成功'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'code': 500, 'msg': f'删除失败：{str(e)}'})

    # 确认支付
    @app.route('/order/<int:order_id>/pay', methods=['POST'])
    @login_required
    def confirm_payment(order_id):
        order = Order.query.get_or_404(order_id)
        if order.user_id != current_user.id:
            return jsonify({'code': 403, 'msg': '无权操作此订单'})
            
        if order.status != 'pending':
            return jsonify({'code': 400, 'msg': '订单状态不正确'})
            
        try:
            # 生成交易流水号：时间戳 + 用户ID + 订单ID + 随机数
            transaction_id = f"{int(time.time())}{current_user.id}{order_id}{random.randint(1000, 9999)}"
            
            order.status = 'paid'
            order.pay_time = datetime.now()
            order.transaction_id = transaction_id
            db.session.commit()
            return jsonify({
                'code': 200, 
                'msg': '支付成功',
                'redirect': url_for('order_detail', order_id=order.id)
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'code': 500, 'msg': f'支付失败：{str(e)}'})

    # 确认收货
    @app.route('/order/<int:order_id>/confirm-receipt', methods=['POST'])
    @login_required
    def confirm_receipt(order_id):
        order = Order.query.get_or_404(order_id)
        if order.user_id != current_user.id:
            return jsonify({'code': 403, 'msg': '无权操作此订单'})
            
        if order.status != 'shipped':
            return jsonify({'code': 400, 'msg': '订单状态不正确'})
            
        try:
            order.status = 'completed'
            order.complete_time = datetime.now()
            db.session.commit()
            return jsonify({'code': 200, 'msg': '确认收货成功'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'code': 500, 'msg': f'操作失败：{str(e)}'})

    # 取消订单
    @app.route('/order/cancel/<int:order_id>', methods=['POST'])
    @login_required
    def cancel_order(order_id):
        order = Order.query.get_or_404(order_id)
        
        # 检查订单是否属于当前用户
        if order.user_id != current_user.id:
            return jsonify({'code': 403, 'msg': '无权操作此订单'})
        
        # 检查订单状态是否可以取消
        if order.status not in ['pending', 'paid']:
            return jsonify({'code': 400, 'msg': '当前订单状态不可取消'})
        
        try:
            # 开始事务
            db.session.begin_nested()
            
            # 恢复库存
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
            order.status = 'cancelled'
            order.cancel_time = datetime.now()
            
            # 记录状态变更日志（用户取消订单不需要admin_id）
            log = OrderStatusLog(
                order_id=order.id,
                old_status=order.status,
                new_status='cancelled',
                admin_id=current_user.id,  # 使用当前用户ID作为admin_id
                remark='用户取消订单'
            )
            db.session.add(log)
            
            # 提交事务
            db.session.commit()
            
            return jsonify({'code': 200, 'msg': '订单取消成功'})
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"取消订单失败: {str(e)}")
            return jsonify({'code': 500, 'msg': f'取消订单失败：{str(e)}'})

    # 首页
    @app.route('/')
    def index():
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = 12  # 每页显示12个商品
        
        # 获取分类参数
        category_id = request.args.get('category', type=int)
        
        # 构建查询
        query = Goods.query
        
        # 如果指定了分类，添加分类过滤
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        # 获取总记录数
        total = query.count()
        
        # 计算总页数
        total_pages = (total + per_page - 1) // per_page
        
        # 获取当前页的数据
        goods_list = query.order_by(Goods.sales.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        # 获取所有分类
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
        
        return render_template('index.html', 
                            goods_list=goods_list,
                            categories=categories,
                            pagination=pagination,
                            current_category=category_id)

    # 修改密码
    @app.route('/user/change-password', methods=['GET', 'POST'])
    @login_required
    def change_password():
        if request.method == 'GET':
            return render_template('user/change_password.html')
            
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if not check_password_hash(current_user.password_hash, old_password):
            return jsonify({
                'code': 400,
                'msg': '原密码错误'
            })
            
        if new_password != confirm_password:
            return jsonify({
                'code': 400,
                'msg': '两次输入的新密码不一致'
            })
            
        try:
            current_user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            logout_user()  # 修改密码后退出登录
            return jsonify({
                'code': 200,
                'msg': '密码修改成功，请重新登录'
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'code': 500,
                'msg': f'密码修改失败：{str(e)}'
            })

    # 重置密码
    @app.route('/user/reset-password', methods=['GET', 'POST'])
    def reset_password():
        if request.method == 'GET':
            return render_template('user/reset_password.html')
            
        email = request.form.get('email')
        phone = request.form.get('phone')
        
        if not email and not phone:
            return jsonify({
                'code': 400,
                'msg': '请至少提供邮箱或手机号'
            })
            
        # 查询用户
        user = None
        if email:
            user = User.query.filter_by(email=email).first()
        if not user and phone:
            user = User.query.filter_by(phone=phone).first()
            
        if not user:
            return jsonify({
                'code': 400,
                'msg': '未找到该用户信息'
            })
            
        try:
            # 如果是首页用户，直接返回固定密码
            if user.username == 'home':
                return jsonify({
                    'code': 200,
                    'msg': '密码重置成功，新密码为：123456'
                })
            
            # 生成新密码
            new_password = '123456'  # 实际应用中应该生成随机密码
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            
            return jsonify({
                'code': 200,
                'msg': f'密码重置成功，新密码为：{new_password}'
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'code': 500,
                'msg': f'密码重置失败：{str(e)}'
            })

    # 用户管理列表
    @app.route('/admin/users')
    @login_required
    @admin_required
    def admin_user_list():
        users = User.query.all()
        return render_template('admin/user_list.html', users=users)

    # 获取用户信息
    @app.route('/admin/users/<int:user_id>', methods=['GET'])
    @login_required
    @admin_required
    def get_user_info(user_id):
        user = User.query.get_or_404(user_id)
        return jsonify({
            'code': 200,
            'data': {
                'id': user.id,
                'username': user.username,
                'is_admin': user.is_admin,
                'is_active': user.is_active
            }
        })

    # 更新用户信息
    @app.route('/admin/users/<int:user_id>', methods=['PUT'])
    @login_required
    @admin_required
    def update_user(user_id):
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        try:
            if 'username' in data and data['username']:
                # 检查用户名是否已存在
                existing_user = User.query.filter(User.username == data['username'], User.id != user_id).first()
                if existing_user:
                    return jsonify({'code': 400, 'msg': '用户名已存在'})
                user.username = data['username']
            
            if 'password' in data and data['password']:
                user.password_hash = generate_password_hash(data['password'])
            
            if 'is_active' in data:
                user.is_active = data['is_active']
            
            db.session.commit()
            return jsonify({'code': 200, 'msg': '更新成功'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'code': 500, 'msg': f'更新失败：{str(e)}'})

    # 删除用户
    @app.route('/admin/users/<int:user_id>', methods=['DELETE'])
    @login_required
    @admin_required
    def delete_user(user_id):
        user = User.query.get_or_404(user_id)
        
        # 不允许删除自己
        if user.id == current_user.id:
            return jsonify({'code': 400, 'msg': '不能删除当前登录用户'})
        
        try:
            # 获取用户的所有订单ID
            order_ids = [order.id for order in Order.query.filter_by(user_id=user_id).all()]
            
            # 删除订单相关的所有记录
            for order_id in order_ids:
                # 删除订单状态日志
                OrderStatusLog.query.filter_by(order_id=order_id).delete()
                # 删除订单备注
                OrderRemark.query.filter_by(order_id=order_id).delete()
            
            # 删除订单
            Order.query.filter_by(user_id=user_id).delete()
            
            # 删除用户的地址记录
            Address.query.filter_by(user_id=user_id).delete()
            
            # 删除用户
            db.session.delete(user)
            db.session.commit()
            return jsonify({'code': 200, 'msg': '删除成功'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'code': 500, 'msg': f'删除失败：{str(e)}'})