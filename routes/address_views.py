from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user
from models import db, Address
from utils.auth import login_required

bp = Blueprint('address', __name__)

@bp.route('/address/list')
@login_required
def address_list():
    addresses = Address.query.filter_by(user_id=current_user.id).order_by(Address.is_default.desc(), Address.create_time.desc()).all()
    return render_template('address/list.html', addresses=addresses)

@bp.route('/address/add', methods=['GET', 'POST'])
@login_required
def address_add():
    if request.method == 'GET':
        return render_template('address/add.html')
        
    try:
        # 获取表单数据
        receiver_name = request.form['receiver_name']
        phone = request.form['phone']
        province = request.form['province']
        city = request.form['city']
        district = request.form['district']
        detail_address = request.form['detail_address']
        is_default = request.form.get('is_default') == 'on'

        # 如果设置为默认地址,需要将其他地址设为非默认
        if is_default:
            Address.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})

        # 创建新地址
        address = Address(
            user_id=current_user.id,
            receiver_name=receiver_name,
            phone=phone,
            province=province,
            city=city,
            district=district,
            detail_address=detail_address,
            is_default=is_default
        )
        db.session.add(address)
        db.session.commit()
        flash('地址添加成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'地址添加失败: {str(e)}', 'danger')
    
    return redirect(url_for('address.address_list'))

@bp.route('/address/<int:address_id>/edit', methods=['POST'])
@login_required
def address_edit(address_id):
    address = Address.query.get_or_404(address_id)
    if address.user_id != current_user.id:
        flash('无权操作此地址', 'danger')
        return redirect(url_for('address.address_list'))

    try:
        # 获取表单数据
        address.receiver_name = request.form['receiver_name']
        address.phone = request.form['phone']
        address.province = request.form['province']
        address.city = request.form['city']
        address.district = request.form['district']
        address.detail_address = request.form['detail_address']
        is_default = request.form.get('is_default') == 'on'

        # 如果设置为默认地址,需要将其他地址设为非默认
        if is_default and not address.is_default:
            Address.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})
            address.is_default = True
        elif not is_default and address.is_default:
            address.is_default = False

        db.session.commit()
        flash('地址更新成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'地址更新失败: {str(e)}', 'danger')
    
    return redirect(url_for('address.address_list'))

@bp.route('/address/<int:address_id>/delete', methods=['POST'])
@login_required
def address_delete(address_id):
    address = Address.query.get_or_404(address_id)
    if address.user_id != current_user.id:
        flash('无权操作此地址', 'danger')
        return redirect(url_for('address.address_list'))

    try:
        db.session.delete(address)
        db.session.commit()
        flash('地址删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'地址删除失败: {str(e)}', 'danger')
    
    return redirect(url_for('address.address_list'))

@bp.route('/address/<int:address_id>/set_default', methods=['POST'])
@login_required
def address_set_default(address_id):
    address = Address.query.get_or_404(address_id)
    if address.user_id != current_user.id:
        return jsonify({'code': 403, 'msg': '无权操作此地址'})

    try:
        # 将其他地址设为非默认
        Address.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})
        # 设置当前地址为默认
        address.is_default = True
        db.session.commit()
        flash('设置默认地址成功', 'success')
        return jsonify({'code': 200, 'msg': '设置成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'设置失败: {str(e)}'}) 