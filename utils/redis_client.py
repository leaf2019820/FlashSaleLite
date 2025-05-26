import redis
from flask import current_app
import json
import time
import logging

# Redis连接池
pool = redis.ConnectionPool(
    host='127.0.0.1',
    port=6379,
    db=0,
    decode_responses=True
)

# Redis客户端
redis_conn = redis.Redis(connection_pool=pool)

# 检查Redis连接
def check_redis_connection():
    try:
        redis_conn.ping()
        return True
    except redis.ConnectionError as e:
        logging.error(f"Redis连接失败: {str(e)}")
        return False

class SeckillRedis:
    @staticmethod
    def init_activity_stock(activity_id, total_stock):
        """初始化活动库存"""
        if not check_redis_connection():
            raise redis.ConnectionError("Redis连接失败")
            
        stock_key = f"seckill:stock:{activity_id}"
        try:
            redis_conn.hset(stock_key, mapping={
                'total': total_stock,
                'available': total_stock
            })
            redis_conn.expire(stock_key, 86400 * 7)  # 7天过期
            return True
        except Exception as e:
            logging.error(f"初始化库存失败: {str(e)}")
            return False

    @staticmethod
    def pre_reduce_stock(activity_id):
        """预减库存"""
        if not check_redis_connection():
            raise redis.ConnectionError("Redis连接失败")
            
        stock_key = f"seckill:stock:{activity_id}"
        with redis_conn.pipeline() as pipe:
            try:
                pipe.watch(stock_key)
                stock = pipe.hget(stock_key, 'available')
                if not stock:
                    logging.error(f"活动 {activity_id} 库存不存在")
                    return False
                    
                if int(stock) > 0:
                    pipe.multi()
                    pipe.hincrby(stock_key, 'available', -1)
                    return pipe.execute()
                return False
            except redis.WatchError:
                logging.error(f"活动 {activity_id} 库存被修改")
                return False
            except Exception as e:
                logging.error(f"预减库存失败: {str(e)}")
                return False

    @staticmethod
    def increase_stock(activity_id):
        """增加库存"""
        if not check_redis_connection():
            raise redis.ConnectionError("Redis连接失败")
            
        stock_key = f"seckill:stock:{activity_id}"
        try:
            redis_conn.hincrby(stock_key, 'available', 1)
            return True
        except Exception as e:
            logging.error(f"增加库存失败: {str(e)}")
            return False

    @staticmethod
    def get_stock(activity_id):
        """获取库存"""
        if not check_redis_connection():
            raise redis.ConnectionError("Redis连接失败")
            
        stock_key = f"seckill:stock:{activity_id}"
        try:
            return redis_conn.hget(stock_key, 'available')
        except Exception as e:
            logging.error(f"获取库存失败: {str(e)}")
            return None

    @staticmethod
    def set_user_activity_lock(user_id, activity_id, expire=10):
        """设置用户活动锁"""
        if not check_redis_connection():
            raise redis.ConnectionError("Redis连接失败")
            
        lock_key = f"seckill:lock:{activity_id}:{user_id}"
        try:
            return redis_conn.set(lock_key, 1, ex=expire, nx=True)
        except Exception as e:
            logging.error(f"设置用户活动锁失败: {str(e)}")
            return False

    @staticmethod
    def release_user_activity_lock(user_id, activity_id):
        """释放用户活动锁"""
        if not check_redis_connection():
            raise redis.ConnectionError("Redis连接失败")
            
        lock_key = f"seckill:lock:{activity_id}:{user_id}"
        try:
            redis_conn.delete(lock_key)
            return True
        except Exception as e:
            logging.error(f"释放用户活动锁失败: {str(e)}")
            return False

    @staticmethod
    def check_user_participated(user_id, activity_id):
        """检查用户是否参与过活动"""
        if not check_redis_connection():
            raise redis.ConnectionError("Redis连接失败")
            
        participated_key = f"seckill:participated:{activity_id}:{user_id}"
        try:
            return redis_conn.exists(participated_key)
        except Exception as e:
            logging.error(f"检查用户参与状态失败: {str(e)}")
            return False

    @staticmethod
    def mark_user_participated(user_id, activity_id):
        """标记用户已参与活动"""
        if not check_redis_connection():
            raise redis.ConnectionError("Redis连接失败")
            
        participated_key = f"seckill:participated:{activity_id}:{user_id}"
        try:
            redis_conn.set(participated_key, 1, ex=86400 * 7)  # 7天过期
            return True
        except Exception as e:
            logging.error(f"标记用户参与失败: {str(e)}")
            return False

    @staticmethod
    def rate_limit(user_id, limit=10, period=60):
        """接口限流"""
        if not check_redis_connection():
            raise redis.ConnectionError("Redis连接失败")
            
        key = f"seckill:limit:{user_id}"
        try:
            count = redis_conn.incr(key)
            if count == 1:
                redis_conn.expire(key, period)
            return count <= limit
        except Exception as e:
            logging.error(f"限流检查失败: {str(e)}")
            return False

    @staticmethod
    def cache_activity_info(activity_id, activity_info):
        """缓存活动信息"""
        key = f"seckill:info:{activity_id}"
        redis_conn.set(key, json.dumps(activity_info), ex=3600)  # 1小时过期

    @staticmethod
    def get_activity_info(activity_id):
        """获取活动信息"""
        key = f"seckill:info:{activity_id}"
        info = redis_conn.get(key)
        return json.loads(info) if info else None

    @staticmethod
    def add_to_queue(activity_id, user_id, address_id, payment_method):
        """添加到秒杀队列"""
        if not check_redis_connection():
            raise redis.ConnectionError("Redis连接失败")
            
        queue_key = f"seckill:queue:{activity_id}"
        try:
            message = {
                'user_id': user_id,
                'address_id': address_id,
                'payment_method': payment_method,
                'timestamp': time.time()
            }
            redis_conn.lpush(queue_key, json.dumps(message))
            redis_conn.expire(queue_key, 3600)  # 1小时过期
            return True
        except Exception as e:
            logging.error(f"添加到队列失败: {str(e)}")
            return False

    @staticmethod
    def get_queue_length(activity_id):
        """获取队列长度"""
        if not check_redis_connection():
            raise redis.ConnectionError("Redis连接失败")
            
        queue_key = f"seckill:queue:{activity_id}"
        try:
            return redis_conn.llen(queue_key)
        except Exception as e:
            logging.error(f"获取队列长度失败: {str(e)}")
            return 0

    @staticmethod
    def mark_order_success(activity_id, user_id):
        """标记订单成功"""
        if not check_redis_connection():
            raise redis.ConnectionError("Redis连接失败")
            
        success_key = f"seckill:success:{activity_id}"
        try:
            redis_conn.sadd(success_key, user_id)
            redis_conn.expire(success_key, 86400 * 7)  # 7天过期
            return True
        except Exception as e:
            logging.error(f"标记订单成功失败: {str(e)}")
            return False

    @staticmethod
    def is_order_success(activity_id, user_id):
        """检查订单是否成功"""
        if not check_redis_connection():
            raise redis.ConnectionError("Redis连接失败")
            
        success_key = f"seckill:success:{activity_id}"
        try:
            return redis_conn.sismember(success_key, user_id)
        except Exception as e:
            logging.error(f"检查订单状态失败: {str(e)}")
            return False
