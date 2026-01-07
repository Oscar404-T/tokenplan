import os
from app import app, db
from app.models import Workshop, Process, User, UserRole
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        # 为数据库创建所有表（兼容SQLite和MySQL）
        db.create_all()
        
        # 检查是否已有车间数据，避免重复添加
        if Workshop.query.count() == 0:
            # 添加车间
            workshops_data = [
                {'name': 'UTG1车间'},
                {'name': 'UTG2车间'},
                {'name': 'UTG3车间'},
                {'name': '中试线'}
            ]
            
            for workshop_data in workshops_data:
                workshop = Workshop(name=workshop_data['name'])
                db.session.add(workshop)
            
            db.session.commit()
            print("车间数据添加成功！")
        
        # 检查是否已有工序数据，避免重复添加
        if Process.query.count() == 0:
            # 获取所有车间
            workshops = Workshop.query.all()
            
            # 定义所有工序
            processes_data = [
                {'name': '点胶'},
                {'name': '切割'},
                {'name': '边抛'},
                {'name': '边强'},
                {'name': '分片'},
                {'name': '酸洗'},
                {'name': '钢化'},
                {'name': '面强'},
                {'name': 'AOI'},
                {'name': '包装'}
            ]
            
            # 为每个车间添加所有工序
            for workshop in workshops:
                for process_data in processes_data:
                    process = Process(name=process_data['name'], workshop_id=workshop.id)
                    db.session.add(process)
            
            db.session.commit()
            print("工序数据添加成功！")
        
        # 检查是否已有用户数据，避免重复添加
        if User.query.count() == 0:
            # 添加管理员用户
            admin_user = User(
                username='admin',
                password=generate_password_hash('admin'),  # 修改密码为admin
                role=UserRole.ADMIN
            )
            
            # 添加普通用户
            regular_user = User(
                username='0210042432',
                password=generate_password_hash('Cao99063010'),  # 密码哈希
                role=UserRole.USER
            )
            
            db.session.add(admin_user)
            db.session.add(regular_user)
            db.session.commit()
            print("用户数据添加成功！")
        
        print("数据库表创建成功！")

if __name__ == '__main__':
    init_db()