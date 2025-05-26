from flask import request, jsonify, render_template, flash, redirect, url_for
from flask_login import current_user
from models import SeckillActivity, Address, Order
from utils.auth import login_required  
from utils import time_utils  
from utils.redis_client import redis_conn, SeckillRedis, check_redis_connection
from models import db
from models import User 
from datetime import datetime
import time
import json
import logging
from functools import wraps
from sqlalchemy import and_
import random

def register_seckill_routes(app):
    # 秒杀活动列表
    @app.route('/seckill/list')
    def seckill_list():
        # 检查Redis连接
        if not check_redis_connection():
            flash('系统维护中，请稍后再试', 'warning')
            return render_template('error.html', message='系统维护中，请稍后再试')
            
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = 12  # 每页显示12个活动
        
        # 获取当前时间
        current_time = time_utils.get_current_time()
        
        # 获取所有秒杀活动并按状态排序
        query = SeckillActivity.query
        
        # 计算总页数
        total = query.count()
        total_pages = (total + per_page - 1) // per_page
        
        # 获取当前页的活动，使用自定义排序
        activities = query.order_by(
            # 进行中的活动优先（当前时间在开始和结束时间之间）
            db.case(
                (db.and_(
                    SeckillActivity.start_time <= current_time,
                    SeckillActivity.end_time >= current_time
                ), 0),
                # 未开始的活动其次（开始时间大于当前时间）
                (SeckillActivity.start_time > current_time, 1),
                # 已结束的活动最后（结束时间小于当前时间）
                else_=2
            ),
            # 同状态的活动按开始时间倒序排列
            SeckillActivity.start_time.desc()
        ).offset((page - 1) * per_page).limit(per_page).all()
        
        # 获取活动信息并缓存
        for activity in activities:
            # 确保加载关联的商品信息
            if not activity.goods:
                continue
                
            # 格式化时间字符串
            activity.start_time_str = activity.start_time.strftime('%Y-%m-%d %H:%M:%S')
            activity.end_time_str = activity.end_time.strftime('%Y-%m-%d %H:%M:%S')
            
            # 设置活动状态
            activity.is_active = activity.start_time <= current_time <= activity.end_time
            
            # 从Redis获取实时库存
            stock_key = f"seckill:stock:{activity.id}"
            redis_stock = redis_conn.hget(stock_key, 'available')
            if redis_stock is not None:
                activity.available_stock = int(redis_stock)
                
            activity_info = {
                'id': activity.id,
                'goods_name': activity.goods.name,
                'goods_photo_url': activity.goods.photo_url,
                'price': float(activity.seckill_price),
                'original_price': float(activity.goods.original_price),
                'stock': activity.available_stock,
                'start_time': activity.start_time_str,
                'end_time': activity.end_time_str
            }
            
            # 初始化Redis库存
            try:
                SeckillRedis.init_activity_stock(activity.id, activity.available_stock)
                SeckillRedis.cache_activity_info(activity.id, activity_info)
            except Exception as e:
                logging.error(f"初始化活动 {activity.id} Redis数据失败: {str(e)}")
                continue
        
        # 获取用户地址列表（如果用户已登录）
        addresses = []
        if current_user.is_authenticated:
            addresses = Address.query.filter_by(user_id=current_user.id).all()
        
        return render_template('seckill/list.html', 
                             activities=activities,
                             addresses=addresses,
                             current_user=current_user,
                             current_page=page,
                             total_pages=total_pages,
                             current_time=current_time)

    # 秒杀活动详情
    @app.route('/seckill/<int:activity_id>')
    def seckill_detail(activity_id):
        activity = SeckillActivity.query.get_or_404(activity_id)
        # 确保活动时间也是本地时间（不带时区信息）
        start_time = activity.start_time.replace(tzinfo=None)
        end_time = activity.end_time.replace(tzinfo=None)
        
        # 格式化时间
        activity.start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        activity.end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 添加时间比较结果用于调试
        now = time_utils.get_current_time()
        activity.is_active = start_time <= now <= end_time
        
        return render_template('seckill/detail.html', activity=activity)

    # 秒杀购买
    @app.route('/seckill/<int:activity_id>/purchase', methods=['POST'])
    @login_required
    def seckill_purchase(activity_id):
        # 检查Redis连接
        if not check_redis_connection():
            return jsonify({'code': 500, 'msg': '系统维护中，请稍后再试'})
            
        user_id = current_user.id
        logging.info(f'开始处理秒杀请求 - 用户ID: {user_id}, 活动ID: {activity_id}')
        
        try:
            # 1. 接口限流
            if not SeckillRedis.rate_limit(user_id):
                logging.warning(f'用户 {user_id} 请求过于频繁')
                return jsonify({'code': 429, 'msg': '请求过于频繁，请稍后再试'})
            
            # 2. 检查用户是否已参与
            if SeckillRedis.check_user_participated(user_id, activity_id):
                logging.warning(f'用户 {user_id} 已经参与过活动 {activity_id}')
                return jsonify({'code': 400, 'msg': '您已经参与过该活动'})
            
            # 3. 获取请求参数
            data = request.get_json()
            if not data:
                logging.error('请求数据为空')
                return jsonify({'code': 400, 'msg': '请求数据不能为空'})
            
            address_id = data.get('address_id')
            payment_method = data.get('payment_method')
            
            if not address_id or not payment_method:
                logging.error('缺少必要参数')
                return jsonify({'code': 400, 'msg': '请选择收货地址和支付方式'})
            
            # 4. 获取活动信息
            activity = SeckillActivity.query.get(activity_id)
            if not activity:
                logging.error(f'活动 {activity_id} 不存在')
                return jsonify({'code': 404, 'msg': '活动不存在'})
            
            # 5. 检查活动状态
            now = datetime.now()
            if now < activity.start_time:
                logging.warning(f'活动 {activity_id} 未开始')
                return jsonify({'code': 400, 'msg': '活动未开始'})
            if now > activity.end_time:
                logging.warning(f'活动 {activity_id} 已结束')
                return jsonify({'code': 400, 'msg': '活动已结束'})
            
            # 6. 获取用户地址
            address = Address.query.get(address_id)
            if not address or address.user_id != user_id:
                logging.error(f'地址 {address_id} 不存在或不属于用户 {user_id}')
                return jsonify({'code': 400, 'msg': '收货地址不存在'})
            
            # 7. 预减库存
            if not SeckillRedis.pre_reduce_stock(activity_id):
                logging.warning(f'活动 {activity_id} 库存不足')
                return jsonify({'code': 400, 'msg': '库存不足'})
            
            # 8. 设置用户活动锁
            if not SeckillRedis.set_user_activity_lock(user_id, activity_id):
                logging.warning(f'用户 {user_id} 操作过于频繁')
                return jsonify({'code': 400, 'msg': '操作太频繁，请稍后再试'})
            
            try:
                # 9. 创建订单
                order_number = f"{int(time.time())}{user_id}{random.randint(1000, 9999)}"
                new_order = Order(
                    order_number=order_number,
                    user_id=current_user.id,
                    goods_id=activity.goods_id,
                    quantity=1,
                    address_id=address_id,
                    payment_method=payment_method,
                    status='pending',
                    total_amount=activity.seckill_price,
                    activity_id=activity.id,
                    # 添加地址信息
                    receiver_name=address.receiver_name,
                    phone=address.phone,
                    province=address.province,
                    city=address.city,
                    district=address.district,
                    detail_address=address.detail_address
                )
                db.session.add(new_order)
                
                # 10. 扣减MySQL库存（使用乐观锁）
                affected_rows = SeckillActivity.query.filter_by(
                    id=activity_id,
                    available_stock=activity.available_stock  # 版本号校验
                ).update({
                    'available_stock': activity.available_stock - 1
                })
                
                if not affected_rows:
                    # 如果MySQL库存扣减失败，回滚Redis库存
                    SeckillRedis.increase_stock(activity_id)
                    db.session.rollback()
                    return jsonify({'code': 400, 'msg': '库存已被其他用户抢购，请刷新后重试'})
                
                # 提交事务
                db.session.commit()
                
                # 11. 标记用户已参与
                SeckillRedis.mark_user_participated(user_id, activity_id)
                
                return jsonify({
                    'code': 200,
                    'msg': '下单成功，请尽快完成支付',
                    'order_id': new_order.id,
                    'redirect': url_for('order_detail', order_id=new_order.id)
                })
                
            except Exception as e:
                # 发生异常时回滚Redis库存
                SeckillRedis.increase_stock(activity_id)
                db.session.rollback()
                logging.error(f'创建订单失败: {str(e)}')
                return jsonify({'code': 500, 'msg': '下单失败，请稍后重试'})
                
        except Exception as e:
            logging.error(f'秒杀处理异常: {str(e)}')
            return jsonify({'code': 500, 'msg': '系统异常，请稍后重试'})

    @app.route('/seckill/<int:activity_id>/status')
    @login_required
    def check_status(activity_id):
        """检查秒杀状态"""
        user_id = current_user.id
        
        # 检查订单是否成功
        if SeckillRedis.is_order_success(activity_id, user_id):
            return jsonify({'code': 200, 'msg': '秒杀成功'})
        
        # 检查队列位置
        queue_length = SeckillRedis.get_queue_length(activity_id)
        if queue_length > 0:
            return jsonify({'code': 202, 'msg': '正在处理中', 'data': {'queue_length': queue_length}})
        
        return jsonify({'code': 400, 'msg': '秒杀失败'})