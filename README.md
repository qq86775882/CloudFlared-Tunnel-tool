# CloudFlared Tunnel 设置工具

这是一个用 Python 编写的 CloudFlared Tunnel 设置工具，用于快速配置和管理 Cloudflare Tunnel 服务。该工具提供了简单的命令行界面，可以帮助用户下载 cloudflared 可执行文件、设置临时隧道或将其注册为系统服务。

## 功能特点

- 自动下载最新版本的 cloudflared 可执行文件
- 支持两种运行模式：临时运行和系统服务
- 自动检测并显示 trycloudflare 域名
- 彩色输出，提升用户体验
- 完整的服务管理功能（创建、启动、停止、删除）
- 详细的错误处理和状态报告

## 系统要求

- Windows 操作系统
- Python 3.6+
- 管理员权限（用于创建系统服务）

## 安装与使用

1. 下载cloudflared.py文件
2. 打开命令提示符或 PowerShell
3. 运行以下命令：

```bash
python cloudflared.py
```

## 使用指南

运行脚本后，按照以下步骤操作：

1.如果检测到已存在的 cloudflared 服务，脚本会询问是否卸载
2. 选择运行模式：
   - 选项 1：临时运行（前台运行并显示 trycloudflare 域名）
   - 选项 2：后台运行（注册为系统服务）
3. 输入本地服务地址（例如：127.0.0.1:8080）
4. 脚本将执行所选操作并显示结果

### 临时运行模式

在临时运行模式下，cloudflared 将在前台运行，并直接在控制台显示输出。这种模式适合测试或临时使用。按 Ctrl+C 可以停止隧道。

### 系统服务模式

在系统服务模式下，cloudflared 将被注册为 Windows 系统服务并在后台运行。脚本会自动启动服务并尝试从日志中获取公共访问 URL。服务创建后，即使用户注销也能继续运行。

## 服务管理命令

创建服务后，可以使用以下命令管理服务：

- 停止服务：`sc stop CloudflaredTunnel`
- 启动服务：`sc start CloudflaredTunnel`
- 删除服务：`sc delete CloudflaredTunnel`

## 日志文件

服务运行时的日志保存在以下位置：

```
C:\ProgramData\cloudflared\cloudflared.log
```

## 注意事项

- 创建系统服务需要管理员权限
-如果服务创建失败，请以管理员身份运行脚本
- 公共访问 URL 可能需要一些时间才能出现在日志中

## 故障排除

1. **下载失败**：检查网络连接或手动下载 cloudflared 可执行文件，或到 https://gitee.com/xiaochaoge2009/main/releases/tag/cloudflared    下载     https://github.com/cloudflare/cloudflared/releases     也可以下载到最新版
2. **服务创建失败**：确保以管理员身份运行脚本
3. **未检测到访问域名**：查看日志文件，服务可能需要更多时间建立连接

