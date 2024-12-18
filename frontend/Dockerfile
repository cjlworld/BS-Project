# 使用 Node.js 20-alpine 镜像作为基础镜像
FROM node:20-alpine AS build

# 设置工作目录
WORKDIR /app/

# 安装 pnpm
RUN npm install -g pnpm

# 更换 npm 源为淘宝源（或其他国内源）
RUN npm config set registry https://registry.npmmirror.com

# 添加 上下文（宿主机）的 所有文件到 build 容器的 /app 目录
COPY . .

# 使用 pnpm 安装依赖并构建 前端 应用
RUN pnpm install && pnpm run build

# 删除不必要的文件和目录
RUN rm -rf /app/node_modules 

# 使用 Nginx 镜像来托管 React 应用
FROM nginx:alpine

# 复制 build 容器的 构建好的 前端 应用到 Nginx 默认的静态文件目录
COPY --from=build /app/dist /usr/share/nginx/html

# 复制 上下文中 自定义的 Nginx 配置文件
COPY nginx_front.conf /etc/nginx/conf.d/default.conf

# 暴露端口号
EXPOSE 20001

# 启动 Nginx 服务器
CMD ["nginx", "-g", "daemon off;"]