import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

# 创建数据库实例
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    # 获取项目根目录路径
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 创建Flask应用实例，显式设置模板和静态文件夹路径
    app = Flask(__name__, 
                template_folder=os.path.join(project_dir, 'app', 'templates'), 
                static_folder=os.path.join(project_dir, 'app', 'static'))

    # 加载配置
    app.config.from_object(Config)

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)

    # 导入模型（在db初始化之后）
    from app import models

    # 确保模型只初始化一次
    global _models_initialized
    if not _models_initialized:
        models.init_models(db)
        _models_initialized = True

    # 导入控制器（在app和db都准备好之后）
    from app import controllers
    controllers.register_routes(app, db)
    
    return app

# 全局标志：防止模型被重复初始化
_models_initialized = False

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)