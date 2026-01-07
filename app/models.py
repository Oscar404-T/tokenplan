from datetime import datetime
from enum import Enum

# db实例将在应用初始化后被设置
db = None


def init_models(app_db):
    """初始化模型，设置db实例"""
    global db
    db = app_db
    
    # 定义UserRole枚举
    global UserRole
    class UserRole(Enum):
        ADMIN = 'admin'
        USER = 'user'

    # 定义User模型
    global User
    class User(db.Model):
        """用户模型"""
        __tablename__ = 'users'
        
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True, nullable=False)
        password = db.Column(db.String(200), nullable=False)  # 存储哈希后的密码
        role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.USER)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        
        def __repr__(self):
            return f'<User {self.username}>'

    # 定义Product模型
    global Product
    class Product(db.Model):
        """产品模型"""
        __tablename__ = 'products'
        
        id = db.Column(db.Integer, primary_key=True)
        product_model = db.Column(db.String(100), nullable=False)  # 产品型号
        length = db.Column(db.Float, nullable=False)  # 长度(mm)
        width = db.Column(db.Float, nullable=False)  # 宽度(mm)
        thickness = db.Column(db.Float, nullable=False)  # 厚度(mm)
        shipping_quantity = db.Column(db.Integer, nullable=False)  # 出货数量
        yield_rate = db.Column(db.Float, nullable=False)  # 预估良率
        shipping_date = db.Column(db.DateTime, nullable=False)  # 出货日期
        raw_glass_size = db.Column(db.String(100), nullable=False)  # 原玻尺寸
        workshop = db.Column(db.String(100), nullable=False)  # 生产车间
        calculated_quantity = db.Column(db.Integer, nullable=False)  # 投产数量
        nesting_count = db.Column(db.Integer, nullable=False)  # 叠数
        cutting_count = db.Column(db.Integer, nullable=False)  # 切数
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        def __repr__(self):
            return f'<Product {self.product_model}>'

    # 定义Workshop模型
    global Workshop
    class Workshop(db.Model):
        """车间模型"""
        __tablename__ = 'workshops'
        
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False)  # 车间名称
        
        def __repr__(self):
            return f'<Workshop {self.name}>'

    # 定义Process模型
    global Process
    class Process(db.Model):
        """工序模型"""
        __tablename__ = 'processes'
        
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False)  # 工序名称
        workshop_id = db.Column(db.Integer, db.ForeignKey('workshops.id'), nullable=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        
        # 关联车间
        workshop = db.relationship('Workshop', backref=db.backref('processes', lazy=True))
        
        def __repr__(self):
            return f'<Process {self.name}>'

    # 定义Equipment模型
    global Equipment
    class Equipment(db.Model):
        """机台模型"""
        __tablename__ = 'equipments'
        
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False)  # 机台名称
        process_id = db.Column(db.Integer, db.ForeignKey('processes.id'), nullable=False)
        quantity = db.Column(db.Integer, nullable=False, default=1)  # 机台数量
        beat = db.Column(db.Float, nullable=False)  # 节拍（秒/批次）
        batch_size = db.Column(db.Integer, nullable=False, default=1)  # 每批次数量
        capacity_per_hour = db.Column(db.Float)  # 每小时产能，由节拍、数量和批次计算得出
        
        # 关联工序
        process = db.relationship('Process', backref=db.backref('equipments', lazy=True))
        
        def __repr__(self):
            return f'<Equipment {self.name}>'

    # 定义Order模型
    global Order
    class Order(db.Model):
        """订单模型"""
        __tablename__ = 'orders'
        
        id = db.Column(db.Integer, primary_key=True)
        order_number = db.Column(db.String(100), nullable=False, unique=True)  # 订单号
        product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
        customer_name = db.Column(db.String(200))  # 客户名称
        order_status = db.Column(db.String(50), default='pending')  # 订单状态
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        # 关联产品
        product = db.relationship('Product', backref=db.backref('orders', lazy=True))
        
        def __repr__(self):
            return f'<Order {self.order_number}>'

    # 定义ProductionSchedule模型
    global ProductionSchedule
    class ProductionSchedule(db.Model):
        """排产计划模型"""
        __tablename__ = 'production_schedules'
        
        id = db.Column(db.Integer, primary_key=True)
        product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
        process_id = db.Column(db.Integer, db.ForeignKey('processes.id'), nullable=False)
        workshop_id = db.Column(db.Integer, db.ForeignKey('workshops.id'), nullable=False)
        schedule_date = db.Column(db.DateTime, nullable=False)  # 排产日期
        hour = db.Column(db.Integer, nullable=False)  # 小时（0-23）
        production_quantity = db.Column(db.Integer, nullable=False, default=0)  # 该小时生产数量
        
        # 关联关系
        product = db.relationship('Product', backref=db.backref('schedules', lazy=True))
        process = db.relationship('Process', backref=db.backref('schedules', lazy=True))
        workshop = db.relationship('Workshop', backref=db.backref('schedules', lazy=True))
        
        def __repr__(self):
            return f'<Schedule {self.product_id} on {self.schedule_date} at hour {self.hour}>'

    # 将类设置为模块的属性
    globals()['UserRole'] = UserRole
    globals()['User'] = User
    globals()['Product'] = Product
    globals()['Workshop'] = Workshop
    globals()['Process'] = Process
    globals()['Equipment'] = Equipment
    globals()['Order'] = Order
    globals()['ProductionSchedule'] = ProductionSchedule
