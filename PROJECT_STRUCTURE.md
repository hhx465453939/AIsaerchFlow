# 项目结构说明

## 核心文件
- `run_project.py` - 项目启动脚本
- `requirements.txt` - 依赖包列表
- `config.json` - 配置文件
- `README.md` - 项目说明文档

## 快速启动工具
- `quick_test.py` - 一键测试工具
- `start_with_browser.py` - 浏览器自动化启动脚本
- `test_browser_connection.py` - 浏览器连接测试

## 核心模块
- `core/` - 核心功能模块
  - `stream_aggregator.py` - 多平台流式聚合器
  - `browser_search_engine.py` - 浏览器搜索引擎

- `backend/` - 后端API
  - `enhanced_api.py` - 增强版API服务

- `webui/` - Web界面
  - `enhanced_app.py` - 增强版Streamlit界面

- `ragflow_utils/` - 工具函数
  - `simple_aggregator.py` - 简单聚合器

## 备份组件
- `backup_components/` - 非核心功能备份
  - `config.example.json` - 配置文件示例

## 技术文档
- `BROWSER_AUTOMATION_SOLUTION.md` - 浏览器自动化解决方案

## 清理说明
本次清理删除了以下类型的文件：
1. 重复的开发日志和文档
2. 过时的脚本和测试文件
3. 不再使用的目录和模块
4. 缓存文件
