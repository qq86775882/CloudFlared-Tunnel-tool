#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Python版本的CloudFlared Tunnel设置工具
# 使用方法: python cloudflared.py

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
        print_color(f"下载失败: {str(e)}", Colors.RED)
        return False

def is_admin():
    """检查是否有管理员权限"""
    try:
        if platform.system() == 'Windows':
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except:
        return False

def get_service_status(service_name):
    """获取Windows服务状态"""
    try:
        result = subprocess.run(['sc', 'query', service_name], 
                               capture_output=True, 
                               text=True, 
                               check=False)
        if "RUNNING" in result.stdout:
            return "RUNNING"
        elif "STOPPED" in result.stdout:
            return "STOPPED"
        else:
            return "NOT FOUND"
    except Exception as e:
        print_color(f"获取服务状态失败: {str(e)}", Colors.RED)
        return "UNKNOWN"

def service_exists(service_name):
    """检查服务是否存在"""
    status = get_service_status(service_name)
    return status != "NOT FOUND"

def create_service(service_name, bin_path):
    """创建Windows服务"""
    try:
        subprocess.run(['sc', 'create', service_name, 'binPath=', bin_path, 'start=', 'auto'], 
                      check=True)
        return True
    except Exception as e:
        print_color(f"创建服务失败: {str(e)}", Colors.RED)
        return False

def delete_service(service_name):
    """删除Windows服务"""
    try:
        subprocess.run(['sc', 'delete', service_name], check=True)
        return True
    except Exception as e:
        print_color(f"删除服务失败: {str(e)}", Colors.RED)
        return False

def start_service(service_name):
    """启动Windows服务"""
    try:
        subprocess.run(['sc', 'start', service_name], check=True)
        return True
    except Exception as e:
        print_color(f"启动服务失败: {str(e)}", Colors.RED)
        return False

def stop_service(service_name):
    """停止Windows服务"""
    try:
        subprocess.run(['sc', 'stop', service_name], check=True)
        return True
    except Exception as e:
        print_color(f"停止服务失败: {str(e)}", Colors.RED)
        return False

def main():
    print_color("====== CloudFlared Tunnel 设置工具 ======", Colors.CYAN)
    print_color("初始化中...", Colors.YELLOW)
    
    # 设置变量
    cloudflared_url = "https://github.com/cloudflare/cloudflared/releases/download/2024.12.2/cloudflared-windows-amd64.exe"
    install_dir = os.path.join(os.environ.get('ProgramData', 'C:\\ProgramData'), 'cloudflared')
    cloudflared_bin = os.path.join(install_dir, "cloudflared.exe")
    log_path = os.path.join(install_dir, "cloudflared.log")
    service_name = "CloudflaredTunnel"
    
    print_color(f"检测到Python版本: {platform.python_version()}", Colors.GREEN)
    
    # 创建安装目录
    try:
        if not os.path.exists(install_dir):
            os.makedirs(install_dir, exist_ok=True)
            print_color(f"创建安装目录: {install_dir}", Colors.GREEN)
    except Exception as e:
        print_color(f"无法创建安装目录，可能需要管理员权限", Colors.RED)
        print_color(f"错误: {str(e)}", Colors.RED)
        sys.exit(1)
    
    # 检查cloudflared是否存在
    print_color("\n检查cloudflared...", Colors.YELLOW)
    if os.path.exists(cloudflared_bin):
        print_color(f"cloudflared.exe已存在: {cloudflared_bin}", Colors.GREEN)
        
        try:
            file_size = os.path.getsize(cloudflared_bin) / (1024 * 1024)
            print_color(f"文件大小: {file_size:.2f} MB", Colors.CYAN)
        except Exception:
            pass
    else:
        print_color("开始下载cloudflared...", Colors.CYAN)
        print_color(f"下载URL: {cloudflared_url}", Colors.WHITE)
        print_color(f"保存位置: {cloudflared_bin}", Colors.WHITE)
        
        download_success = download_file(cloudflared_url, cloudflared_bin)
        
        if download_success:
            print_color("下载完成！", Colors.GREEN)
            try:
                file_size = os.path.getsize(cloudflared_bin) / (1024 * 1024)
                print_color(f"文件大小: {file_size:.2f} MB", Colors.CYAN)
            except Exception:
                pass
        else:
            print_color("下载失败，请检查网络连接或手动下载", Colors.RED)
            print_color(f"手动下载URL: {cloudflared_url}", Colors.YELLOW)
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
        
        if not is_admin():
            print_color("警告: 创建系统服务可能需要管理员权限", Colors.YELLOW)
            print_color("如果失败，请以管理员身份运行此脚本", Colors.YELLOW)
        
        try:
            service_command = f'"{cloudflared_bin}" tunnel --url {local_addr} --logfile "{log_path}"'
            
            if create_service(service_name, service_command):
                print_color("服务创建成功", Colors.GREEN)
            else:
                print_color("服务创建可能失败", Colors.YELLOW)
            
            time.sleep(2)
            
            print_color("启动服务...", Colors.YELLOW)
            if start_service(service_name):
                print_color("服务启动成功，等待日志输出...", Colors.GREEN)
            
                domain = None
                for i in range(30):
                    time.sleep(1)
                    
                    if os.path.exists(log_path):
                        try:
                            with open(log_path, 'r', errors='ignore') as f:
                                log_content = f.read()
                            
                            match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', log_content)
                            if match:
                                domain = match.group(0)
                                print_color("\n=== 服务运行成功 ===", Colors.GREEN)
                                print_color(f"公共访问URL: {domain}", Colors.GREEN)
                                print_color(f"本地服务地址: {local_addr}", Colors.CYAN)
                                print_color(f"日志文件位置: {log_path}", Colors.WHITE)
                                break
                        except Exception:
                            pass
                    
                    if i % 3 == 0:
                        print(".", end="", flush=True)
                
                print("")
                
                if not domain:
                    print_color(f"未检测到访问域名，请手动检查日志: {log_path}", Colors.YELLOW)
                    print_color("服务可能需要更多时间建立连接", Colors.CYAN)
                    
                    try:
                        service_status = get_service_status(service_name)
                        print_color(f"服务状态: {service_status}", Colors.CYAN)
                    except Exception:
                        print_color("无法获取服务状态", Colors.RED)
                
                print_color("\n服务管理命令:", Colors.YELLOW)
                print_color(f"停止服务: sc stop {service_name}", Colors.WHITE)
                print_color(f"启动服务: sc start {service_name}", Colors.WHITE)
                print_color(f"删除服务: sc delete {service_name}", Colors.WHITE)
            
        except Exception as e:
            print_color("创建或启动服务失败", Colors.RED)
            print_color(f"错误: {str(e)}", Colors.RED)
            print_color("请确保您有管理员权限", Colors.YELLOW)
            
            try:
                delete_service(service_name)
            except Exception:
                pass
    
    print_color("\n脚本执行完成", Colors.GREEN)

if __name__ == "__main__":
    main()
