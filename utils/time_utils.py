from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9+ 标准库，旧版本需安装 pytz
from typing import Optional

def parse_iso_datetime(iso_str: str) -> Optional[datetime]:
    """
    解析ISO 8601时间字符串（支持YYYY-MM-DDTHH:MM和YYYY-MM-DDTHH:MM:SS）
    :param iso_str: 前端传递的时间字符串（如"2024-06-15T14:30"）
    :return: datetime对象，解析失败返回None
    """
    try:
        # 优先尝试完整ISO格式（含秒）
        return datetime.fromisoformat(iso_str)
    except ValueError:
        # 兼容前端datetime-local的分钟级精度（无秒）
        return datetime.strptime(iso_str, "%Y-%m-%dT%H:%M")

def format_iso_datetime(dt: datetime) -> str:
    """
    格式化为前端datetime-local兼容的时间字符串（YYYY-MM-DDTHH:MM）
    :param dt: 数据库中的datetime对象
    :return: 格式化后的字符串（如"2024-06-15T14:30"）
    """
    return dt.strftime("%Y-%m-%dT%H:%M")


def get_current_time():
    """
    统一获取当前上海时区时间（保留 .replace(tzinfo=None) 但返回本地时间）
    所有业务逻辑中需要获取当前时间时调用此方法
    """
    # 获取上海时区的当前时间（带时区信息）
    local_tz = ZoneInfo("Asia/Shanghai")
    local_time_with_tz = datetime.now(local_tz)
    # 移除时区信息，返回朴素时间对象（保留你要求的 .replace(tzinfo=None)）
    return local_time_with_tz.replace(tzinfo=None)

# 可选扩展：支持指定时区的时间获取（示例）
# from datetime import datetime
# from pytz import timezone
# def get_current_time(timezone_name='UTC'):
#     return datetime.now(timezone(timezone_name))