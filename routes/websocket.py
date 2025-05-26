from flask import Blueprint
from flask_socketio import SocketIO, emit
from utils.redis_client import SeckillRedis
import json
import threading
import time
from datetime import datetime

websocket_bp = Blueprint('websocket', __name__)
socketio = SocketIO()

def start_seckill_monitor():
    """启动秒杀监控线程"""
    def monitor():
        while True:
            try:
                # 获取所有活动的库存信息
                activities = SeckillActivity.query.filter(
                    SeckillActivity.start_time <= datetime.now(),
                    SeckillActivity.end_time >= datetime.now()
                ).all()
                
                for activity in activities:
                    # 获取Redis中的库存
                    stock = SeckillRedis.get_stock(activity.id)
                    if stock is not None:
                        # 广播库存更新
                        socketio.emit('stock_update', {
                            'activity_id': activity.id,
                            'stock': int(stock)
                        })
                    
                    # 检查活动状态
                    now = datetime.now()
                    if now < activity.start_time:
                        status = 'pending'
                    elif now > activity.end_time:
                        status = 'ended'
                    else:
                        status = 'active'
                    
                    # 广播状态更新
                    socketio.emit('activity_status', {
                        'activity_id': activity.id,
                        'status': status
                    })
                
                time.sleep(1)  # 每秒更新一次
                
            except Exception as e:
                print(f'监控线程错误: {str(e)}')
                time.sleep(5)  # 发生错误时等待5秒后重试
    
    # 启动监控线程
    monitor_thread = threading.Thread(target=monitor, daemon=True)
    monitor_thread.start()

@websocket_bp.route('/ws/seckill')
def seckill_websocket():
    """WebSocket连接处理"""
    return socketio.handle_request()

def init_websocket(app):
    """初始化WebSocket"""
    socketio.init_app(app)
    start_seckill_monitor() 