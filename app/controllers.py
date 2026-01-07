from flask import render_template, request, redirect, url_for, flash, jsonify, session
import math
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.security import check_password_hash


def login_required(f):
    """登录验证装饰器，检查会话是否超时"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查session中是否有用户信息
        user_id = request.cookies.get('user_id')
        if not user_id:
            return redirect(url_for('login'))
        
        # 检查会话时间
        last_activity = session.get('last_activity')
        if last_activity:
            # 将字符串转换为datetime对象
            last_activity = datetime.fromisoformat(last_activity)
            # 检查是否超过30分钟
            if datetime.now() - last_activity > timedelta(minutes=30):
                # 清除会话
                session.clear()
                flash('会话已超时，请重新登录！', 'error')
                return redirect(url_for('login'))
        
        # 更新最后活动时间
        session['last_activity'] = datetime.now().isoformat()
        
        from app.models import User
        user = User.query.get(int(user_id))
        if not user:
            return redirect(url_for('login'))
        
        # 将用户信息传递给视图函数
        return f(user=user, *args, **kwargs)
    
    return decorated_function


def admin_required(f):
    """管理员权限验证装饰器，检查会话是否超时"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.cookies.get('user_id')
        if not user_id:
            return redirect(url_for('login'))
        
        # 检查会话时间
        last_activity = session.get('last_activity')
        if last_activity:
            last_activity = datetime.fromisoformat(last_activity)
            if datetime.now() - last_activity > timedelta(minutes=30):
                session.clear()
                flash('会话已超时，请重新登录！', 'error')
                return redirect(url_for('login'))
        
        # 更新最后活动时间
        session['last_activity'] = datetime.now().isoformat()
        
        from app.models import User, UserRole
        user = User.query.get(int(user_id))
        if not user or user.role.name != 'ADMIN':
            flash('权限不足！', 'error')
            return redirect(url_for('index'))
        
        return f(user=user, *args, **kwargs)
    
    return decorated_function


def register_routes(app, db):
    # 导入模型
    from app.models import Product, Workshop, Process, Equipment, Order, ProductionSchedule, User, UserRole

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """用户登录"""
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = User.query.filter_by(username=username).first()
            
            if user and check_password_hash(user.password, password):
                # 登录成功，设置session信息
                from flask import make_response
                response = make_response(redirect(url_for('index')))
                response.set_cookie('user_id', str(user.id))
                return response
            else:
                flash('用户名或密码错误！', 'error')
        
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        """用户登出"""
        from flask import make_response
        response = make_response(redirect(url_for('login')))
        response.set_cookie('user_id', '', expires=0)
        flash('已成功退出登录！', 'success')
        return response

    @app.route('/')
    @login_required
    def index(user):
        """首页"""
        return render_template('index.html', user=user)

    @app.route('/order_management')
    @login_required
    def order_management(user):
        """订单管理页面"""
        orders = Order.query.all()
        return render_template('order_management.html', orders=orders, user=user)

    @app.route('/order/create', methods=['GET', 'POST'])
    @login_required
    def create_order(user):
        """创建订单 - 普通用户及以上权限"""
        # 检查用户权限
        if user.role != UserRole.ADMIN and user.role != UserRole.USER:
            flash('权限不足！', 'error')
            return redirect(url_for('index'))
            
        if request.method == 'POST':
            # 获取表单数据
            customer_name = request.form.get('customer_name', '')
            product_model = request.form.get('product_model')
            length = float(request.form.get('length'))
            width = float(request.form.get('width'))
            thickness_mm = float(request.form.get('thickness'))  # 用户输入的厚度单位是毫米，直接使用
            shipping_quantity = int(request.form.get('shipping_quantity'))
            yield_rate = float(request.form.get('yield_rate'))
            shipping_date_str = request.form.get('shipping_date')
            shipping_date = datetime.strptime(shipping_date_str, '%Y-%m-%d')
            raw_glass_size = request.form.get('raw_glass_size')
            workshop = request.form.get('workshop')
            
            # 计算投产数量
            calculated_quantity = math.ceil(shipping_quantity / yield_rate)
            
            # 计算叠数 - 直接使用毫米单位
            nesting_count = calculate_nesting_count(thickness_mm)
            
            # 计算切数
            cutting_count = calculate_cutting_count(length, width, raw_glass_size)
            
            # 创建产品 - 直接存储毫米单位
            product = Product(
                product_model=product_model,
                length=length,
                width=width,
                thickness=thickness_mm,  # 直接存储为毫米单位
                shipping_quantity=shipping_quantity,
                yield_rate=yield_rate,
                shipping_date=shipping_date,
                raw_glass_size=raw_glass_size,
                workshop=workshop,
                calculated_quantity=calculated_quantity,
                nesting_count=nesting_count,
                cutting_count=cutting_count
            )
            
            db.session.add(product)
            db.session.flush()  # 获取ID但不提交
            
            # 创建订单
            order = Order(
                order_number=f"ORDER_{product.id}_{int(datetime.now().timestamp())}",
                product_id=product.id,
                customer_name=customer_name,
                order_status='pending'
            )
            
            db.session.add(order)
            db.session.commit()
            
            flash('订单创建成功！', 'success')
            return redirect(url_for('order_management'))
        
        return render_template('create_order.html', user=user)

    @app.route('/order/<int:order_id>/view')
    @login_required
    def view_order(order_id, user):
        """查看订单详情"""
        order = Order.query.get_or_404(order_id)
        return render_template('view_order.html', order=order, user=user)

    @app.route('/order/<int:order_id>/edit', methods=['GET', 'POST'])
    @admin_required
    def edit_order(order_id, user):
        """编辑订单 - 仅管理员"""
        order = Order.query.get_or_404(order_id)
        if request.method == 'POST':
            # 更新订单数据
            product = order.product
            product.product_model = request.form.get('product_model')
            product.length = float(request.form.get('length'))
            product.width = float(request.form.get('width'))
            thickness_mm = float(request.form.get('thickness'))  # 用户输入的厚度单位是毫米，直接使用
            product.thickness = thickness_mm  # 直接存储为毫米单位
            product.shipping_quantity = int(request.form.get('shipping_quantity'))
            product.yield_rate = float(request.form.get('yield_rate'))
            shipping_date_str = request.form.get('shipping_date')
            product.shipping_date = datetime.strptime(shipping_date_str, '%Y-%m-%d')
            product.raw_glass_size = request.form.get('raw_glass_size')
            product.workshop = request.form.get('workshop')
            
            # 更新订单信息
            order.customer_name = request.form.get('customer_name', '')
            
            # 重新计算相关值
            product.calculated_quantity = math.ceil(product.shipping_quantity / product.yield_rate)
            product.nesting_count = calculate_nesting_count(product.thickness)  # 直接使用毫米单位
            product.cutting_count = calculate_cutting_count(product.length, product.width, product.raw_glass_size)
            
            db.session.commit()
            flash('订单更新成功！', 'success')
            return redirect(url_for('order_management'))
        
        return render_template('edit_order.html', order=order, user=user)

    @app.route('/order/<int:order_id>/delete', methods=['POST'])
    @admin_required
    def delete_order(order_id, user):
        """删除订单 - 仅管理员"""
        order = Order.query.get_or_404(order_id)
        
        # 删除与该订单相关的产品及其所有排程
        product = order.product
        # 删除与该产品相关的所有排程记录
        ProductionSchedule.query.filter_by(product_id=product.id).delete()
        
        # 删除订单和产品
        db.session.delete(order)
        db.session.delete(product)
        db.session.commit()
        
        flash('订单删除成功！', 'success')
        return redirect(url_for('order_management'))

    @app.route('/capacity_management')
    @admin_required
    def capacity_management(user):
        """产能管理页面"""
        workshops = Workshop.query.all()
        processes = Process.query.all()
        equipments = Equipment.query.all()
        
        # 按工序组织设备数据
        equipment_data = {}
        for equipment in equipments:
            if equipment.process_id not in equipment_data:
                equipment_data[equipment.process_id] = []
            equipment_data[equipment.process_id].append(equipment)
        
        return render_template('capacity_management.html', 
                               workshops=workshops, 
                               processes=processes, 
                               equipments=equipments,
                               equipment_data=equipment_data,
                               user=user)

    @app.route('/overall_production_schedule')
    @login_required
    def overall_production_schedule(user):
        """整体排产查看页面"""
        # 获取请求参数中的车间过滤条件
        selected_workshop_name = request.args.get('workshop', 'UTG1车间')  # 默认为UTG1车间
        
        # 查询数据并按日期、工序和小时排序，确保按时间顺序处理
        schedules = ProductionSchedule.query.join(Workshop).filter(Workshop.name == selected_workshop_name).order_by(
            ProductionSchedule.schedule_date,
            ProductionSchedule.hour
        ).all()
        products = Product.query.all()
        processes = Process.query.all()
        workshops = Workshop.query.all()
        
        # 按日期和工序聚合排程数据
        schedule_data = {}
        
        # 遍历所有排程记录，按日期和工序组织
        for schedule in schedules:
            date_str = schedule.schedule_date.strftime('%Y-%m-%d')
            process_key = f"{schedule.workshop.name}_{schedule.process.name}"
            
            # 初始化日期和工序数据
            if date_str not in schedule_data:
                schedule_data[date_str] = {}
            if process_key not in schedule_data[date_str]:
                # 为每个工序初始化24小时的数据结构
                schedule_data[date_str][process_key] = {str(hour): {'products': []} for hour in range(24)}
            
            # 更新特定小时的数据
            hour_str = str(schedule.hour)
            if hour_str in schedule_data[date_str][process_key]:
                current_data = schedule_data[date_str][process_key][hour_str]
                
                # 检查是否已有相同产品型号的记录
                existing_product = None
                for prod in current_data['products']:
                    if prod['product_model'] == schedule.product.product_model:
                        existing_product = prod
                        break
                
                if existing_product:
                    # 如果已存在相同产品型号，累加数量
                    existing_product['quantity'] += schedule.production_quantity
                else:
                    # 添加新的产品型号记录
                    # 获取该工序的设备数量
                    equipment_count = db.session.query(db.func.sum(Equipment.quantity)).join(Process).filter(
                        Process.id == schedule.process.id
                    ).scalar() or 0
                    
                    # 计算该产品在当前工序的累积已投数量 - 截至当前时间点（含）的累计产量
                    # 查询该产品在当前工序、截至当前时间点的所有产量
                    cumulative_investment = db.session.query(db.func.sum(ProductionSchedule.production_quantity)).join(
                        Workshop
                    ).filter(
                        ProductionSchedule.product_id == schedule.product.id,
                        ProductionSchedule.process_id == schedule.process.id,  # 确保只计算当前工序
                        Workshop.name == selected_workshop_name,
                        # 计算从开始到当前时间点的所有产量
                        db.or_(
                            ProductionSchedule.schedule_date < schedule.schedule_date,
                            db.and_(
                                ProductionSchedule.schedule_date == schedule.schedule_date,
                                ProductionSchedule.hour <= schedule.hour
                            )
                        )
                    ).scalar() or 0
                    
                    product_info = {
                        'product_model': schedule.product.product_model,
                        'quantity': schedule.production_quantity,
                        'equipment_count': equipment_count,
                        'cumulative_investment': cumulative_investment  # 截至当前时间点的累积已投数量
                    }
                    current_data['products'].append(product_info)

        # 清理空的工序：移除那些所有小时产量都为0的工序
        for date_str, processes_data in list(schedule_data.items()):
            for process_key in list(processes_data.keys()):
                # 检查该工序的所有小时，如果产量都是0，则标记为可删除
                all_zero = all(
                    len(hour_data['products']) == 0 or 
                    all(product['quantity'] == 0 for product in hour_data['products'])
                    for hour_data in processes_data[process_key].values()
                )
                if all_zero:
                    del schedule_data[date_str][process_key]
            # 如果某个日期下没有任何有效的工序，也删除该日期
            if not schedule_data[date_str]:
                del schedule_data[date_str]
        
        return render_template('overall_production_schedule.html', 
                               schedule_data=schedule_data,
                               workshops=workshops,
                               processes=processes,
                               selected_workshop=selected_workshop_name,
                               user=user)

    @app.route('/add_equipment', methods=['POST'])
    @admin_required
    def add_equipment(user):
        """添加机台 - 仅管理员"""
        name = request.form.get('name')
        process_id = request.form.get('process_id')
        quantity = request.form.get('quantity')
        beat = request.form.get('beat')
        batch_size = request.form.get('batch_size', 1)  # 批次大小，默认为1
        
        # 计算每小时产能：3600秒/节拍*机台数量*每批次数量
        capacity_per_hour = (3600 / float(beat)) * int(quantity) * int(batch_size) if beat and quantity and batch_size else 0
        
        equipment = Equipment(
            name=name,
            process_id=process_id,
            quantity=int(quantity),
            beat=float(beat),
            batch_size=int(batch_size),
            capacity_per_hour=capacity_per_hour
        )
        
        db.session.add(equipment)
        db.session.commit()
        
        flash('机台添加成功！', 'success')
        return redirect(url_for('capacity_management'))

    @app.route('/add_process', methods=['POST'])
    @admin_required
    def add_process(user):
        """添加工序 - 仅管理员"""
        name = request.form.get('name')
        workshop_id = request.form.get('workshop_id')
        
        process = Process(
            name=name,
            workshop_id=workshop_id
        )
        
        db.session.add(process)
        db.session.commit()
        
        flash('工序添加成功！', 'success')
        return redirect(url_for('capacity_management'))

    @app.route('/update_equipment/<int:equipment_id>', methods=['POST'])
    @admin_required
    def update_equipment(equipment_id, user):
        """更新设备信息 - 仅管理员"""
        equipment = Equipment.query.get_or_404(equipment_id)
        equipment.name = request.form.get('name')
        equipment.quantity = int(request.form.get('quantity'))
        equipment.beat = float(request.form.get('beat'))
        equipment.batch_size = int(request.form.get('batch_size', 1))  # 更新批次大小
        
        # 重新计算每小时产能
        equipment.capacity_per_hour = (3600 / equipment.beat) * equipment.quantity * equipment.batch_size
        
        db.session.commit()
        flash('设备信息更新成功！', 'success')
        return redirect(url_for('capacity_management'))

    @app.route('/delete_equipment/<int:equipment_id>', methods=['POST'])
    @admin_required
    def delete_equipment(equipment_id, user):
        """删除设备 - 仅管理员"""
        equipment = Equipment.query.get_or_404(equipment_id)
        db.session.delete(equipment)
        db.session.commit()
        flash('设备删除成功！', 'success')
        return redirect(url_for('capacity_management'))

    @app.route('/generate_schedule', methods=['POST'])
    @admin_required
    def generate_schedule(user):
        """根据订单和产能信息生成排程计划（流水线式）- 仅管理员"""
        from collections import defaultdict
        
        # 获取所有订单
        orders = Order.query.all()
        
        # 清空现有排程 - 在获取订单数据后执行，避免潜在的锁问题
        db.session.execute(db.delete(ProductionSchedule))
        db.session.commit()
        
        
        # 定义标准工序流程顺序
        PROCESS_SEQUENCE = [
            '点胶', '切割', '边抛', '边强', '分片', '酸洗', '钢化', '面强', 'AOI', '包装'
        ]
        
        # 根据订单和产能信息生成排程
        for order in orders:
            product = order.product
            
            # 根据产品指定的车间名称找到对应的车间
            target_workshop = Workshop.query.filter_by(name=product.workshop).first()
            if not target_workshop:
                continue  # 如果找不到指定的车间，则跳过该订单
            
            # 获取该车间下的所有工序并按流程顺序排序
            all_processes = Process.query.filter_by(workshop_id=target_workshop.id).all()
            # 按预定义的流程顺序对工序进行排序
            sorted_processes = []
            for proc_name in PROCESS_SEQUENCE:
                for process in all_processes:
                    if process.name == proc_name:
                        sorted_processes.append(process)
                        break
            
            # 如果没有按标准流程定义的工序，则跳过
            if not sorted_processes:
                continue
                
            # 计算每个工序的产能
            process_capacities = {}
            for process in sorted_processes:
                # 获取该工序的设备
                equipments = Equipment.query.filter_by(process_id=process.id).all()
                
                if not equipments:
                    process_capacities[process.id] = 0
                    continue
                
                # 计算该工序的总产能（每小时）
                total_capacity_per_hour = sum(equip.capacity_per_hour for equip in equipments)
                
                if total_capacity_per_hour <= 0:
                    process_capacities[process.id] = 0
                    continue
                
                process_capacities[process.id] = total_capacity_per_hour
            
            # 开始时间（从当前时间开始）
            start_time = datetime.now()
            
            # 按小时模拟整个流水线的生产过程
            # 为每个时间点跟踪每个工序的待处理数量
            max_simulation_hours = int(product.calculated_quantity / min(
                [cap for cap in process_capacities.values() if cap > 0], 
                default=1
            )) + len(sorted_processes)  # 确保有足够的时间来完成所有工序
            
            # 模拟流水线生产，确保每个后续工序比前一个工序晚1小时开始
            current_time = start_time
            hour_counter = 0
            
            # 记录每个工序在每个时间点的累计产出
            process_output_by_time = {process.id: {} for process in sorted_processes}
            
            # 为每个工序维护当前待处理的数量
            process_remaining = {}
            for process in sorted_processes:
                if process.id in process_capacities:
                    process_remaining[process.id] = product.calculated_quantity
                else:
                    process_remaining[process.id] = 0
            
            # 为每个工序记录累计产出
            process_cumulative_output = {process.id: 0 for process in sorted_processes}
            
            # 记录每个工序的开始时间偏移（第一个工序偏移0小时，第二个偏移1小时，以此类推）
            process_start_offsets = {process.id: i for i, process in enumerate(sorted_processes)}
            
            while any(remaining > 0 for remaining in process_remaining.values()) and hour_counter < max_simulation_hours:
                # 按工序顺序处理（点胶 -> 切割 -> ... -> 包装）
                for idx, process in enumerate(sorted_processes):
                    if process.id not in process_capacities or process_capacities[process.id] <= 0:
                        continue
                    
                    # 检查当前时间是否已到达该工序的开始时间
                    start_offset = process_start_offsets[process.id]
                    if hour_counter < start_offset:
                        # 该工序尚未到开始时间
                        continue
                    
                    capacity_per_hour = process_capacities[process.id]
                    
                    # 第一个工序（点胶）直接处理，不受前序工序限制
                    if idx == 0:
                        # 第一个工序直接处理剩余的数量
                        production_this_hour = min(int(capacity_per_hour), process_remaining[process.id])
                    else:
                        # 对于后续工序，受前序工序的产出限制
                        prev_process = sorted_processes[idx - 1]
                        
                        # 当前工序可生产的数量 = min(产能, 剩余待处理数, 前序工序当前已产出但未被当前工序处理的数量)
                        prev_total_output = process_cumulative_output[prev_process.id]
                        current_total_output = process_cumulative_output[process.id]
                        
                        # 前序工序已经产出但当前工序还未处理的数量
                        available_to_process = max(0, prev_total_output - current_total_output)
                        
                        production_this_hour = min(
                            int(capacity_per_hour), 
                            process_remaining[process.id], 
                            available_to_process
                        )
                    
                    # 如果有可生产的数量，则创建排程记录
                    if production_this_hour > 0:
                        schedule = ProductionSchedule(
                            product_id=product.id,
                            process_id=process.id,
                            workshop_id=target_workshop.id,  # 使用产品指定的车间ID
                            schedule_date=current_time.date(),
                            hour=current_time.hour,
                            production_quantity=production_this_hour
                        )
                        
                        db.session.add(schedule)
                        
                        # 更新剩余数量和累计产出
                        process_remaining[process.id] -= production_this_hour
                        process_cumulative_output[process.id] += production_this_hour
                        
                        # 记录当前时间点的产出
                        time_key = f"{current_time.strftime('%Y-%m-%d')}_{current_time.hour:02d}"
                        if time_key not in process_output_by_time[process.id]:
                            process_output_by_time[process.id][time_key] = 0
                        process_output_by_time[process.id][time_key] += production_this_hour
                
                # 移动到下一个小时
                current_time += timedelta(hours=1)
                hour_counter += 1
        
        # 更新所有订单状态为已完成
        for order in orders:
            order.order_status = 'completed'
        
        db.session.commit()
        flash('排程计划生成成功！', 'success')
        return redirect(url_for('overall_production_schedule'))

    @app.route('/delete_schedule_by_date/<date>', methods=['POST'])
    @admin_required
    def delete_schedule_by_date(date, user):
        """根据日期删除排程 - 仅管理员"""
        from datetime import datetime
        try:
            # 将字符串转换为日期对象
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            # 删除指定日期的排程
            ProductionSchedule.query.filter(
                db.func.date(ProductionSchedule.schedule_date) == date_obj.date()
            ).delete()
            db.session.commit()
            flash(f'{date} 的排程数据已删除！', 'success')
        except Exception as e:
            flash('删除排程数据失败！', 'error')
        
        return redirect(url_for('overall_production_schedule'))

    @app.route('/delete_schedule_by_process', methods=['POST'])
    @admin_required
    def delete_schedule_by_process(user):
        """根据工序和日期删除排程 - 仅管理员"""
        from datetime import datetime
        date_str = request.form.get('date')
        process_id = request.form.get('process_id')
        workshop_id = request.form.get('workshop_id')
        
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            # 删除指定日期、工序和车间的排程
            ProductionSchedule.query.filter(
                db.func.date(ProductionSchedule.schedule_date) == date_obj.date(),
                ProductionSchedule.process_id == process_id,
                ProductionSchedule.workshop_id == workshop_id
            ).delete()
            db.session.commit()
            flash(f'{date_str} 的排程数据已删除！', 'success')
        except Exception as e:
            flash('删除排程数据失败！', 'error')
        
        return redirect(url_for('overall_production_schedule'))

    @app.route('/delete_all_schedules', methods=['POST'])
    @admin_required
    def delete_all_schedules(user):
        """删除所有排程 - 仅管理员，需要密码确认"""
        from werkzeug.security import check_password_hash
        
        password = request.form.get('password')
        
        # 验证密码
        if not password:
            flash('请输入管理员密码！', 'error')
            return redirect(url_for('overall_production_schedule'))
        
        # 获取当前登录用户（管理员）并验证密码
        current_user = User.query.get(user.id)
        if not check_password_hash(current_user.password, password):
            flash('密码错误！', 'error')
            return redirect(url_for('overall_production_schedule'))
        
        # 删除所有排程记录
        try:
            deleted_count = ProductionSchedule.query.delete()
            db.session.commit()
            flash(f'成功删除 {deleted_count} 条排程记录！', 'success')
        except Exception as e:
            db.session.rollback()
            flash('删除排程记录失败！', 'error')
        
        return redirect(url_for('overall_production_schedule'))

    # 其他路由函数可以在这里添加...


# 定义计算函数
def calculate_nesting_count(thickness_mm):
    """计算叠数：0.008×（叠数+1）+产品板厚（mm）×叠数+0.8 ≤ 1.3mm
    现在thickness_mm参数单位是毫米"""
    # 公式推导：
    # 0.008×(n+1) + thickness_mm×n + 0.8 ≤ 1.3
    # 0.008×n + 0.008 + thickness_mm×n + 0.8 ≤ 1.3
    # n×(0.008 + thickness_mm) + 0.808 ≤ 1.3
    # n×(0.008 + thickness_mm) ≤ 1.3 - 0.808
    # n ≤ (1.3 - 0.808) / (0.008 + thickness_mm)
    max_n = (1.3 - 0.808) / (0.008 + thickness_mm)
    return int(max_n) if max_n >= 1 else 1


def calculate_cutting_count(length, width, raw_glass_size):
    """计算切数：考虑点胶偏移单边4mm，产品长宽单边+2mm，原玻尺寸"""
    if not raw_glass_size or 'x' not in raw_glass_size:
        return 1  # 默认值
    
    try:
        raw_parts = raw_glass_size.split('x')
        if len(raw_parts) < 2:
            return 1
            
        # 解析原玻尺寸（单位是毫米mm）
        raw_x = float(raw_parts[0].strip())  # 单位已经是毫米
        raw_y = float(raw_parts[1].strip())  # 单位已经是毫米
        
        # 应用点胶偏移：单边4mm，所以每边减去4mm，总共长宽各减去8mm
        effective_x = raw_x - 8  # 有效长度 = 原玻长度 - 8mm
        effective_y = raw_y - 8  # 有效宽度 = 原玻宽度 - 8mm
        
        # 确保有效区域为正数
        if effective_x <= 0 or effective_y <= 0:
            return 1  # 如果有效区域为负或零，则返回默认值1
            
        # 计算实际需要的产品尺寸（产品长宽单边+2mm）
        actual_length = length + 2 * 2  # 长度单边+2mm，总共+4mm
        actual_width = width + 2 * 2    # 宽度单边+2mm，总共+4mm
        
        # 定义两个方向的产品尺寸
        orientation1 = (actual_length, actual_width)  # 原始方向
        orientation2 = (actual_width, actual_length)  # 旋转90度
        
        max_count = 1  # 默认值
        
        # 尝试不同的布局策略
        for prod_len, prod_wid in [orientation1, orientation2]:
            if prod_len <= effective_x and prod_wid <= effective_y:
                # 计算在给定方向下单个方向最多能放多少个产品
                count_along_x = int(effective_x // prod_len)
                count_along_y = int(effective_y // prod_wid)
                
                # 基础排列：全部按同一方向
                basic_count = count_along_x * count_along_y
                max_count = max(max_count, basic_count)
                
                # 尝试混合排列，利用剩余空间
                remaining_x = effective_x - (count_along_x * prod_len)
                remaining_y = effective_y - (count_along_y * prod_wid)
                
                # 在X方向剩余空间尝试放置旋转的产品
                if remaining_x >= prod_wid and prod_len <= effective_y:
                    additional_count_x = int(remaining_x // prod_wid) * count_along_y
                    max_count = max(max_count, basic_count + additional_count_x)
                
                # 在Y方向剩余空间尝试放置旋转的产品
                if remaining_y >= prod_len and prod_wid <= effective_x:
                    additional_count_y = int(remaining_y // prod_len) * count_along_x
                    max_count = max(max_count, basic_count + additional_count_y)
        
        return max(max_count, 1)
    except:
        return 1  # 如果解析失败，返回默认值

