# README

## 项目简介

2024 秋冬 BS 课程大作业 

---

本项目旨在开发一个功能完善的商品比价网站以及 APP，为用户提供便捷、高效的商品价格比较服务。

网站将整合多个主流电商平台（如淘宝、京东等）的商品数据，用户可以通过商品名称、关键词搜索等方式，快速获取目标商品在不同平台上的实时价格信息，并进行直观的价格比较。

同时，本项目还能帮助用户抓住每一次价格变动。用户不仅能查看还能订阅特定商品的价格变动，当商品价格下降时，系统会通过邮件等方式及时通知用户，帮助用户抓住最佳购买时机。

此外，启真智选还引入了 AI 智能分析功能，通过调用 LLM 接口，为用户提供个性化的商品推荐和比价分析，帮助用户做出更明智的购物决策。

***

项目已经部署在公网服务器上，部署地址：

- 前端：[启真智选](http://101.34.242.157:20001/#/)
- 后端：[101.34.242.157:8000](http://101.34.242.157:8000/)

## 项目结构

- `frontend/` 前端代码目录
- `backend/` 后端代码目录

## 部署方式

需要宿主机为 linux 并且具有 docker, mysql 环境，并且打开 `:20001` （前端）和 `:8000` （后端） 端口的防火墙端口。最好还要有通畅的网络，能连上 docker 和 playwright 的下载网站。

### 前端部署

需要将 `frontend/src/utils.ts` 中的 `prefix` 改为您部署的后端的地址，例如：

```ts
const prefix: string = "http://101.34.242.157:8000";
```

然后运行

```shell
cd frontend
docker compose up -d --build
```

即可部署完成。

### 后端部署

编辑后端的配置文件 `backend/config.toml` 

修改 `database.database_url` 为宿主机的 mysql url，修改 `cors.allow_origins` 为您部署的前端地址，其他部分可以不用修改，例如：

```toml
[email]
sender_email = "******@163.com"
sender_password = "******"
smtp_server = "smtp.163.com"
smtp_port = 465

[cors] 
allow_origins = ['http://localhost:5173', 'http://localhost:20001', 'http://101.34.242.157:20001']

[jwt]
secret_key = 'secret_key'

[database]
database_url = 'mysql+aiomysql://root:root@localhost:3307/bs'

[openai]
api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

## 项目亮点

- **使用流式响应，及时呈现获取到的数据**
- **使用 JWT Cookie 实现登录鉴权**
- 使用 playwright 自动化爬取网站信息
- **AI 赋能**
- 密码加密
- **响应式 UI**
- docker 自动化打包
- 历史价格图表
- 邮件通知
- 历史价格模糊搜索

