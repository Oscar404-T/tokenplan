# tokenplan

tokenplan 是一个基于 Flask 的轻量级 Web 应用，旨在实现订单管理、产能规划与整体生产排程的可视化和管理功能。目标用户为制造业或生产型企业的生产计划与运营管理人员，用于解决生产订单信息分散、排产不透明、产能调配不清晰等问题，提升生产管理效率。

## 项目结构

```
tokenplan/
├── app/                    # Flask应用主目录
│   ├── __init__.py         # 应用工厂和初始化
│   ├── controllers.py      # 控制器和路由定义
│   ├── models.py           # 数据模型定义
│   ├── static/             # 静态资源（CSS, JS）
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── main.js
│   └── templates/          # HTML模板文件
│       ├── base.html
│       ├── capacity_management.html
│       ├── create_order.html
│       ├── edit_order.html
│       ├── index.html
│       ├── login.html
│       ├── order_management.html
│       ├── overall_production_schedule.html
│       └── view_order.html
├── migrations/             # 数据库迁移文件
├── app.py                  # 应用启动文件
├── config.py               # 应用配置
├── init_db.py              # 数据库初始化脚本
├── start_app.py            # 启动脚本（带环境变量）
├── requirements.txt        # 项目依赖
├── .env / .env.example     # 环境变量配置
└── README.md               # 项目说明
```

## 技术栈

- 后端框架: Flask v2.3.3
- ORM 工具: Flask-SQLAlchemy v3.0.5
- 数据库迁移: Flask-Migrate v4.0.5
- 数据库驱动: PyMySQL v1.1.0（用于连接 MySQL）
- 请求处理: Werkzeug v2.3.7
- 前端技术: HTML + CSS + JavaScript

## 安装与运行

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 配置数据库：
   - 复制 `.env.example` 为 `.env`
   - 根据需要修改数据库连接参数

3. 初始化数据库：
   ```bash
   python init_db.py
   ```

4. 启动应用：
   ```bash
   python start_app.py
   # 或者
   python app.py
   ```

## 功能模块

- 订单管理：创建、编辑、查看生产订单
- 产能管理：监控和配置生产能力
- 生产排程：展示整体生产计划时间表
- 用户认证：登录验证和权限管理

## 环境配置

项目支持通过环境变量配置数据库连接，优先使用 MySQL，开发环境可选择使用 SQLite。

## 数据库设计

使用 MySQL 数据库，包含以下主要表：
- users: 用户信息
- products: 产品信息
- workshops: 车间信息
- processes: 工序信息
- equipments: 设备信息
- orders: 订单信息
- production_schedules: 生产排程信息