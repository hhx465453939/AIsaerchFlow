#!/usr/bin/env python3
"""
AI多平台搜索聚合器 - 启动脚本
增强版启动器 - 包含实时搜索功能和浏览器自动化
"""

import subprocess
import time
import sys
import os
import threading
import logging
import requests
import psutil
import shutil
import socket

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_edge_debug_mode():
    """检查Edge是否已在调试模式运行"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if 'msedge' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if '--remote-debugging-port=9222' in cmdline:
                    return True
        return False
    except Exception as e:
        logger.warning(f"检查Edge进程失败: {e}")
        return False

def find_edge_executable():
    """查找Edge浏览器可执行文件路径"""
    possible_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Users\{}\AppData\Local\Microsoft\Edge\Application\msedge.exe".format(os.getenv('USERNAME', '')),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # 尝试在PATH中查找
    edge_path = shutil.which("msedge")
    if edge_path:
        return edge_path
    
    return None

def start_edge_debug_mode():
    """启动Edge调试模式"""
    try:
        edge_path = find_edge_executable()
        if not edge_path:
            print("❌ 未找到Microsoft Edge浏览器")
            print("💡 请确保已安装Microsoft Edge浏览器")
            return False
        
        print(f"🔍 找到Edge路径: {edge_path}")
        print("🚀 启动Edge调试模式...")
        
        # 启动Edge调试模式
        process = subprocess.Popen([
            edge_path,
            "--remote-debugging-port=9222",
            "--user-data-dir=" + os.path.join(os.getenv('TEMP', ''), 'edge_debug'),
            "--no-first-run",
            "--no-default-browser-check"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待浏览器启动
        time.sleep(3)
        
        # 检查调试端口是否可用
        for i in range(10):
            try:
                response = requests.get("http://localhost:9222/json", timeout=1)
                if response.status_code == 200:
                    print("✅ Edge调试模式启动成功")
                    return True
            except:
                pass
            time.sleep(1)
            if i < 9:
                print(f"⏳ 等待Edge调试服务... ({i+1}/10)")
        
        print("⚠️ Edge调试端口检测超时，但浏览器可能已启动")
        return True
        
    except Exception as e:
        print(f"❌ 启动Edge调试模式失败: {e}")
        return False

def open_ai_platforms():
    """在新标签页中打开AI平台"""
    try:
        ai_platforms = [
            ("DeepSeek", "https://chat.deepseek.com"),
            ("Kimi", "https://kimi.moonshot.cn"),
            ("智谱清言", "https://chatglm.cn")
        ]
        
        print("🌐 打开AI平台页面...")
        for platform_name, url in ai_platforms:
            try:
                # 使用调试API打开新标签页
                response = requests.post(
                    "http://localhost:9222/json/new",
                    params={"url": url},
                    timeout=2
                )
                if response.status_code == 200:
                    print(f"  ✅ {platform_name}: {url}")
                else:
                    print(f"  ⚠️ {platform_name}: 打开失败")
            except:
                print(f"  ⚠️ {platform_name}: 连接失败")
            time.sleep(0.5)
        
        print("\n💡 请在浏览器中登录您需要使用的AI平台")
        
    except Exception as e:
        print(f"❌ 打开AI平台页面失败: {e}")

def setup_browser_automation():
    """设置浏览器自动化环境"""
    print("\n🌐 浏览器自动化设置")
    print("=" * 40)
    
    # 检查Edge是否已在调试模式运行
    if check_edge_debug_mode():
        print("✅ 检测到Edge已在调试模式运行")
        return True
    
    # 询问用户是否要启动浏览器
    print("💡 浏览器自动化需要Edge调试模式")
    print("   这样可以无需配置Cookie直接使用AI平台")
    print()
    choice = input("是否启动Edge调试模式？(Y/n): ").strip().lower()
    
    if choice == 'n' or choice == 'no':
        print("⚠️ 跳过浏览器启动，您可以稍后手动启动")
        print("💡 手动启动命令:")
        edge_path = find_edge_executable()
        if edge_path:
            print(f'   "{edge_path}" --remote-debugging-port=9222')
        else:
            print('   "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" --remote-debugging-port=9222')
        return False
    
    # 启动Edge调试模式
    success = start_edge_debug_mode()
    if success:
        # 等待一下再打开AI平台
        time.sleep(2)
        open_ai_platforms()
        print("\n✨ 浏览器自动化环境已准备就绪！")
        print("💡 现在可以在Web界面选择'浏览器自动化'模式")
    
    return success

def start_backend():
    """启动增强版后端API服务"""
    try:
        # 确保端口8000可用
        if not ensure_port_available(8000, "API服务"):
            return None
        
        logger.info("🚀 启动增强版API服务...")
        process = subprocess.Popen([
            sys.executable, "backend/enhanced_api.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待API启动
        for i in range(15):
            try:
                response = requests.get("http://localhost:8000/health", timeout=1)
                if response.status_code == 200:
                    logger.info("✅ 增强版API服务启动成功")
                    print("📡 API服务: http://localhost:8000")
                    print("📚 API文档: http://localhost:8000/docs")
                    return process
            except:
                pass
            time.sleep(1)
            if i < 14:
                print(f"⏳ 等待API启动... ({i+1}/15)")
        
        logger.error("❌ API服务启动超时")
        return None
        
    except Exception as e:
        logger.error(f"❌ 启动后端失败: {e}")
        return None

def start_frontend(browser_debug_available=False):
    """启动增强版前端界面"""
    try:
        # 确保端口8501可用
        if not ensure_port_available(8501, "Web界面"):
            return None
        
        logger.info("🌐 启动增强版Web界面...")
        
        # 检查Streamlit是否可用
        result = subprocess.run([sys.executable, "-c", "import streamlit"], capture_output=True)
        if result.returncode != 0:
            logger.error("❌ Streamlit未安装，请运行: pip install streamlit")
            return None
        
        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", "webui/enhanced_app.py",
            "--server.port=8501",
            "--server.address=localhost"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待界面启动
        for i in range(20):
            try:
                response = requests.get("http://localhost:8501", timeout=1)
                if response.status_code == 200:
                    logger.info("✅ 增强版Web界面启动成功")
                    web_url = "http://localhost:8501"
                    print(f"🌐 访问地址: {web_url}")
                    
                    # 如果浏览器调试模式可用，自动在调试Edge中打开
                    if browser_debug_available:
                        print("🚀 正在调试Edge中自动打开Web界面...")
                        if open_url_in_debug_edge(web_url):
                            print("✨ Web界面已在调试Edge中打开，可以直接使用浏览器自动化模式！")
                        else:
                            print("⚠️ 请手动在调试Edge中访问: http://localhost:8501")
                    else:
                        print("💡 建议在同一个调试Edge浏览器中访问Web界面以获得最佳体验")
                    
                    return process
            except:
                pass
            time.sleep(1)
            if i < 19:
                print(f"⏳ 等待界面启动... ({i+1}/20)")
        
        logger.error("❌ Web界面启动超时")
        return None
        
    except Exception as e:
        logger.error(f"❌ 启动前端失败: {e}")
        return None

def check_port_available(port):
    """检查端口是否可用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except OSError:
        return False

def kill_process_on_port(port):
    """停止占用指定端口的进程"""
    try:
        # 在Windows上查找占用端口的进程
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if f':{port} ' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    try:
                        subprocess.run(['taskkill', '/f', '/pid', pid], 
                                     capture_output=True, check=True)
                        print(f"✅ 已停止占用端口{port}的进程 (PID: {pid})")
                        time.sleep(1)  # 等待进程完全停止
                        return True
                    except subprocess.CalledProcessError:
                        print(f"⚠️ 无法停止进程 {pid}")
        return False
    except Exception as e:
        print(f"❌ 检查端口占用失败: {e}")
        return False

def ensure_port_available(port, service_name):
    """确保端口可用"""
    if check_port_available(port):
        return True
    
    print(f"⚠️ 端口{port}被占用，尝试释放...")
    if kill_process_on_port(port):
        # 再次检查
        if check_port_available(port):
            print(f"✅ 端口{port}已释放，可以启动{service_name}")
            return True
    
    print(f"❌ 端口{port}仍被占用，{service_name}启动可能失败")
    return False

def open_url_in_debug_edge(url):
    """在调试模式Edge中打开URL"""
    try:
        response = requests.post(
            "http://localhost:9222/json/new",
            params={"url": url},
            timeout=3
        )
        if response.status_code == 200:
            print(f"✅ 已在调试Edge中打开: {url}")
            return True
        else:
            print(f"⚠️ 无法在调试Edge中打开: {url}")
            return False
    except Exception as e:
        print(f"❌ 调试Edge连接失败: {e}")
        return False

def main():
    """主启动函数"""
    print("🔍 AI多平台搜索聚合器 v2.1.0")
    print("=" * 60)
    print("🚀 增强版功能: 实时搜索 • 流式展示 • 浏览器自动化")
    print("=" * 60)
    print()
    
    try:
        # 第0步: 设置浏览器自动化 (可选)
        print("第0步: 浏览器自动化设置 (可选)")
        browser_debug_available = False
        try:
            browser_debug_available = setup_browser_automation()
        except Exception as e:
            print(f"⚠️ 浏览器设置失败: {e}")
            print("💡 您仍可以使用模拟模式或Cookie模式")
        
        print("\n" + "=" * 60)
        
        # 启动后端服务
        print("第1步: 启动后端API服务")
        api_process = start_backend()
        if not api_process:
            print("❌ 后端启动失败，请检查错误信息")
            return
        
        print("\n第2步: 启动前端Web界面")  
        web_process = start_frontend(browser_debug_available)
        if not web_process:
            print("❌ 前端启动失败，请检查错误信息")
            if api_process:
                api_process.terminate()
            return
        
        print("\n🎉 启动完成！")
        print("=" * 60)
        print("🌐 Web界面: http://localhost:8501")
        print("📡 API服务: http://localhost:8000")
        print("📚 API文档: http://localhost:8000/docs")
        print("=" * 60)
        
        if browser_debug_available:
            print("💡 推荐使用模式:")
            print("  🌐 浏览器自动化: ⭐⭐⭐⭐⭐ (已设置，强烈推荐)")
            print("  🎭 模拟模式: ⭐⭐⭐⭐ (快速测试)")
            print("  🍪 Cookie配置: ⭐⭐⭐ (备用方案)")
        else:
            print("💡 推荐使用模式:")
            print("  🎭 模拟模式: ⭐⭐⭐⭐⭐ (立即可用)")
            print("  🍪 Cookie配置: ⭐⭐⭐ (手动配置)")
            print("  🌐 浏览器自动化: ⭐⭐ (需要先设置)")
        
        print("=" * 60)
        print("📋 功能特色:")
        print("  • 实时观看搜索过程")
        print("  • 多平台并发搜索")
        print("  • 智能结果聚合")
        if browser_debug_available:
            print("  • 浏览器会话复用 ✅")
        else:
            print("  • 浏览器会话复用 (未设置)")
        print("=" * 60)
        print("按 Ctrl+C 停止所有服务...")
        
        # 等待用户中断
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 正在停止服务...")
        
    except Exception as e:
        logger.error(f"启动失败: {e}")
    finally:
        # 清理进程
        if 'api_process' in locals() and api_process:
            try:
                api_process.terminate()
                api_process.wait(timeout=5)
                print("✅ API服务已停止")
            except:
                api_process.kill()
                print("🔪 强制停止API服务")
        
        if 'web_process' in locals() and web_process:
            try:
                web_process.terminate()
                web_process.wait(timeout=5)
                print("✅ Web界面已停止")
            except:
                web_process.kill()
                print("🔪 强制停止Web界面")
        
        print("👋 服务已停止")

if __name__ == "__main__":
    main() 