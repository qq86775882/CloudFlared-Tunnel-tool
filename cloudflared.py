#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Python版本的CloudFlared Tunnel设置工具
# 使用方法: python cloudflared.py
# 兼容Python 3.5+

import os
import sys
import time
import ctypes
import subprocess
import platform
import shutil
import urllib.request
import re
from pathlib import Path
import stat

# 检测Python版本
python_version = sys.version_info
if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 5):
    print("错误: 需要Python 3.5或更高版本")
    sys.exit(1)

# 在Linux系统上检查root权限
if platform.system() != 'Windows':
    if os.geteuid() != 0:
        print("\033[31m错误: 此脚本需要root权限运行\033[0m")
        print("\033[33m请使用以下命令重新运行:\033[0m")
        print("\033[32msudo python3 " + sys.argv[0] + "\033[0m")
        sys.exit(1)

# 颜色常量定义
class Colors:
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    RESET = '\033[0m'

def print_color(message, color=Colors.WHITE):
    """打印彩色文本"""
    try:
        print(f"{color}{message}{Colors.RESET}")
    except:
        print(message)

# 检查f-string支持
try:
    test_fstring = f"test"
except SyntaxError:
    # 如果不支持f-string (Python 3.5及以下)，重写print_color函数
    def print_color(message, color=Colors.WHITE):
        """打印彩色文本(兼容Python 3.5)"""
        try:
            print(color + message + Colors.RESET)
        except:
            print(message)

def download_file(url, output_path):
    """下载文件到指定路径"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response, open(output_path, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        return True
    except Exception as e:
        print_color("下载失败: " + str(e), Colors.RED)
        return False

def is_admin():
    """检查是否有管理员权限"""
    try:
        if platform.system() == 'Windows':
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            # Linux系统下，脚本开头已经检查了root权限，所以这里直接返回True
            return True
    except:
        return False

def get_service_status_windows(service_name):
    """获取Windows服务状态"""
    try:
        result = subprocess.run(['sc', 'query', service_name], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               universal_newlines=True, 
                               check=False)
        if "RUNNING" in result.stdout:
            return "RUNNING"
        elif "STOPPED" in result.stdout:
            return "STOPPED"
        else:
            return "NOT FOUND"
    except Exception as e:
        print_color("获取服务状态失败: " + str(e), Colors.RED)
        return "UNKNOWN"

def get_service_status_linux(service_name):
    """获取Linux服务状态"""
    try:
        result = subprocess.run(['systemctl', 'status', service_name], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               universal_newlines=True, 
                               check=False)
        if "active (running)" in result.stdout:
            return "RUNNING"
        elif "inactive (dead)" in result.stdout or "loaded" in result.stdout:
            return "STOPPED"
        else:
            return "NOT FOUND"
    except Exception as e:
        print_color("获取服务状态失败: " + str(e), Colors.RED)
        return "UNKNOWN"

def get_service_status(service_name):
    """获取服务状态"""
    if platform.system() == 'Windows':
        return get_service_status_windows(service_name)
    else:
        return get_service_status_linux(service_name)

def service_exists(service_name):
    """检查服务是否存在"""
    status = get_service_status(service_name)
    return status != "NOT FOUND"

def create_service_windows(service_name, bin_path):
    """创建Windows服务"""
    try:
        subprocess.run(['sc', 'create', service_name, 'binPath=', bin_path, 'start=', 'auto'], 
                      check=True)
        return True
    except Exception as e:
        print_color(f"创建服务失败: {str(e)}", Colors.RED)
        return False

def create_service_linux(service_name, bin_path, local_addr, log_path):
    """创建Linux systemd服务"""
    try:
        # 在Linux环境下默认使用root用户运行服务
        user = "root"
        group = "root"
        
        # 获取日志文件的绝对路径
        log_path_abs = os.path.abspath(log_path)
        log_dir = os.path.dirname(log_path_abs)
        
        # 创建服务单元文件
        service_content = f"""[Unit]
Description=Cloudflare Tunnel
After=network.target

[Service]
Type=simple
ExecStart={bin_path} tunnel --url {local_addr} --logfile {log_path_abs} --no-autoupdate
Restart=always
RestartSec=5
User={user}
Group={group}
WorkingDirectory={log_dir}
StandardOutput=append:{log_path_abs}
StandardError=append:{log_path_abs}

[Install]
WantedBy=multi-user.target
"""
        service_path = f"/etc/systemd/system/{service_name}.service"
        
        with open(service_path, 'w') as f:
            f.write(service_content)
        
        print_color(f"systemd服务单元创建完成: {service_path}", Colors.GREEN)
        print_color(f"服务将以 {user}:{group} 身份运行", Colors.CYAN)
        print_color(f"日志文件绝对路径: {log_path_abs}", Colors.CYAN)
        print_color(f"工作目录: {log_dir}", Colors.CYAN)
        
        # 确保日志文件和目录的权限正确
        try:
            # 设置日志目录权限
            os.makedirs(log_dir, exist_ok=True)
            os.system(f"chmod 755 {log_dir}")
            
            # 创建并设置日志文件权限
            with open(log_path_abs, 'a') as f:
                f.write(f"# Service log initialized at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            os.system(f"chmod 644 {log_path_abs}")
            print_color(f"日志文件和目录权限已设置", Colors.GREEN)
        except Exception as e:
            print_color(f"设置日志权限时出错: {str(e)}", Colors.YELLOW)
        
        # 重新加载systemd
        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        return True
    except Exception as e:
        print_color(f"创建服务失败: {str(e)}", Colors.RED)
        return False

def create_service(service_name, bin_path, local_addr=None, log_path=None):
    """创建服务"""
    if platform.system() == 'Windows':
        return create_service_windows(service_name, bin_path)
    else:
        return create_service_linux(service_name, bin_path, local_addr, log_path)

def delete_service_windows(service_name):
    """删除Windows服务"""
    try:
        subprocess.run(['sc', 'delete', service_name], check=True)
        return True
    except Exception as e:
        print_color(f"删除服务失败: {str(e)}", Colors.RED)
        return False

def delete_service_linux(service_name):
    """删除Linux服务"""
    try:
        subprocess.run(['systemctl', 'disable', f"{service_name}.service"], check=True)
        service_path = f"/etc/systemd/system/{service_name}.service"
        if os.path.exists(service_path):
            os.remove(service_path)
        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        return True
    except Exception as e:
        print_color(f"删除服务失败: {str(e)}", Colors.RED)
        return False

def delete_service(service_name):
    """删除服务"""
    if platform.system() == 'Windows':
        return delete_service_windows(service_name)
    else:
        return delete_service_linux(service_name)

def start_service_windows(service_name):
    """启动Windows服务"""
    try:
        subprocess.run(['sc', 'start', service_name], check=True)
        return True
    except Exception as e:
        print_color(f"启动服务失败: {str(e)}", Colors.RED)
        return False

def start_service_linux(service_name):
    """启动Linux服务"""
    try:
        subprocess.run(['systemctl', 'start', f"{service_name}.service"], check=True)
        return True
    except Exception as e:
        print_color("启动服务失败: " + str(e), Colors.RED)
        return False

def get_tunnel_url_from_output(cloudflared_bin, local_addr, timeout=15):
    """直接从临时运行的输出中获取隧道URL"""
    try:
        # 创建一个临时运行的cloudflared进程来获取URL
        print_color("尝试通过临时运行获取公网域名...", Colors.YELLOW)
        process = subprocess.Popen(
            [cloudflared_bin, 'tunnel', '--url', local_addr, '--no-autoupdate'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # 等待最多timeout秒来获取域名
        domain = None
        start_time = time.time()
        print_color(f"等待域名生成，最多等待{timeout}秒...", Colors.CYAN)
        
        while time.time() - start_time < timeout:
            # 检查进程是否还在运行
            if process.poll() is not None:
                print_color("进程意外退出", Colors.RED)
                break
                
            # 尝试读取输出（非阻塞）
            try:
                # 检查是否有数据可读
                import select
                reads, _, _ = select.select([process.stdout, process.stderr], [], [], 0.5)
                
                for stream in reads:
                    line = stream.readline()
                    if not line:
                        continue
                        
                    # 检查输出中是否包含域名
                    if 'https://' in line and 'trycloudflare.com' in line:
                        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                        if match:
                            domain = match.group(0)
                            print_color(f"发现域名: {domain}", Colors.GREEN)
                            break
                
                # 如果找到了域名，退出循环
                if domain:
                    break
            except Exception as e:
                print_color(f"读取输出时出错: {str(e)}", Colors.RED)
            
            # 每5秒显示一次进度
            elapsed = int(time.time() - start_time)
            if elapsed > 0 and elapsed % 5 == 0:
                print_color(f"已等待 {elapsed} 秒...", Colors.CYAN)
        
        # 检查是否超时
        if time.time() - start_time >= timeout and not domain:
            print_color(f"等待超时（{timeout}秒），未能获取域名", Colors.RED)
        
        # 无论是否找到域名，都终止进程
        print_color("终止临时进程...", Colors.YELLOW)
        try:
            process.terminate()
            # 给进程一点时间来终止
            try:
                process.wait(timeout=2)
            except:
                # 如果进程没有在2秒内终止，强制终止
                process.kill()
                print_color("已强制终止进程", Colors.RED)
        except Exception as e:
            print_color(f"终止进程时出错: {str(e)}", Colors.RED)
            
        return domain
    except Exception as e:
        print_color("获取域名时发生错误: " + str(e), Colors.RED)
        return None

def get_tunnel_url_from_journalctl(service_name, max_attempts=2):
    """从systemd日志中获取隧道URL"""
    try:
        print_color("尝试从systemd日志中获取URL...", Colors.YELLOW)
        
        # 多次尝试，因为服务可能刚刚启动，日志可能还没有完全写入
        for attempt in range(max_attempts):
            if attempt > 0:
                print_color(f"第 {attempt+1} 次尝试...", Colors.CYAN)
                # 等待日志写入
                time.sleep(3)
                
            # 从journalctl中获取日志输出
            try:
                result = subprocess.run(
                    ['journalctl', '-u', f"{service_name}.service", '-n', '100', '--no-pager'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    timeout=5  # 添加超时防止命令卡住
                )
                
                # 检查命令是否成功
                if result.returncode != 0:
                    print_color(f"获取日志失败，返回码: {result.returncode}", Colors.RED)
                    if result.stderr:
                        print_color(f"错误: {result.stderr}", Colors.RED)
                    continue
                
                # 检查输出中是否包含域名
                output = result.stdout
                
                if 'trycloudflare.com' in output:
                    match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', output)
                    if match:
                        url = match.group(0)
                        print_color(f"从systemd日志中找到URL: {url}", Colors.GREEN)
                        return url
                    else:
                        print_color("日志中包含trycloudflare.com但无法提取完整URL", Colors.YELLOW)
                else:
                    print_color("日志中未找到trycloudflare.com", Colors.YELLOW)
            except subprocess.TimeoutExpired:
                print_color("获取日志命令超时", Colors.RED)
            except Exception as e:
                print_color(f"获取日志时出错: {str(e)}", Colors.RED)
        
        print_color("无法从systemd日志中获取URL", Colors.RED)
        return None
    except Exception as e:
        print_color("从journalctl获取域名失败: " + str(e), Colors.RED)
        return None

def start_service(service_name):
    """启动服务"""
    if platform.system() == 'Windows':
        return start_service_windows(service_name)
    else:
        return start_service_linux(service_name)

def stop_service_windows(service_name):
    """停止Windows服务"""
    try:
        subprocess.run(['sc', 'stop', service_name], check=True)
        return True
    except Exception as e:
        print_color(f"停止服务失败: {str(e)}", Colors.RED)
        return False

def stop_service_linux(service_name):
    """停止Linux服务"""
    try:
        subprocess.run(['systemctl', 'stop', f"{service_name}.service"], check=True)
        return True
    except Exception as e:
        print_color(f"停止服务失败: {str(e)}", Colors.RED)
        return False

def stop_service(service_name):
    """停止服务"""
    if platform.system() == 'Windows':
        return stop_service_windows(service_name)
    else:
        return stop_service_linux(service_name)

def set_executable_permission(file_path):
    """为文件设置执行权限并验证权限设置成功"""
    if platform.system() != 'Windows':
        try:
            print_color(f"为 {file_path} 设置执行权限...", Colors.YELLOW)
            # 检查当前权限
            current_permissions = os.stat(file_path).st_mode
            print_color(f"当前权限: {oct(current_permissions)}", Colors.CYAN)
            
            # 使用chmod系统调用设置权限
            os.chmod(file_path, current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            
            # 也使用shell命令增加一层保障
            os.system(f"chmod +x {file_path}")
            
            # 验证权限是否正确设置
            new_permissions = os.stat(file_path).st_mode
            print_color(f"新权限: {oct(new_permissions)}", Colors.CYAN)
            
            # 验证是否有执行权限
            if new_permissions & stat.S_IXUSR:
                print_color("执行权限设置成功", Colors.GREEN)
                return True
            else:
                print_color("警告: 执行权限可能未正确设置，尝试强制设置权限", Colors.YELLOW)
                try:
                    # 强制设置777权限作为备用
                    os.system(f"chmod 755 {file_path}")
                    if os.stat(file_path).st_mode & stat.S_IXUSR:
                        print_color("执行权限强制设置成功", Colors.GREEN)
                        return True
                    else:
                        raise Exception("无法设置执行权限")
                except Exception as e:
                    print_color(f"无法强制设置权限: {str(e)}", Colors.RED)
                    return False
        except Exception as e:
            print_color(f"设置执行权限时出错: {str(e)}", Colors.RED)
            print_color("请手动运行: chmod +x " + file_path, Colors.YELLOW)
            return False
    return True

def main():
    print_color("====== CloudFlared Tunnel 设置工具 ======", Colors.CYAN)
    print_color("初始化中...", Colors.YELLOW)
    
    # 检测系统类型
    system = platform.system()
    print_color(f"检测到操作系统: {system}", Colors.GREEN)
    
    # 获取当前工作目录
    current_dir = os.getcwd()
    
    # 设置变量
    if system == 'Windows':
        cloudflared_url = "https://github.com/cloudflare/cloudflared/releases/download/2024.12.2/cloudflared-windows-amd64.exe"
        install_dir = os.path.join(os.environ.get('ProgramData', 'C:\\ProgramData'), 'cloudflared')
        cloudflared_bin = os.path.join(install_dir, "cloudflared.exe")
        log_path = os.path.join(install_dir, "cloudflared.log")
    else:  # Linux
        # Linux下已确保使用root权限运行
        print_color("已确认拥有root权限", Colors.GREEN)
        
        arch = platform.machine()
        if arch == 'x86_64' or arch == 'amd64':
            cloudflared_url = "https://github.com/cloudflare/cloudflared/releases/download/2024.12.2/cloudflared-linux-amd64"
        elif arch == 'aarch64' or arch == 'arm64':
            cloudflared_url = "https://github.com/cloudflare/cloudflared/releases/download/2024.12.2/cloudflared-linux-arm64"
        else:
            print_color(f"不支持的架构: {arch}", Colors.RED)
            sys.exit(1)
        
        install_dir = "/usr/local/bin"
        cloudflared_bin = os.path.join(install_dir, "cloudflared")
        
        # 在Linux环境下默认使用当前目录存放日志
        log_path = os.path.join(current_dir, "cloudflared.log")
        print_color("将使用当前目录保存日志文件", Colors.CYAN)
    
    service_name = "cloudflared"
    
    print_color(f"检测到Python版本: {platform.python_version()}", Colors.GREEN)
    print_color(f"日志文件路径: {log_path}", Colors.CYAN)
    
    # Linux环境下提供日志路径选择
    if system != 'Windows':
        print_color("\n选择日志文件保存位置:", Colors.YELLOW)
        print("1) 当前目录 (默认): " + log_path)
        print("2) 用户主目录: ~/.cloudflared/cloudflared.log")
        print("3) 系统日志目录: /var/log/cloudflared.log")
        
        log_choice = input("请选择 (直接回车使用当前目录): ")
        
        if log_choice == "2":
            home_dir = os.path.expanduser("~")
            log_dir = os.path.join(home_dir, ".cloudflared")
            if not os.path.exists(log_dir):
                try:
                    os.makedirs(log_dir, exist_ok=True)
                except Exception as e:
                    print_color("无法创建日志目录: " + str(e), Colors.RED)
            log_path = os.path.join(log_dir, "cloudflared.log")
            print_color("日志将保存到: " + log_path, Colors.CYAN)
        elif log_choice == "3":
            log_path = "/var/log/cloudflared.log"
            print_color("日志将保存到: " + log_path, Colors.CYAN)
        else:
            # 默认使用当前目录
            print_color("将使用当前目录: " + log_path, Colors.CYAN)
    
    # 创建安装目录
    try:
        if not os.path.exists(install_dir) and system == 'Windows':
            os.makedirs(install_dir, exist_ok=True)
            print_color(f"创建安装目录: {install_dir}", Colors.GREEN)
    except Exception as e:
        print_color(f"无法创建安装目录，可能需要管理员/root权限", Colors.RED)
        print_color(f"错误: {str(e)}", Colors.RED)
        sys.exit(1)
    
    # 检查cloudflared是否存在
    print_color("\n检查cloudflared...", Colors.YELLOW)
    if os.path.exists(cloudflared_bin):
        print_color(f"cloudflared已存在: {cloudflared_bin}", Colors.GREEN)
        
        try:
            file_size = os.path.getsize(cloudflared_bin) / (1024 * 1024)
            print_color(f"文件大小: {file_size:.2f} MB", Colors.CYAN)
            
            # 即使文件已存在，也确保它有执行权限（Linux）
            if system != 'Windows':
                # 检查是否有执行权限
                if not os.access(cloudflared_bin, os.X_OK):
                    print_color("现有的cloudflared文件没有执行权限，正在设置...", Colors.YELLOW)
                    set_executable_permission(cloudflared_bin)
                else:
                    print_color("cloudflared已有执行权限", Colors.GREEN)
        except Exception as e:
            print_color(f"检查文件时出错: {str(e)}", Colors.RED)
    else:
        print_color("开始下载cloudflared...", Colors.CYAN)
        print_color(f"下载URL: {cloudflared_url}", Colors.WHITE)
        print_color(f"保存位置: {cloudflared_bin}", Colors.WHITE)
        
        download_success = download_file(cloudflared_url, cloudflared_bin)
        
        if download_success:
            print_color("下载完成！", Colors.GREEN)
            try:
                # 为Linux系统设置可执行权限
                if system != 'Windows':
                    set_executable_permission(cloudflared_bin)
                
                file_size = os.path.getsize(cloudflared_bin) / (1024 * 1024)
                print_color(f"文件大小: {file_size:.2f} MB", Colors.CYAN)
            except Exception as e:
                print_color(f"设置权限错误: {str(e)}", Colors.RED)
        else:
            print_color("下载失败，请检查网络连接或手动下载", Colors.RED)
            print_color(f"手动下载URL: {cloudflared_url}", Colors.YELLOW)
            sys.exit(1)
    
    # 如果在Linux上，确保二进制文件可以执行
    if system != 'Windows':
        print_color("\n验证cloudflared是否可执行...", Colors.YELLOW)
        if os.access(cloudflared_bin, os.X_OK):
            print_color("cloudflared已有执行权限", Colors.GREEN)
        else:
            print_color("警告: cloudflared没有执行权限，尝试设置...", Colors.RED)
            if not set_executable_permission(cloudflared_bin):
                print_color("错误: 无法设置执行权限，请手动执行:", Colors.RED)
                print_color(f"chmod +x {cloudflared_bin}", Colors.WHITE)
                if input("是否继续? (y/n): ").lower() not in ['y', 'yes']:
                    sys.exit(1)
    
    # 检查现有服务
    print_color("\n检查现有服务...", Colors.YELLOW)
    try:
        if service_exists(service_name):
            service_status = get_service_status(service_name)
            print_color(f"检测到现有cloudflared服务: {service_name}", Colors.YELLOW)
            print_color(f"服务状态: {service_status}", Colors.CYAN)
            
            uninstall = ""
            while uninstall.lower() not in ['y', 'yes', 'n', 'no']:
                uninstall = input("是否要卸载旧服务？(y/n): ")
            
            if uninstall.lower() in ['y', 'yes']:
                print_color("卸载旧服务...", Colors.CYAN)
                try:
                    stop_service(service_name)
                    time.sleep(2)
                    
                    delete_service(service_name)
                    
                    if os.path.exists(log_path):
                        os.remove(log_path)
                    
                    print_color("服务卸载完成", Colors.GREEN)
                except Exception as e:
                    print_color(f"卸载服务错误: {str(e)}", Colors.RED)
            else:
                print_color("保留现有服务，仅更新运行地址", Colors.YELLOW)
    except Exception as e:
        print_color(f"检查服务错误: {str(e)}", Colors.RED)
    
    # 选择运行模式
    print_color("\n请选择运行模式:", Colors.YELLOW)
    print("1) 临时运行 (前台运行并显示trycloudflare域名)")
    print("2) 后台运行 (注册为系统服务)")
    
    mode = ""
    while mode not in ['1', '2']:
        mode = input("请输入1或2: ")
    
    local_addr = ""
    while not local_addr:
        local_addr = input("请输入本地服务地址 (例如: 127.0.0.1:8080): ")
    
    if mode == "1":
        print_color("\n以临时模式运行cloudflared...", Colors.CYAN)
        print_color("启动cloudflared进程...", Colors.YELLOW)
        print_color(f"本地服务地址: {local_addr}", Colors.GREEN)
        
        try:
            print_color("直接运行cloudflared，输出到控制台...", Colors.YELLOW)
            print_color("按Ctrl+C停止隧道", Colors.YELLOW)
            
            subprocess.run([cloudflared_bin, 'tunnel', '--url', local_addr])
            
        except Exception as e:
            print_color(f"启动进程错误: {str(e)}", Colors.RED)
    
    elif mode == "2":
        print_color("\n注册为系统服务并在后台运行...", Colors.CYAN)
        
        if system == 'Windows' and not is_admin():
            print_color("警告: 创建系统服务需要管理员权限", Colors.YELLOW)
            print_color("如果失败，请以管理员身份运行此脚本", Colors.YELLOW)
        
        try:
            if system == 'Windows':
                service_command = f'"{cloudflared_bin}" tunnel --url {local_addr} --logfile "{log_path}"'
                success = create_service(service_name, service_command)
            else:
                # 确保日志目录存在
                log_dir = os.path.dirname(log_path)
                if not os.path.exists(log_dir):
                    try:
                        os.makedirs(log_dir, exist_ok=True)
                        print_color(f"创建日志目录: {log_dir}", Colors.GREEN)
                    except Exception as e:
                        print_color(f"创建日志目录失败: {str(e)}", Colors.RED)
                        # 如果无法创建目录，使用临时目录
                        log_path = "/tmp/cloudflared.log"
                        print_color(f"改用临时日志路径: {log_path}", Colors.YELLOW)
                
                # 确保日志文件有权限写入
                try:
                    with open(log_path, 'a') as f:
                        f.write(f"# Log initialized at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    print_color(f"日志文件初始化成功: {log_path}", Colors.GREEN)
                    
                    # 设置权限确保服务可以写入
                    try:
                        os.chmod(log_path, 0o666)
                        print_color("已设置日志文件权限", Colors.GREEN)
                    except Exception as e:
                        print_color(f"设置日志权限失败: {str(e)}", Colors.YELLOW)
                        
                except Exception as e:
                    print_color(f"创建日志文件失败: {str(e)}", Colors.RED)
                    log_path = "/tmp/cloudflared.log"
                    try:
                        with open(log_path, 'a') as f:
                            f.write(f"# Log initialized at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        os.chmod(log_path, 0o666)
                        print_color(f"改用临时日志路径: {log_path}", Colors.YELLOW)
                    except Exception as e2:
                        print_color(f"创建临时日志文件也失败: {str(e2)}", Colors.RED)
                
                # 在创建服务前，先获取一个URL作为备用
                print_color("为确保能获取公网URL，可以先临时运行以获取域名...", Colors.CYAN)
                backup_domain = None
                
                get_backup = input("是否临时运行以获取域名? (y/n, 默认n): ")
                if get_backup.lower() in ['y', 'yes']:
                    print_color("尝试获取临时域名...", Colors.CYAN)
                    backup_domain = get_tunnel_url_from_output(cloudflared_bin, local_addr)
                    if backup_domain:
                        print_color(f"已获取临时域名（备用）: {backup_domain}", Colors.GREEN)
                    else:
                        print_color("未能获取临时域名，将继续创建服务", Colors.YELLOW)
                else:
                    print_color("跳过临时域名获取，直接创建服务", Colors.YELLOW)
                
                print_color(f"创建systemd服务，日志输出到: {log_path}", Colors.CYAN)
                success = create_service(service_name, cloudflared_bin, local_addr, log_path)
            
            if success:
                print_color("服务创建成功", Colors.GREEN)
            else:
                print_color("服务创建可能失败", Colors.YELLOW)
            
            time.sleep(2)
            
            print_color("启动服务...", Colors.YELLOW)
            if start_service(service_name):
                print_color("服务启动成功，等待日志输出...", Colors.GREEN)
            
                domain = None
                # 首先尝试从日志文件获取域名
                for i in range(15):
                    time.sleep(1)
                    
                    if os.path.exists(log_path):
                        try:
                            with open(log_path, 'r', errors='ignore') as f:
                                log_content = f.read()
                            
                            # 调试日志文件内容
                            if i == 0 or i == 14:  # 第一次和最后一次检查时显示日志内容
                                log_size = os.path.getsize(log_path)
                                print_color(f"日志文件大小: {log_size} 字节", Colors.CYAN)
                                if log_size > 0:
                                    print_color("日志文件内容(前200字符):", Colors.CYAN)
                                    print(log_content[:200] + "..." if len(log_content) > 200 else log_content)
                            
                            match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', log_content)
                            if match:
                                domain = match.group(0)
                                print_color("\n=== 服务运行成功 ===", Colors.GREEN)
                                print_color("公共访问URL: " + domain, Colors.GREEN)
                                print_color("本地服务地址: " + local_addr, Colors.CYAN)
                                print_color("日志文件位置: " + log_path, Colors.WHITE)
                                break
                        except Exception as e:
                            print_color("读取日志文件失败: " + str(e), Colors.YELLOW)
                    
                    if i % 3 == 0:
                        print(".", end="", flush=True)
                
                # 如果从日志文件找不到域名，尝试从journalctl获取(仅限Linux)
                if not domain and system != 'Windows':
                    print_color("\n从日志文件无法获取域名，尝试从systemd日志中获取...", Colors.YELLOW)
                    domain = get_tunnel_url_from_journalctl(service_name)
                    if domain:
                        print_color("\n=== 服务运行成功 ===", Colors.GREEN)
                        print_color("公共访问URL: " + domain, Colors.GREEN)
                        print_color("本地服务地址: " + local_addr, Colors.CYAN)
                        print_color("日志文件位置: " + log_path, Colors.WHITE)
                
                # 如果仍然没有找到域名，尝试临时运行一个实例来获取域名
                if not domain:
                    print_color("\n从服务日志无法获取域名，尝试临时运行来获取...", Colors.YELLOW)
                    domain = get_tunnel_url_from_output(cloudflared_bin, local_addr)
                    if domain:
                        print_color("\n=== 获取域名成功 ===", Colors.GREEN)
                        print_color("公共访问URL: " + domain, Colors.GREEN)
                        print_color("本地服务地址: " + local_addr, Colors.CYAN)
                        print_color("日志文件位置: " + log_path, Colors.WHITE)
                        print_color("注意: 此地址应与后台服务使用的地址相同", Colors.YELLOW)
                
                # 如果所有方法都失败，但有备用域名，则使用备用域名
                if not domain and backup_domain:
                    domain = backup_domain
                    print_color("\n=== 使用预先获取的备用域名 ===", Colors.GREEN)
                    print_color("公共访问URL: " + domain, Colors.GREEN)
                    print_color("本地服务地址: " + local_addr, Colors.CYAN)
                    print_color("日志文件位置: " + log_path, Colors.WHITE)
                    print_color("注意: 此地址与服务可能使用的地址相同，但无法保证", Colors.YELLOW)
                
                if not domain:
                    print_color("\n未能获取公共访问URL，可能的原因:", Colors.RED)
                    print_color("1. 服务启动失败", Colors.YELLOW)
                    print_color("2. 网络连接问题", Colors.YELLOW)
                    print_color("3. 日志输出格式变更", Colors.YELLOW)
                    
                    # 检查服务状态
                    try:
                        service_status = get_service_status(service_name)
                        print_color(f"\n当前服务状态: {service_status}", Colors.CYAN)
                        
                        # 如果服务正在运行，尝试输出更多诊断信息
                        if service_status == "RUNNING" and system != "Windows":
                            print_color("\n获取服务详细信息...", Colors.CYAN)
                            try:
                                # 使用systemctl status获取更详细的信息
                                status_result = subprocess.run(
                                    ['systemctl', 'status', service_name],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    universal_newlines=True,
                                    timeout=5  # 添加超时
                                )
                                if status_result.returncode == 0:
                                    print_color("服务状态详情:", Colors.CYAN)
                                    print(status_result.stdout)
                                else:
                                    print_color("无法获取详细服务状态", Colors.RED)
                            except Exception as e:
                                print_color(f"获取详细状态失败: {str(e)}", Colors.RED)
                            
                            try:    
                                print_color("\n验证cloudflared进程:", Colors.CYAN)
                                subprocess.run(["ps", "-ef", "|", "grep", "cloudflared"], shell=True)
                            except Exception as e:
                                print_color(f"获取进程信息失败: {str(e)}", Colors.RED)
                    except Exception as e:
                        print_color(f"无法获取服务状态: {str(e)}", Colors.RED)
                        
                    print_color("\n建议尝试:", Colors.CYAN)
                    print_color("- 检查服务状态: sudo systemctl status " + service_name, Colors.WHITE)
                    print_color("- 查看服务日志: sudo journalctl -u " + service_name + " -f", Colors.WHITE)
                    print_color("- 临时运行模式: " + cloudflared_bin + " tunnel --url " + local_addr, Colors.WHITE)
                    
                print_color("\n服务管理命令:", Colors.YELLOW)
                if system == 'Windows':
                    print_color("停止服务: sc stop " + service_name, Colors.WHITE)
                    print_color("启动服务: sc start " + service_name, Colors.WHITE)
                    print_color("删除服务: sc delete " + service_name, Colors.WHITE)
                else:
                    print_color("停止服务: sudo systemctl stop " + service_name, Colors.WHITE)
                    print_color("启动服务: sudo systemctl start " + service_name, Colors.WHITE)
                    print_color("重启服务: sudo systemctl restart " + service_name, Colors.WHITE)
                    print_color("删除服务: sudo systemctl disable " + service_name + " && sudo rm /etc/systemd/system/" + service_name + ".service", Colors.WHITE)
                    print_color("\n查看实时日志: sudo journalctl -u " + service_name + " -f", Colors.WHITE)
                    print_color("查看域名: sudo journalctl -u " + service_name + " | grep trycloudflare.com", Colors.WHITE)
                    print_color("查看服务配置: sudo cat /etc/systemd/system/" + service_name + ".service", Colors.WHITE)
            else:
                print_color("服务启动失败", Colors.RED)
                print_color("请使用以下命令检查错误:", Colors.CYAN)
                if system != 'Windows':
                    print_color("- sudo journalctl -u " + service_name + " -e", Colors.WHITE)
                    print_color("- sudo systemctl status " + service_name, Colors.WHITE)
            
        except Exception as e:
            print_color("创建或启动服务失败", Colors.RED)
            print_color(f"错误: {str(e)}", Colors.RED)
            print_color("请确保您有root/管理员权限", Colors.YELLOW)
            
            try:
                delete_service(service_name)
            except Exception:
                pass
    
    print_color("\n脚本执行完成", Colors.GREEN)

if __name__ == "__main__":
    main()
