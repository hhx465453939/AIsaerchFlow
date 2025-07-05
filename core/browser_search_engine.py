#!/usr/bin/env python3
"""
浏览器自动化搜索引擎
使用Playwright连接到现有浏览器会话，直接操作AI平台页面进行搜索
"""

import asyncio
import time
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BrowserSearchEngine:
    """浏览器自动化搜索引擎"""
    
    def __init__(self, debug_port: int = 9222):
        self.debug_port = debug_port
        self.browser = None
        self.playwright = None
        
        # AI平台配置 - 增强检测规则
        self.platform_configs = {
            "DeepSeek": {
                "domains": ["chat.deepseek.com", "deepseek.com"],  # 支持多个域名
                "input_selector": 'textarea[placeholder*="请输入"], textarea[placeholder*="输入"], textarea[data-testid*="input"], #chat-input textarea',
                "send_selector": 'button[type="submit"], button[aria-label*="发送"], .send-button, [data-testid*="send"]',
                "result_selector": '.message-content, .answer-content, [class*="message"], [class*="response"], .chat-message',
                "wait_time": 3
            },
            "Kimi": {
                "domains": ["kimi.moonshot.cn", "moonshot.cn"],
                "input_selector": 'textarea[placeholder*="请输入"], textarea[placeholder*="有什么"], textarea[placeholder*="输入"], #input-area textarea, .input-textarea',
                "send_selector": 'button[type="submit"], button[aria-label*="发送"], .send-btn, [data-testid*="send"], .submit-button',
                "result_selector": '.message, [class*="answer"], [class*="response"], .chat-message, .ai-response',
                "wait_time": 4
            },
            "智谱清言": {
                "domains": ["chatglm.cn", "zhipuai.cn"],
                "input_selector": 'textarea, input[type="text"], .input-box textarea, #chat-input, [placeholder*="输入"]',
                "send_selector": 'button[type="submit"], .send-btn, .submit-btn, [aria-label*="发送"], .send-button',
                "result_selector": '.response, .answer, [class*="message"], .chat-response, .ai-message',
                "wait_time": 5
            }
        }
    
    async def connect(self) -> bool:
        """连接到浏览器会话"""
        try:
            from playwright.async_api import async_playwright
            
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.connect_over_cdp(
                f"http://localhost:{self.debug_port}"
            )
            
            logger.info(f"成功连接到浏览器 (端口: {self.debug_port})")
            return True
            
        except Exception as e:
            logger.error(f"连接浏览器失败: {e}")
            return False
    
    async def disconnect(self):
        """断开浏览器连接"""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.warning(f"断开连接时出错: {e}")
    
    async def detect_available_platforms(self) -> List[Dict[str, any]]:
        """检测浏览器中可用的AI平台"""
        available_platforms = []
        
        # 先连接到浏览器
        if not await self.connect():
            logger.error("无法连接到浏览器，请确保Edge调试模式已启动")
            return available_platforms
        
        try:
            # 检查所有上下文和页面
            all_pages = []
            for context in self.browser.contexts:
                all_pages.extend(context.pages)
            
            logger.info(f"开始检测，共发现 {len(all_pages)} 个页面")
            
            for page in all_pages:
                page_url = page.url
                logger.info(f"检查页面: {page_url}")
                
                for platform_name, config in self.platform_configs.items():
                    domains = config["domains"]
                    
                    # 检查页面是否属于AI平台（支持多个域名）
                    is_platform_page = any(domain in page_url for domain in domains)
                    
                    if is_platform_page:
                        logger.info(f"✅ 发现 {platform_name} 页面: {page_url}")
                        
                        try:
                            # 获取页面标题
                            page_title = await page.title()
                            logger.info(f"页面标题: {page_title}")
                            
                            # 检查是否已登录
                            is_logged_in = await self._check_platform_login_status(page, platform_name, config)
                            
                            platform_info = {
                                "platform": platform_name,
                                "url": page_url,
                                "domain": domains[0],  # 使用主域名
                                "is_logged_in": is_logged_in,
                                "tab_title": page_title,
                                "status": "ready" if is_logged_in else "need_login"
                            }
                            
                            available_platforms.append(platform_info)
                            logger.info(f"🎯 {platform_name} 状态: {'已登录' if is_logged_in else '需要登录'}")
                            
                        except Exception as e:
                            logger.error(f"检查 {platform_name} 页面时出错: {e}")
                            
                        break  # 找到匹配的平台后跳出内层循环
            
            # 去重（同一个平台可能有多个标签页）
            unique_platforms = {}
            for platform in available_platforms:
                platform_name = platform["platform"]
                if platform_name not in unique_platforms or platform["is_logged_in"]:
                    unique_platforms[platform_name] = platform
            
            final_platforms = list(unique_platforms.values())
            logger.info(f"检测完成，发现 {len(final_platforms)} 个平台页面")
            
            return final_platforms
            
        except Exception as e:
            logger.error(f"检测平台时出错: {e}")
            return []
        finally:
            await self.disconnect()
    
    async def _check_platform_login_status(self, page, platform: str, config: Dict) -> bool:
        """检查平台登录状态"""
        try:
            # 激活页面
            await page.bring_to_front()
            await asyncio.sleep(1)
            
            # 检查输入框是否存在（表示已登录）
            input_selector = config["input_selector"]
            
            try:
                # 等待输入框出现，超时时间短一些
                await page.wait_for_selector(input_selector, timeout=5000)
                
                # 检查输入框是否可用
                input_element = page.locator(input_selector).first
                is_visible = await input_element.is_visible()
                is_enabled = await input_element.is_enabled()
                
                if is_visible and is_enabled:
                    logger.info(f"{platform} 输入框可用，已登录")
                    return True
                else:
                    logger.warning(f"{platform} 输入框不可用")
                    return False
                    
            except Exception as e:
                logger.warning(f"{platform} 输入框检测失败: {e}")
                
                # 如果输入框检测失败，尝试其他登录状态检测方法
                return await self._check_alternative_login_indicators(page, platform)
                
        except Exception as e:
            logger.error(f"检查 {platform} 登录状态失败: {e}")
            return False
    
    async def _check_alternative_login_indicators(self, page, platform: str) -> bool:
        """检查替代的登录状态指示器"""
        try:
            # 检查是否存在登录按钮（未登录的标志）
            login_selectors = [
                'button:has-text("登录")',
                'button:has-text("Login")', 
                'a:has-text("登录")',
                'a:has-text("Login")',
                '.login-btn',
                '.login-button'
            ]
            
            for selector in login_selectors:
                try:
                    login_element = page.locator(selector).first
                    if await login_element.is_visible():
                        logger.info(f"{platform} 发现登录按钮，未登录")
                        return False
                except:
                    continue
            
            # 检查是否存在用户头像或用户名（已登录的标志）
            logged_in_selectors = [
                '.avatar',
                '.user-avatar', 
                '.profile-avatar',
                '[class*="avatar"]',
                '[class*="user"]',
                '.user-info'
            ]
            
            for selector in logged_in_selectors:
                try:
                    user_element = page.locator(selector).first
                    if await user_element.is_visible():
                        logger.info(f"{platform} 发现用户头像，已登录")
                        return True
                except:
                    continue
            
            # 检查页面标题是否包含登录相关关键词
            title = await page.title()
            if any(keyword in title.lower() for keyword in ['login', '登录', 'sign in', '请登录']):
                logger.info(f"{platform} 页面标题包含登录关键词，未登录")
                return False
            
            # 如果都检测不出来，默认认为可能已登录（保守判断）
            logger.warning(f"{platform} 无法确定登录状态，默认为已登录")
            return True
            
        except Exception as e:
            logger.error(f"替代登录检测失败: {e}")
            return False
    
    async def search_platform(self, platform: str, query: str) -> Dict:
        """在指定平台进行搜索"""
        if platform not in self.platform_configs:
            return {
                "success": False,
                "error": f"不支持的平台: {platform}",
                "content": ""
            }
        
        config = self.platform_configs[platform]
        
        try:
            # 查找平台页面
            page = await self._find_platform_page(platform)
            if not page:
                return {
                    "success": False,
                    "error": f"未找到 {platform} 页面，请确保已打开并登录",
                    "content": ""
                }
            
            logger.info(f"找到 {platform} 页面: {page.url}")
            
            # 清空输入框并输入问题
            await self._input_query(page, config, query)
            
            # 点击发送按钮
            await self._send_query(page, config)
            
            # 等待并获取回答
            content = await self._get_response(page, config, platform)
            
            return {
                "success": True,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "platform": platform,
                "method": "browser_automation"
            }
            
        except Exception as e:
            logger.error(f"{platform} 搜索失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": f"❌ {platform} 搜索异常: {str(e)}"
            }
    
    async def _find_platform_page(self, platform: str):
        """查找指定平台的页面"""
        config = self.platform_configs[platform]
        domains = config["domains"]
        
        # 遍历所有上下文和页面
        for context in self.browser.contexts:
            for page in context.pages:
                page_url = page.url
                # 检查是否匹配任一域名
                if any(domain in page_url for domain in domains):
                    # 确保页面是活动的
                    await page.bring_to_front()
                    logger.info(f"找到并激活 {platform} 页面: {page_url}")
                    return page
        
        logger.warning(f"未找到 {platform} 页面")
        return None
    
    async def _input_query(self, page, config: Dict, query: str):
        """输入搜索问题"""
        input_selectors = config["input_selector"].split(", ")
        
        # 尝试多个输入框选择器
        input_element = None
        for selector in input_selectors:
            try:
                await page.wait_for_selector(selector.strip(), timeout=3000)
                input_element = page.locator(selector.strip()).first
                
                if await input_element.is_visible() and await input_element.is_enabled():
                    logger.info(f"找到可用输入框: {selector.strip()}")
                    break
            except:
                continue
        
        if not input_element:
            raise Exception("未找到可用的输入框")
        
        try:
            # 聚焦到输入框
            await input_element.focus()
            await asyncio.sleep(0.3)
            
            # 清空输入框 - 多种方法
            await input_element.click()
            await page.keyboard.press("Control+a")
            await asyncio.sleep(0.1)
            await page.keyboard.press("Delete")
            await asyncio.sleep(0.3)
            
            # 输入问题 - 分段输入，避免卡住
            await input_element.type(query, delay=50)
            await asyncio.sleep(0.5)
            
            # 验证输入是否成功
            current_value = await input_element.input_value()
            if query not in current_value:
                logger.warning(f"输入验证失败，重试...")
                await input_element.fill(query)
                await asyncio.sleep(0.3)
            
            logger.info(f"✅ 成功输入问题: {query[:50]}...")
            
        except Exception as e:
            logger.error(f"输入问题失败: {e}")
            raise
    
    async def _send_query(self, page, config: Dict):
        """发送查询"""
        send_selectors = config["send_selector"].split(", ")
        
        # 尝试多个发送按钮选择器
        sent = False
        for selector in send_selectors:
            try:
                send_button = page.locator(selector.strip()).first
                
                if await send_button.is_visible() and await send_button.is_enabled():
                    await send_button.click()
                    logger.info(f"✅ 点击发送按钮: {selector.strip()}")
                    sent = True
                    break
            except:
                continue
        
        if not sent:
            # 尝试按回车键
            try:
                await page.keyboard.press("Enter")
                logger.info("✅ 使用回车键发送")
                sent = True
            except:
                pass
        
        if not sent:
            raise Exception("无法发送查询，未找到可用的发送方式")
        
        # 等待发送完成
        await asyncio.sleep(2)
    
    async def _get_response(self, page, config: Dict, platform: str) -> str:
        """获取AI回答"""
        result_selector = config["result_selector"]
        wait_time = config["wait_time"]
        
        logger.info(f"等待 {platform} 回答...")
        
        # 等待回答出现
        try:
            await page.wait_for_selector(result_selector, timeout=30000)
        except:
            logger.warning(f"{platform} 回答超时，尝试获取现有内容")
        
        # 等待内容生成
        await asyncio.sleep(wait_time)
        
        # 获取最新的回答内容
        try:
            # 获取所有匹配的元素
            elements = await page.query_selector_all(result_selector)
            
            if not elements:
                return f"⚠️ 未找到 {platform} 的回答内容"
            
            # 获取最后一个元素的文本（通常是最新回答）
            last_element = elements[-1]
            content = await last_element.inner_text()
            
            if content.strip():
                return f"# {platform} 回答\n\n{content.strip()}"
            else:
                return f"⚠️ {platform} 回答内容为空"
                
        except Exception as e:
            logger.error(f"获取 {platform} 回答失败: {e}")
            return f"❌ 获取 {platform} 回答失败: {str(e)}"


class BrowserSearchManager:
    """浏览器搜索管理器"""
    
    def __init__(self):
        self.engine = None
    
    async def search_multiple_platforms(self, platforms: List[str], query: str) -> Dict:
        """在多个平台进行搜索"""
        self.engine = BrowserSearchEngine()
        
        # 连接到浏览器
        if not await self.engine.connect():
            return {
                "success": False,
                "error": "无法连接到浏览器会话",
                "results": []
            }
        
        results = []
        
        try:
            # 并发搜索多个平台
            tasks = [
                self.engine.search_platform(platform, query)
                for platform in platforms
            ]
            
            platform_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(platform_results):
                if isinstance(result, Exception):
                    results.append({
                        "platform": platforms[i],
                        "success": False,
                        "error": str(result),
                        "content": f"❌ {platforms[i]} 搜索异常: {str(result)}"
                    })
                else:
                    results.append(result)
            
            return {
                "success": True,
                "results": results,
                "method": "browser_automation",
                "timestamp": datetime.now().isoformat()
            }
            
        finally:
            await self.engine.disconnect()


# 异步搜索函数接口
async def browser_search(platforms: List[str], query: str) -> Dict:
    """浏览器自动化搜索接口"""
    manager = BrowserSearchManager()
    return await manager.search_multiple_platforms(platforms, query)


# 同步搜索函数接口（用于与现有代码兼容）
def sync_browser_search(platforms: List[str], query: str) -> Dict:
    """同步浏览器搜索接口"""
    try:
        # 在新的事件循环中运行异步函数
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(browser_search(platforms, query))
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"浏览器搜索失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "results": []
        } 