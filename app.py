from flask import Flask, session, jsonify, request, redirect, render_template
from flask_login import LoginManager
from models import db, User, Goods, SeckillActivity, Order, Category, Address
from utils.auth import login_required, admin_required
from utils.redis_client import redis_conn
import threading
from urllib.parse import urlparse, urljoin
from functools import wraps
from routes.user_views import register_user_routes
from routes.admin_views import register_admin_routes
from routes.seckill_views import register_seckill_routes
from routes.address_views import bp as address_bp  # 新增：导入地址管理蓝图
from routes.order_views import register_order_routes  # 新增：导入订单路由
import os

app = Flask(__name__)
app.secret_key = "your-secret-key-here"  # 生产环境需替换为随机字符串

# 初始化 LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# MySQL 配置（根据本地环境修改）
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:123456@127.0.0.1:3306/flashsale?charset=utf8mb4'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = { 
    'connect_args': {
        'init_command': 'SET SESSION time_zone = "+08:00"'
    }
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 文件上传配置
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小为16MB

# 确保上传目录存在
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db.init_app(app)

# 注册路由
register_user_routes(app)
register_admin_routes(app)
register_seckill_routes(app)
register_order_routes(app)  # 新增：注册订单路由
app.register_blueprint(address_bp)  # 新增：注册地址管理蓝图

# 初始化数据库（首次运行时执行）
with app.app_context():
    db.create_all()

# 普通用户：提交秒杀请求（核心逻辑）
# 在 app.py 全局作用域初始化队列处理线程（仅启动一次）
def start_background_queue_processor():
    def process_queue():
        while True:
            try:
                # 遍历所有可能的秒杀活动队列（实际可优化为监听特定键）
                queue_keys = redis_conn.keys("seckill:queue:*")
                for queue_key in queue_keys:
                    _, request_data = redis_conn.blpop(queue_key, timeout=10)
                    if not request_data:
                        continue
                    # 解析入队的4个字段：user_id,时间戳,address_id,payment_method（与入队格式一致）
                    user_id, timestamp, address_id, payment_method = request_data.split(',')  # 关键修改：调整为4字段解析
                    item_id = queue_key.split(":")[-1]

                    # 双重校验库存（Redis+MySQL）
                    stock_key = f"seckill:stock:{item_id}"
                    with app.app_context():
                        # 先查MySQL当前库存（防止Redis与DB不同步）
                        activity = db.session.get(SeckillActivity, item_id)
                        if not activity or activity.available_stock <= 0:
                            # 库存不足，不需要回滚Redis库存，因为预减库存时已经减过了
                            continue

                        # 原子扣减MySQL库存（使用乐观锁）
                        affected_rows = SeckillActivity.query.filter_by(
                            id=item_id,
                            available_stock=activity.available_stock  # 版本号校验
                        ).update({
                            'available_stock': activity.available_stock - 1
                        })
                        if not affected_rows:
                            # 库存已被修改，回滚Redis库存
                            redis_conn.hincrby(stock_key, 'available', 1)
                            continue

                        # 查询地址详细信息（从数据库获取）
                        address = Address.query.get_or_404(address_id)
                        receiver = address.receiver
                        phone = address.phone
                        detail = address.detail

                        # 创建订单（使用查询到的地址信息和解析出的支付方式）
                        order = Order(
                            user_id=user_id,
                            activity_id=item_id,
                            goods_id=activity.goods_id,
                            quantity=1,
                            status='pending',  # 修改为pending状态
                            payment_method=payment_method,
                            receiver_name=address.receiver_name,
                            phone=address.phone,
                            province=address.province,
                            city=address.city,
                            district=address.district,
                            detail_address=address.detail_address,
                            total_amount=activity.seckill_price  # 添加总金额
                        )
                        db.session.add(order)
                        db.session.commit()

                        # 记录成功用户
                        redis_conn.sadd(f"seckill:success:{item_id}", user_id)
            except Exception as e:
                print(f"后台队列处理发生错误: {e}")
    # 启动后台线程（应用启动时执行一次）
    threading.Thread(target=process_queue, daemon=True).start()
# 在 app 初始化后调用（例如在 if __name__ == '__main__' 前）
start_background_queue_processor()

# 秒杀活动列表（管理员查看）
@app.context_processor
def inject_categories():
    categories = Category.query.all()
    return dict(categories=categories)

# 新增一个库存校验接口，用于前端AJAX调用：
@app.route('/goods/<int:goods_id>/check_stock')
@login_required  # 可选：根据业务需求添加登录校验
def check_goods_stock(goods_id):
    """前端实时校验库存接口"""
    quantity = request.args.get('quantity', type=int)
    if not quantity or quantity < 1:
        return jsonify(valid=False, message="请输入1件及以上的购买数量")
    
    goods = Goods.query.get_or_404(goods_id)
    if quantity > goods.stock:
        return jsonify(
            valid=False,
            message=f"库存不足，当前可用库存：{goods.stock}件"
        )
    return jsonify(valid=True, message="库存充足")

if __name__ == '__main__':
    app.run(debug=True)