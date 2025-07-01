# CloudFlared Tunnel 设置工具

这是一个跨平台的CloudFlare Tunnel设置工具，支持Windows和Linux系统，可以帮助您快速创建和管理CloudFlare Tunnel服务，将本地服务通过安全隧道暴露到公网。

## 功能特点

- 支持Windows和Linux系统
- 自动下载适合您系统的cloudflared二进制文件
- 支持临时运行模式和系统服务模式
- 自动检测并显示生成的trycloudflare.com域名
- 完整的服务管理功能（安装、启动、停止、卸载）
- 兼容Python 3.5+及更高版本
- 多种方式获取公网URL，提高成功率
- 灵活的日志文件存储选项
- 改进的超时处理和错误恢复机制
- 可选择跳过临时域名获取步骤，加快服务设置

## 系统要求

- Python 3.5+（推荐使用Python 3.6+）
- Windows 10+（需要管理员权限） 或 Linux（必须使用root权限）
- 网络连接（用于下载cloudflared）

### 重要提示

- 在**Windows**系统上，建议以管理员权限运行以创建系统服务
- 在**Linux**系统上，**必须**使用root权限运行脚本（sudo），否则脚本将无法运行

## 安装位置

脚本会自动下载cloudflared二进制文件并安装到以下位置：

- **Windows系统**: `C:\ProgramData\cloudflared\cloudflared.exe`
- **Linux系统**: `/usr/local/bin/cloudflared`

如果您已经手动安装了cloudflared，只要将其放在上述相应的位置，脚本将直接使用而不重复下载。

## 使用方法

### 1. 下载脚本

```bash
# 克隆仓库或者直接下载cloudflared.py文件
git clone https://github.com/qq86775882/CloudFlared-Tunnel-tool.git
```bash
git clone https://gitee.com/xiaochaoge2009/CloudFlared-Tunnel-tool.git

```

### 2. 运行脚本

#### Windows系统:

```bash
# 普通运行
python cloudflared.py

# 管理员权限运行（推荐，尤其是创建系统服务时）
# 右键点击PowerShell或CMD，选择"以管理员身份运行"
# 然后执行:
python cloudflared.py
```

#### Linux系统:

```bash
# Linux系统必须使用root权限运行
sudo python3 cloudflared.py

# 如果没有使用root权限，脚本会提示并退出
```
## 好玩的

配合netlify，可以永久性指向。大致思路：先在github上新建个项目，放一个txt文件（名字随意）和一个index.html，使用github的api接口，在服务启动获取到公网ip后，更新txt文件。 在netlify上托管这个项目，获得一个公网地址；然后index.html文件中随便写点代码，大致内容为打开时访问netlify上的公网地址+txt文件名，获取到baseurl，然后在当前页打开这个url   netlify官网为：https://app.netlify.com/，    详细可以查看我的另一个项目：         https://github.com/qq86775882/ceshi
### 3. 配置选项

运行脚本后，您需要进行以下配置：

1. **选择日志保存位置** (仅Linux):
   - 选项1: 当前目录 (默认)
   - 选项2: 用户主目录 (`~/.cloudflared/cloudflared.log`)
   - 选项3: 系统日志目录 (`/var/log/cloudflared.log`)

2. **选择运行模式**:
   - 选项1: 临时运行（前台运行，直接在控制台显示输出）
   - 选项2: 后台运行（安装为系统服务，开机自启）

3. **输入本地服务地址**:
   - 格式: `IP:端口` 例如 `127.0.0.1:8080`
   - 这是您希望通过隧道暴露的本地服务地址

4. **临时域名获取选项** (仅后台运行模式):
   - 您可以选择是否在创建服务前先临时运行以获取域名
   - 选择"n"可以跳过这一步，加快服务设置过程
   - 选择"y"会先临时运行cloudflared获取域名作为备用，但可能需要等待几秒钟

### 4. 管理服务

#### Windows系统:

```powershell
# 启动服务
sc start cloudflared

# 停止服务
sc stop cloudflared

# 删除服务
sc delete cloudflared
```

#### Linux系统:

```bash
# 启动服务
sudo systemctl start cloudflared

# 停止服务
sudo systemctl stop cloudflared

# 查看服务状态
sudo systemctl status cloudflared

# 查看服务日志
sudo journalctl -u cloudflared -f

# 查看服务生成的公网URL
sudo journalctl -u cloudflared | grep trycloudflare.com

# 删除服务
sudo systemctl disable cloudflared && sudo rm /etc/systemd/system/cloudflared.service
```

## 工作原理

1. 脚本会根据您的系统自动下载对应版本的cloudflared二进制文件
2. 在临时模式下，cloudflared会直接在前台运行并显示生成的域名
3. 在服务模式下，脚本会:
   - Windows: 创建名为"cloudflared"的Windows服务
   - Linux: 创建systemd服务单元文件并启用
4. 服务启动后会生成一个随机的*.trycloudflare.com域名供访问
5. 所有访问该域名的请求会安全地转发到您指定的本地服务
6. 在Linux系统上，服务以root用户运行，确保具有足够权限

## 改进的超时和错误处理机制

最新版本增加了以下改进：

1. **可选的临时域名获取**:
   - 在创建服务前，您可以选择是否需要先临时运行以获取域名
   - 适合网络环境不稳定或需要快速部署的场景

2. **超时处理**:
   - 临时运行时有最大等待时间限制（默认15秒）
   - 使用非阻塞方式读取输出，避免程序卡住
   - 多种方法尝试获取域名，降低失败率

3. **更详细的诊断信息**:
   - 服务启动后会显示更详细的状态信息
   - 当无法获取域名时提供更多故障排除指引

## 文件位置

### 二进制文件位置
- **Windows**: `C:\ProgramData\cloudflared\cloudflared.exe`
- **Linux**: `/usr/local/bin/cloudflared`

### 日志文件位置
- **Windows**: `C:\ProgramData\cloudflared\cloudflared.log`
- **Linux** (可选择以下位置):
  - 当前目录 (默认): `./cloudflared.log`
  - 用户主目录: `~/.cloudflared/cloudflared.log`
  - 系统日志目录: `/var/log/cloudflared.log`
  - 无法写入时的备选路径: `/tmp/cloudflared.log`

### 服务配置文件
- **Windows**: 注册为系统服务，无配置文件
- **Linux**: `/etc/systemd/system/cloudflared.service`

## 获取隧道URL的方法

脚本使用以下多种方式尝试获取隧道的公网URL:

1. **从日志文件中提取**
   - 这是默认方法，会检查配置的日志文件中是否包含URL

2. **从systemd日志中提取** (仅Linux)
   - 如果日志文件中没有找到URL，会尝试从systemd的journalctl日志中获取
   - 新版本会多次尝试并有超时保护

3. **临时运行实例获取**
   - 如果以上方法都失败，会临时运行一个cloudflared实例来获取URL
   - 新版本增加了超时保护，避免长时间等待
   - 获取后会自动终止临时实例

4. **手动查看日志**
   - 如果所有自动方法都失败，可以手动运行以下命令查看URL:
   ```bash
   sudo journalctl -u cloudflared | grep trycloudflare.com
   ```
   - 或者直接查看当前目录下的日志文件:
   ```bash
   cat ./cloudflared.log | grep trycloudflare.com
   ```

## 常见问题

1. **无法安装服务**
   - 确保您在Linux系统上使用了root权限（sudo）
   - Windows系统上需要管理员权限

2. **下载失败**
   - 检查网络连接
   - 可能需要配置代理
   - 可以手动下载cloudflared并放在指定位置

3. **未显示域名**
   - 检查当前目录下的`cloudflared.log`文件: `cat ./cloudflared.log | grep trycloudflare.com`
   - 在Linux系统下运行: `sudo journalctl -u cloudflared | grep trycloudflare.com`
   - 确保本地服务地址正确且服务正在运行
   - 尝试临时模式运行: `/usr/local/bin/cloudflared tunnel --url 127.0.0.1:8080`

4. **服务启动失败**
   - 检查日志文件获取详细错误信息: `sudo journalctl -u cloudflared -f`
   - 验证本地服务是否正常运行
   - 确保没有端口冲突
   - 确认cloudflared二进制文件有执行权限

5. **日志文件没有内容**
   - 使用当前目录作为日志路径(默认选项)
   - 查看systemd服务日志: `sudo journalctl -u cloudflared -f`

6. **临时运行时卡住不动**
   - 如果在获取临时域名时程序卡住，可以按Ctrl+C中断
   - 在后台运行模式中，选择"n"跳过临时域名获取步骤
   - 可以直接使用临时模式运行查看域名

## 安全提示

- 通过此工具生成的域名可以被任何人访问
- 建议为您的本地服务配置适当的认证机制
- 这是一个临时隧道，如需长期稳定的隧道，请考虑使用CloudFlare官方的命名隧道

## 许可证

MIT

