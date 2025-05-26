from flask import request, jsonify, render_template, flash, redirect, url_for
from flask_login import current_user
from models import Order
from utils.auth import login_required
from models import db

def register_order_routes(app):
    pass  # 所有订单相关的路由都在user_views.py中实现 