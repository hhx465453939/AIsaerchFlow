#!/usr/bin/env python3
"""
AI搜索聚合器 - 浏览器自动化启动脚本
自动启动项目并提供浏览器连接指导
"""

import subprocess
import sys
import time
import os
import webbrowser
from pathlib import Path

def print_banner():
    """打印启动横幅"""
    print("🌐" + "="*70 + "🌐")
    print("    AI多平台搜索聚合器 - 浏览器自动化版")
    print("    v2.1 - 突破Cookie加密限制，直接复用浏览器会话")
    print("🌐" + "="*70 + "🌐")
    print()

def check_dependencies():
    """检查必要的依赖"""
    print("🔍 检查依赖...")
    
    missing_deps = []
    
    # 检查基础依赖
    try:
        import streamlit
        print("✅ Streamlit 已安装")
    except ImportError:
        missing_deps.append("streamlit")
    
    try:
        import playwright
        print("✅ Playwright 已安装")
    except ImportError:
        missing_deps.append("playwright")
    
    try:
        import psutil
        print("✅ psutil 已安装")
    except ImportError:
        missing_deps.append("psutil")
    
    if missing_deps:
        print(f"❌ 缺少依赖: {', '.join(missing_deps)}")
        print("\n💡 请安装缺少的依赖:")
        print(f"pip install {' '.join(missing_deps)}")
        if 'playwright' in missing_deps:
            print("playwright install")
        return False
    
    print("✅ 所有依赖已满足")
    return True

def show_browser_setup_guide():
    """显示浏览器设置指导"""
    print("\n📖 浏览器设置指导")
    print("=" * 50)
    
    print("为了使用浏览器自动化功能，需要以调试模式启动Edge浏览器：")
    print()
    
    print("🎯 方法1: 命令行启动 (推荐)")
    print('复制并运行以下命令:')
    print()
    print('"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" --remote-debugging-port=9222')
    print()
    print("或者：")
    print('"C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe" --remote-debugging-port=9222')
    print()
    
    print("🎯 方法2: 修改快捷方式")
    print("1. 右键桌面上的Edge快捷方式")
    print("2. 选择 '属性'")
    print("3. 在 '目标' 字段的末尾添加: --remote-debugging-port=9222")
    print("4. 点击 '确定' 并重新启动Edge")
    print()
    
    print("📝 重要提示:")
    print("• 启动调试模式后，在Edge中访问并登录 https://chat.deepseek.com")
    print("• 保持浏览器和AI平台页面打开")
    print("• 然后回到这里继续操作")
    print()

def wait_for_user_ready():
    """等待用户完成浏览器设置"""
    print("⏳ 请按照上述指导设置浏览器...")
    print()
    
    while True:
        response = input("✋ 已完成浏览器设置并登录AI平台? [y/N]: ").strip().lower()
        if response in ['y', 'yes', '是']:
            break
        elif response in ['n', 'no', '否', '']:
            print("💡 请完成浏览器设置后再继续")
            continue
        else:
            print("⚠️ 请输入 y 或 n")

def test_browser_connection():
    """测试浏览器连接"""
    print("\n🧪 测试浏览器连接...")
    
    try:
        result = subprocess.run([
            sys.executable, "test_browser_connection.py"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ 浏览器连接测试成功！")
            return True
        else:
            print("❌ 浏览器连接测试失败")
            print("错误输出:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ 连接测试超时")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def start_project():
    """启动项目"""
    print("\n🚀 启动项目...")
    
    try:
        # 启动项目
        subprocess.Popen([sys.executable, "run_project.py"])
        
        # 等待服务启动
        print("⏳ 等待服务启动...")
        time.sleep(8)
        
        # 自动打开浏览器
        print("🌐 打开Web界面...")
        webbrowser.open("http://localhost:8501")
        
        print("\n🎉 启动完成！")
        print("=" * 50)
        print("🌐 Web界面: http://localhost:8501")
        print("📡 API服务: http://localhost:8000")
        print("💡 使用指南:")
        print("  1. 选择 '🔥 真实模式'")
        print("  2. 点击 '🔧 配置真实模式'")
        print("  3. 点击 '🌐 连接浏览器会话'")
        print("  4. 开始搜索！")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return False

def main():
    """主函数"""
    print_banner()
    
    # 检查依赖
    if not check_dependencies():
        print("\n❌ 请先安装缺少的依赖")
        return
    
    # 显示浏览器设置指导
    show_browser_setup_guide()
    
    # 等待用户设置
    wait_for_user_ready()
    
    # 测试浏览器连接
    if test_browser_connection():
        print("✅ 浏览器连接正常，继续启动项目...")
    else:
        print("⚠️ 浏览器连接测试失败，但仍可继续启动项目")
        response = input("是否继续启动? [Y/n]: ").strip().lower()
        if response in ['n', 'no', '否']:
            print("👋 启动取消")
            return
    
    # 启动项目
    if start_project():
        print("\n🎊 项目启动成功！现在可以使用浏览器自动化功能了！")
        
        try:
            input("\n按 Enter 键退出...")
        except KeyboardInterrupt:
            pass
    else:
        print("\n❌ 项目启动失败")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 启动被用户中断")
    except Exception as e:
        print(f"\n❌ 启动过程出现异常: {e}") 