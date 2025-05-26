# 商品相关路由
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db, Goods, Category
from utils.auth import login_required, admin_required

bp = Blueprint('goods', __name__)

# 首页
@app.route('/')
def index():
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = 8  # 每页显示12个商品
        
        # 查询商品列表
        query = Goods.query.options(
            db.joinedload(Goods.category)
        ).order_by(Goods.create_time.desc())
        
        # 使用paginate进行分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 获取所有分类
        categories = Category.query.all()
        
        return render_template('index.html', 
                            goods_list=pagination.items,
                            categories=categories,
                            pagination=pagination)
    except Exception as e:
        app.logger.error(f'获取商品列表失败：{str(e)}')
        flash('获取商品列表失败，请稍后重试', 'danger')
        return redirect(url_for('index')) 