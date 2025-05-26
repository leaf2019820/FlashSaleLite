from functools import wraps
from flask import jsonify, redirect, url_for, request, flash
from flask_login import current_user, login_required as flask_login_required

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.accept_mimetypes.accept_json:
                return jsonify(code=401, msg="请先登录"), 401
            else:
                # 普通页面请求重定向到登录页
                return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            # 页面请求重定向到登录页，API请求返回JSON
            if request.accept_mimetypes.accept_html:
                flash("非法访问！请重新登陆！")
                return redirect(url_for('login', next=request.url))
            else:
                return jsonify(code=401, msg="请先登录"), 401
        
        if current_user.role != "admin":
            # 页面请求提示并跳转，API请求返回JSON
            if request.accept_mimetypes.accept_html:
                flash("无管理员权限")
                return redirect(url_for('index'))  # 跳转到首页或上一页
            else:
                return jsonify(code=403, msg="无管理员权限"), 403
        
        return f(*args, **kwargs)
    return decorated_function