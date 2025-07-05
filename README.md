# AI多平台搜索聚合器 v2.1.0

> 🚀 **一键启动的AI多平台搜索聚合器** - 支持浏览器自动化，无需Cookie配置

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-Latest-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ 核心特色

### 🌐 **浏览器自动化优先**
- **一键连接**：自动检测已登录的浏览器会话
- **无需Cookie**：直接复用浏览器登录状态
- **智能切换**：浏览器失败时自动回退到Cookie模式

### 🚀 **三种运行模式**
1. **🎭 模拟模式** (推荐) - 内置测试数据，立即可用
2. **🌐 浏览器自动化** - 连接已登录浏览器，无需配置
3. **🍪 Cookie配置** - 传统方式，手动配置

### 📊 **实时搜索体验**
- **并发搜索**：同时查询多个AI平台
- **流式展示**：实时显示搜索过程和内容生成
- **智能聚合**：自动整合多平台结果

## 🎯 支持平台

| 平台 | 状态 | 模式支持 | 推荐指数 |
|------|------|----------|----------|
| DeepSeek | ✅ 完全支持 | 模拟/浏览器/Cookie | ⭐⭐⭐⭐⭐ |
| Kimi | ✅ 完全支持 | 模拟/浏览器/Cookie | ⭐⭐⭐⭐ |
| 智谱清言 | ✅ 完全支持 | 模拟/浏览器/Cookie | ⭐⭐⭐⭐ |
| 豆包 | 🚧 开发中 | 模拟 | ⭐⭐⭐ |
| 秘塔搜索 | 📋 计划中 | 模拟 | ⭐⭐ |

## 🚀 快速开始

### 📋 环境要求
- Python 3.8+
- Microsoft Edge 浏览器
- 网络连接

### ⚡ 一键启动

```bash
# 克隆项目
git clone <repository-url>
cd AIsaerchFlow

# 安装依赖
pip install -r requirements.txt

# 启动项目
python run_project.py
```

启动后自动打开：http://localhost:8501

### 🎯 使用步骤

#### 方案1：模拟模式 (推荐新手)
1. 打开Web界面
2. 选择"🎭 模拟模式"
3. 输入搜索问题
4. 点击"🚀 开始搜索"
5. 3秒内获得聚合结果

#### 方案2：浏览器自动化 (推荐高级用户)
1. **启动调试模式Edge**：
   ```bash
   "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222
   ```

2. **登录AI平台**：
   - 访问 https://chat.deepseek.com 并登录
   - 访问 https://kimi.moonshot.cn 并登录
   - 访问 https://chatglm.cn 并登录

3. **使用搜索器**：
   - 打开Web界面
   - 选择"🌐 浏览器自动化"
   - 系统自动检测已登录平台
   - 开始搜索获得真实结果

#### 方案3：Cookie配置 (传统方式)
1. 选择"🍪 Cookie配置"
2. 点击"🔧 进入Cookie配置"
3. 手动输入或自动导入Cookie
4. 开始真实搜索

## 🛠️ 高级功能

### 📊 实时监控
- **搜索进度**：实时显示每个平台的搜索状态
- **内容流**：流式展示AI回答生成过程
- **错误诊断**：自动检测并提示问题解决方案

### 🔧 配置选项
- **超时设置**：调整搜索超时时间 (10-120秒)
- **并发数**：控制同时搜索的平台数 (1-5个)
- **AI处理**：启用智能内容聚合

### 📈 统计分析
- **搜索历史**：记录所有搜索记录
- **平台状态**：实时监控平台可用性
- **性能指标**：响应时间和成功率统计

## 🔧 开发者指南

### 📁 项目结构
```
AIsaerchFlow/
├── run_project.py              # 主启动脚本
├── requirements.txt            # 依赖列表
├── config.json                # 配置文件
├── core/                      # 核心模块
│   ├── stream_aggregator.py   # 流式聚合器
│   └── browser_search_engine.py # 浏览器搜索引擎
├── backend/                   # 后端API
│   └── enhanced_api.py        # FastAPI服务
├── webui/                     # Web界面
│   └── enhanced_app.py        # Streamlit界面
├── ragflow_utils/             # 工具函数
│   └── simple_aggregator.py   # 简单聚合器
└── backup_components/         # 备份组件
```

### 🔌 API接口
- `GET /` - 健康检查
- `POST /search` - 同步搜索 (向后兼容)
- `POST /search-async` - 异步搜索
- `GET /search-status/{id}` - 搜索状态
- `GET /platforms` - 平台列表
- `GET /browser-platforms` - 浏览器平台检测

### 🧪 测试工具
- `quick_test.py` - 一键功能测试
- `test_browser_connection.py` - 浏览器连接测试
- `start_with_browser.py` - 浏览器模式启动

## 🔍 故障排除

### 常见问题

**Q: 浏览器自动化连接失败？**
```bash
# 解决方案：启用Edge调试模式
"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222
```

**Q: 搜索结果为空？**
- 检查网络连接
- 确认平台登录状态
- 尝试模拟模式验证功能

**Q: API连接失败？**
```bash
# 手动启动后端
python backend/enhanced_api.py
```

**Q: 依赖安装失败？**
```bash
# 升级pip并重新安装
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 🆘 获取帮助
1. 检查 [技术文档](BROWSER_AUTOMATION_SOLUTION.md)
2. 运行 `python quick_test.py` 诊断问题
3. 查看 `PROJECT_STRUCTURE.md` 了解项目结构

## 🚧 开发路线图

### v2.2.0 (计划中)
- [ ] 支持更多AI平台 (豆包、秘塔搜索)
- [ ] 增加结果导出功能
- [ ] 优化搜索算法
- [ ] 添加用户偏好设置

### v2.3.0 (未来)
- [ ] 支持插件系统
- [ ] 添加API密钥模式
- [ ] 移动端适配
- [ ] 云部署支持

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 发起Pull Request

## 📄 许可证

本项目采用 [MIT许可证](LICENSE)

## 📞 联系方式

- 项目地址：[GitHub Repository]
- 技术支持：[提交Issue]
- 文档反馈：欢迎改进建议

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给个Star支持！⭐**

Made with ❤️ by AI Multi-Platform Search Team

</div> 