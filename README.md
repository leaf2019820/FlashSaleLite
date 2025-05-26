# FlashSaleLite - 轻量级秒杀系统

## 一、项目介绍

FlashSaleLite 是一个基于 Python Flask 框架开发的轻量级秒杀系统，旨在提供一个简单易用、功能完整的秒杀解决方案。系统支持商品秒杀、库存管理、订单处理等核心功能，并实现了基本的用户权限管理。

### 主要特点：
- 支持秒杀活动的创建、管理和参与
- 使用 Redis 实现库存预减和请求队列
- 异步处理秒杀请求，提高系统并发能力
- 完整的用户权限管理（普通用户/管理员）
- 响应式界面设计，支持移动端访问

## 二、技术栈

### 1. 后端技术
- **Web框架：** Flask 2.0.1
- **数据库ORM：** SQLAlchemy 1.4.23
- **数据库：** MySQL 8.0+
- **缓存/队列：** Redis 3.5.3
- **用户认证：** Flask-Login 0.5.0
- **表单处理：** Flask-WTF 0.15.1
- **数据库迁移：** Flask-Migrate 3.1.0

### 2. 前端技术
- **模板引擎：** Jinja2
- **CSS框架：** Bootstrap 5
- **JavaScript：** jQuery
- **图表库：** Chart.js（用于数据可视化）

### 3. 开发工具
- **Python版本：** 3.7+
- **包管理：** pip
- **开发环境：** Windows 10
- **API测试：** Postman/Insomnia

## 三、部署流程

### 1. 环境准备
```bash
# 1. 安装 Python 3.7+
# 2. 安装 MySQL 8.0+
# 3. 安装 Redis
```

### 2. 项目配置
```bash
# 1. 克隆项目
git clone [项目地址]

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库连接信息等
```

### 3. 数据库初始化
```bash
# 1. 创建数据库
mysql -u root -p
CREATE DATABASE flashsale CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 2. 初始化数据库
flask db init
flask db migrate
flask db upgrade
```

### 4. 启动服务
```bash
# 1. 启动 Redis 服务
redis-server

# 2. 启动 Flask 应用
flask run
```

## 四、功能模块说明

### 1. 用户认证模块
- 用户注册、用户登录/登出、权限控制（普通用户/管理员）

### 2. 商品管理模块
- 商品列表展示、商品详情查看、商品库存管理

### 3. 秒杀活动模块
- 秒杀活动创建、活动列表展示、秒杀参与功能、库存预减处理

### 4. 订单处理模块
- 订单创建、订单状态管理、订单查询

### 5. 后台管理模块
- 商品管理、活动管理、订单管理、用户管理

## 五、接口说明

详细接口文档请查看[接口说明文档](./接口说明.md)

## 六、系统截图

系统主要界面的截图，包括：
1. 首页展示

   ![1748092020289](C:\Users\25932\AppData\Roaming\Typora\typora-user-images\1748092020289.png)

2. 秒杀活动列表

   ![1748092151051](C:\Users\25932\AppData\Roaming\Typora\typora-user-images\1748092151051.png)

   ![1748092164661](C:\Users\25932\AppData\Roaming\Typora\typora-user-images\1748092164661.png)

3. 商品详情页

   ![1748092052817](C:\Users\25932\AppData\Roaming\Typora\typora-user-images\1748092052817.png)

   ![1748092183528](C:\Users\25932\AppData\Roaming\Typora\typora-user-images\1748092183528.png)

4. 订单管理界面

   ![1748092064410](C:\Users\25932\AppData\Roaming\Typora\typora-user-images\1748092064410.png)

5. 后台管理界面]

   ![1748092074041](C:\Users\25932\AppData\Roaming\Typora\typora-user-images\1748092074041.png)

   6.用户管理图

   ![1748092111550](C:\Users\25932\AppData\Roaming\Typora\typora-user-images\1748092111550.png)

   7.我的订单

   ![1748092205314](C:\Users\25932\AppData\Roaming\Typora\typora-user-images\1748092205314.png)

   8.我的地址

   ![1748092235291](C:\Users\25932\AppData\Roaming\Typora\typora-user-images\1748092235291.png)

## 八、常见问题

1. **Q: 如何处理高并发？**
   A: 系统使用 Redis 预减库存和请求队列，配合异步处理机制处理高并发请求。

2. **Q: 如何保证数据一致性？**
   A: 使用 Redis 和 MySQL 双重校验，确保库存数据的准确性。

3. **Q: 系统支持哪些支付方式？**
   A: 目前支持模拟支付，可根据需求扩展接入实际支付接口。

## 九、更新日志

### v1.0.0 (2025-05-24)
- 初始版本发布
- 实现基础秒杀功能
- 完成用户认证系统
- 添加后台管理功能

## 十、联系方式

- 项目维护者：小小若溪
- 个人主页：https://rxstore24.cc/

  



