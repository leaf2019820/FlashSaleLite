from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from utils import time_utils
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)  # 存储密码哈希
    role = db.Column(db.String(10), default="user")  # "user" 或 "admin"
    email = db.Column(db.String(120), unique=True)  # 邮箱
    phone = db.Column(db.String(20), unique=True)  # 手机号
    is_active = db.Column(db.Integer, default=1)  # 账户状态：1-正常，0-封禁
    create_time = db.Column(db.DateTime, default=datetime.utcnow)  # 创建时间

    @property
    def is_admin(self):
        return self.role == "admin"

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # 分类名称（唯一）
    description = db.Column(db.Text)  # 分类描述
    goods = db.relationship('Goods', backref='category', lazy=True)  # 关联商品

class Goods(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    original_price = db.Column(db.Float, nullable=False)
    create_time = db.Column(db.DateTime, default=time_utils.get_current_time())
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    photo_url = db.Column(db.String(255))
    sales = db.Column(db.Integer, nullable=False, default=0)  # 新增：销量字段
    
    # 第一阶段新增字段
    brand = db.Column(db.String(50))  # 品牌
    model = db.Column(db.String(50))  # 型号
    weight = db.Column(db.Float)  # 重量(kg)
    dimensions = db.Column(db.String(50))  # 尺寸(长x宽x高)
    material = db.Column(db.String(100))  # 材质
    warranty = db.Column(db.String(100))  # 保修信息

class SeckillActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    goods_id = db.Column(db.Integer, db.ForeignKey('goods.id'), nullable=False)
    goods = db.relationship('Goods', backref='seckill_activities')
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    seckill_price = db.Column(db.Float, nullable=False)
    total_stock = db.Column(db.Integer, nullable=False)
    available_stock = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='active')  # 新增状态字段

class SeckillOrder(db.Model):
    """记录用户参与秒杀活动的记录"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('seckill_activity.id', ondelete='CASCADE'), nullable=False)
    create_time = db.Column(db.DateTime, default=time_utils.get_current_time)
    
    # 关联关系
    user = db.relationship('User', backref=db.backref('seckill_orders', lazy=True))
    activity = db.relationship('SeckillActivity', backref=db.backref('seckill_orders', lazy=True))

class Order(db.Model):
    """订单模型"""
    __tablename__ = 'order'
    
    # 状态文本映射
    status_text_map = {
        'pending': '待付款',
        'paid': '已付款',
        'shipped': '已发货',
        'completed': '已完成',
        'cancelled': '已取消',
        'refunding': '退款中'
    }
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    goods_id = db.Column(db.Integer, db.ForeignKey('goods.id'), nullable=False)
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('seckill_activity.id'), nullable=True)  # 新增：关联秒杀活动
    quantity = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    payment_method = db.Column(db.String(20))
    transaction_id = db.Column(db.String(100), nullable=True)  # 新增：交易流水号
    create_time = db.Column(db.DateTime, default=time_utils.get_current_time, nullable=False)
    pay_time = db.Column(db.DateTime, nullable=True)
    ship_time = db.Column(db.DateTime, nullable=True)
    complete_time = db.Column(db.DateTime, nullable=True)
    cancel_time = db.Column(db.DateTime, nullable=True)  # 新增：取消时间
    
    # 地址信息字段
    receiver_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(11), nullable=True)
    province = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    district = db.Column(db.String(50), nullable=False)
    detail_address = db.Column(db.String(200), nullable=False)
    
    user = db.relationship('User', backref=db.backref('orders', lazy='dynamic'))
    goods = db.relationship('Goods', backref=db.backref('orders', lazy='dynamic'))
    address = db.relationship('Address', backref=db.backref('orders', lazy='dynamic'))
    activity = db.relationship('SeckillActivity', backref=db.backref('orders', lazy='dynamic'))  # 新增：关联秒杀活动
    
    @property
    def status_text(self):
        return self.status_text_map.get(self.status, '未知状态')
    
    @property
    def status_color(self):
        status_map = {
            'pending': 'warning',
            'paid': 'info',
            'shipped': 'primary',
            'completed': 'success',
            'cancelled': 'danger',
            'refunding': 'warning'
        }
        return status_map.get(self.status, 'secondary')

class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_name = db.Column(db.String(50), nullable=False)  # 收货人姓名
    phone = db.Column(db.String(20), nullable=False)  # 手机号码
    province = db.Column(db.String(50), nullable=False)  # 省份
    city = db.Column(db.String(50), nullable=False)  # 城市
    district = db.Column(db.String(50), nullable=False)  # 区县
    detail_address = db.Column(db.String(200), nullable=False)  # 详细地址
    is_default = db.Column(db.Boolean, default=False)  # 是否默认地址
    create_time = db.Column(db.DateTime, default=datetime.utcnow)  # 创建时间

    # 关联用户
    user = db.relationship('User', backref=db.backref('addresses', lazy=True))

    def __repr__(self):
        return f'<Address {self.id}>'

class OrderStatusLog(db.Model):
    """订单状态变更日志"""
    __tablename__ = 'order_status_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    old_status = db.Column(db.String(20), nullable=False)
    new_status = db.Column(db.String(20), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    remark = db.Column(db.String(200))
    create_time = db.Column(db.DateTime, default=datetime.now)
    
    order = db.relationship('Order', backref=db.backref('status_logs', lazy='dynamic'))
    admin = db.relationship('User', backref=db.backref('order_status_logs', lazy='dynamic'))
    
    @property
    def status_text(self):
        status_map = {
            'pending': '待付款',
            'paid': '已付款',
            'shipped': '已发货',
            'completed': '已完成',
            'cancelled': '已取消',
            'refunding': '退款中'
        }
        return status_map.get(self.new_status, '未知状态')

class OrderRemark(db.Model):
    """订单备注"""
    __tablename__ = 'order_remarks'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now)
    
    order = db.relationship('Order', backref=db.backref('remarks', lazy='dynamic'))
    admin = db.relationship('User', backref=db.backref('order_remarks', lazy='dynamic'))