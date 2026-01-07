# MySQL数据库配置指南

本项目已配置为支持MySQL数据库，但默认在开发环境中使用SQLite。按照以下步骤将数据库切换到MySQL。

## 默认配置说明

- **开发环境**：默认使用SQLite数据库（无需额外配置）
- **生产环境**：默认使用MySQL数据库（需要配置环境变量）

## 开发环境：使用SQLite（默认）

如果只是开发测试，无需任何配置即可运行：

```bash
python init_db.py
python app.py
```

## 开发环境：切换到MySQL

如果你希望在开发环境中也使用MySQL，请按以下步骤操作：

### 步骤1：创建MySQL数据库和用户

首先，你需要在MySQL中创建一个专用的数据库和用户：

```sql
-- 使用root或具有管理员权限的账户登录MySQL
mysql -u root -p

-- 创建数据库
CREATE DATABASE tokenplan CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建专用用户（请将 'your_password' 替换为安全密码）
CREATE USER 'tokenplan_user'@'localhost' IDENTIFIED BY 'your_password';

-- 授予该用户对tokenplan数据库的所有权限
GRANT ALL PRIVILEGES ON tokenplan.* TO 'tokenplan_user'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;

-- 退出MySQL
EXIT;
```

或者，如果你需要允许应用从其他主机连接，请使用：
```sql
CREATE USER 'tokenplan_user'@'%' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON tokenplan.* TO 'tokenplan_user'@'%';
FLUSH PRIVILEGES;
```

### 步骤2：配置环境变量

复制 `.env.example` 文件并命名为 `.env`，然后根据你的MySQL配置修改以下变量：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```bash
# MySQL Database Configuration (当设置这些变量时，开发环境也会使用MySQL)
MYSQL_HOST=localhost
MYSQL_USER=tokenplan_user
MYSQL_PASSWORD=your_password
MYSQL_DB=tokenplan
MYSQL_PORT=3306

# Application Configuration
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
```

## 生产环境：使用MySQL

在生产环境中，应用会自动使用MySQL，但需要设置DATABASE_URL：

```bash
# 在服务器上设置环境变量
export FLASK_ENV=production
export DATABASE_URL="mysql+pymysql://tokenplan_user:your_password@localhost/tokenplan"
```

## 安装依赖

确保安装了所有依赖项：

```bash
pip install -r requirements.txt
```

**注意：** 如果遇到MySQL认证问题，请确保安装了cryptography包：

```bash
pip install cryptography
```

## 初始化数据库

运行初始化脚本来创建表结构和初始数据：

```bash
python init_db.py
```

## 使用Flask-Migrate管理数据库迁移

如果你有数据库迁移需求，可以使用Flask-Migrate：

```bash
# 初始化迁移环境（仅首次）
flask db init

# 创建迁移脚本
flask db migrate -m "Initial migration"

# 应用迁移
flask db upgrade
```

## 验证连接

启动应用以验证数据库连接：

```bash
python app.py
```

## 故障排除

如果遇到连接问题，请检查：

1. MySQL服务是否正在运行
2. 数据库用户和密码是否正确
3. 数据库是否已创建
4. 防火墙是否阻止了MySQL端口（默认3306）
5. 如果遇到 `RuntimeError: 'cryptography' package is required for sha256_password or caching_sha2_password auth methods` 错误，需要安装 `cryptography` 包：
   ```bash
   pip install cryptography
   ```
6. 如果遇到 `Access denied for user` 错误，请检查：
   - 用户名和密码是否正确
   - 用户是否具有对tokenplan数据库的访问权限
   - MySQL服务是否允许从localhost连接
7. 在开发环境中，如果要使用MySQL，请确保设置了MYSQL_HOST等环境变量
8. 在生产环境中，如果要使用MySQL，请确保设置了FLASK_ENV=production和DATABASE_URL