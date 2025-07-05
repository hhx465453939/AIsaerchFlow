#!/usr/bin/env python3
"""
浏览器连接测试脚本
验证是否能够连接到Edge浏览器并检测AI平台页面
"""

import asyncio
import sys
import time

async def test_browser_connection():
    """测试浏览器连接"""
    print("🌐 浏览器连接测试")
    print("=" * 50)
    
    try:
        # 检查Playwright是否安装
        try:
            from playwright.async_api import async_playwright
            print("✅ Playwright 已安装")
        except ImportError:
            print("❌ Playwright 未安装")
            print("💡 请运行: pip install playwright")
            print("💡 然后运行: playwright install")
            return False
        
        # 尝试连接到浏览器
        print("\n🔍 尝试连接到Edge浏览器...")
        
        playwright = await async_playwright().start()
        
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
            print("✅ 成功连接到浏览器调试端口")
            
            # 检查浏览器上下文
            contexts = browser.contexts
            print(f"📊 检测到 {len(contexts)} 个浏览器上下文")
            
            if not contexts:
                print("⚠️ 没有可用的浏览器上下文")
                print("💡 请确保浏览器已打开并有页面")
                return False
            
            # 收集所有页面
            all_pages = []
            for context in contexts:
                all_pages.extend(context.pages)
            
            print(f"📄 检测到 {len(all_pages)} 个页面")
            
            if not all_pages:
                print("⚠️ 没有可用的页面")
                return False
            
            # 显示所有页面
            print("\n📋 当前打开的页面:")
            for i, page in enumerate(all_pages):
                title = await page.title()
                url = page.url
                print(f"  {i+1}. {title} - {url}")
            
            # 检查AI平台页面
            ai_platforms = {
                "DeepSeek": "chat.deepseek.com",
                "Kimi": "kimi.moonshot.cn", 
                "智谱清言": "chatglm.cn",
                "豆包": "doubao.com"
            }
            
            detected_platforms = []
            platform_pages = {}
            
            print("\n🔍 检测AI平台页面...")
            for page in all_pages:
                url = page.url
                for platform, domain in ai_platforms.items():
                    if domain in url:
                        detected_platforms.append(platform)
                        platform_pages[platform] = page
                        title = await page.title()
                        print(f"✅ 找到 {platform}: {title}")
            
            if not detected_platforms:
                print("⚠️ 未检测到AI平台页面")
                print("💡 请在浏览器中打开以下任一平台:")
                for platform, domain in ai_platforms.items():
                    print(f"   • {platform}: https://{domain}")
                return False
            
            # 测试页面交互
            print(f"\n🧪 测试页面交互能力...")
            
            for platform in detected_platforms:
                page = platform_pages[platform]
                try:
                    # 尝试激活页面
                    await page.bring_to_front()
                    print(f"✅ {platform} 页面已激活")
                    
                    # 检查页面是否可交互
                    await page.wait_for_load_state("networkidle", timeout=5000)
                    print(f"✅ {platform} 页面加载完成")
                    
                    # 尝试查找输入框
                    input_selectors = [
                        'textarea[placeholder*="请输入"]',
                        'textarea[placeholder*="有什么"]',
                        'textarea',
                        'input[type="text"]'
                    ]
                    
                    found_input = False
                    for selector in input_selectors:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            print(f"✅ {platform} 找到输入框: {selector}")
                            found_input = True
                            break
                    
                    if not found_input:
                        print(f"⚠️ {platform} 未找到输入框")
                    
                except Exception as e:
                    print(f"⚠️ {platform} 交互测试失败: {str(e)}")
            
            await browser.close()
            print(f"\n🎉 测试完成！")
            print(f"   检测到可用平台: {', '.join(detected_platforms)}")
            return True
            
        except Exception as e:
            if "connect" in str(e).lower():
                print("❌ 无法连接到浏览器调试端口")
                print("\n💡 启用调试模式的方法:")
                print("1. 关闭所有Edge窗口")
                print('2. 运行命令启动Edge:')
                print('   "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" --remote-debugging-port=9222')
                print("3. 在Edge中访问并登录AI平台")
                print("4. 重新运行此测试")
                return False
            else:
                print(f"❌ 连接失败: {str(e)}")
                return False
        
        finally:
            await playwright.stop()
            
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        return False

def main():
    """主函数"""
    print("🚀 AI搜索聚合器 - 浏览器连接测试工具")
    print()
    
    try:
        success = asyncio.run(test_browser_connection())
        
        print("\n" + "=" * 50)
        if success:
            print("✅ 浏览器连接测试成功！")
            print("💡 现在可以在项目中使用浏览器会话功能")
            print("\n📋 下一步操作:")
            print("1. 启动项目: python run_project.py")
            print("2. 访问界面: http://localhost:8501")  
            print("3. 选择真实模式")
            print("4. 点击'连接浏览器会话'")
        else:
            print("❌ 浏览器连接测试失败")
            print("💡 请按照上述建议解决问题")
            
    except KeyboardInterrupt:
        print("\n\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程出现异常: {e}")

if __name__ == "__main__":
    main() 