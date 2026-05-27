# DeepSeek 仪表板 🚀

> 一个轻量级的 Windows 桌面仪表板，用于可视化和分析 DeepSeek API 使用情况。
> 
---
## ✨ 功能特性

- 📊 **Token 用量分析** — 实时查看提示词（prompt）与补全（completion）Token 消耗
- 🤖 **模型分布** — 按 `deepseek-coder` / `deepseek-chat` 等模型分类统计
- 💰 **费用追踪** — 单次请求费用及累计消费一目了然
- ⚡ **延迟监控** — 响应时间趋势图，定位慢查询
- 💾 **缓存命中率** — 分析缓存使用效率，优化成本
- 📈 **时间趋势** — 按天 / 小时查看请求量和费用变化
- 🔌 **纯离线** — 所有数据本地存储，无需联网

---

## 📦 下载

从 [Releases](https://github.com/Linhaochgen/DeepSeekDashboard/releases) 页面下载最新版本：

| 文件 | 说明 |
|---|---|
| `DeepSeekDashboard.exe` | Windows 可执行文件（~48 MB） |
| `usage_log.json` | 示例数据文件（可选） |

> **系统要求：** Windows 10 及以上（64 位）

---

## 🚀 快速开始

1. 下载 `DeepSeekDashboard.exe`
2. 将你的 DeepSeek API 日志导出为 JSON 格式（见下方数据格式），命名为 `usage_log.json`
3. 将 `usage_log.json` 放在 `.exe` **同级目录**下
4. 双击 `DeepSeekDashboard.exe` 启动
5. 开始探索你的 API 使用数据！

---

## 📄 数据格式

`usage_log.json` 是一个 JSON 数组，每个 API 请求对应一个对象：

```json
[
  {
    "timestamp": "2026-04-27T06:30:49.780095",
    "model": "deepseek-coder",
    "prompt_tokens": 905,
    "completion_tokens": 288,
    "total_tokens": 1193,
    "cache_hit": false,
    "latency_ms": 787.9,
    "cost": 0.002386,
    "status": "success"
  }
]
```

### 字段说明

| 字段 | 类型 | 说明 |
|---|---|---|
| `timestamp` | 字符串 (ISO-8601) | API 请求时间 |
| `model` | 字符串 | 使用的模型名称 |
| `prompt_tokens` | 整数 | 输入 Token 数 |
| `completion_tokens` | 整数 | 输出 Token 数 |
| `total_tokens` | 整数 | Token 总数 |
| `cache_hit` | 布尔值 | 是否命中缓存 |
| `latency_ms` | 浮点数 | 响应延迟（毫秒） |
| `cost` | 浮点数 | 预估费用（美元） |
| `status` | 字符串 | 请求状态 |

---

## ❓ 常见问题

**Q：有 Mac / Linux 版本吗？**
A：目前仅支持 Windows。欢迎开发者参与跨平台移植。

**Q：如何导出 DeepSeek API 日志？**
A：请参考 DeepSeek 官方文档，导出 API 请求日志后，按上述 JSON 格式整理即可。

**Q：数据安全吗？**
A：所有数据仅在本地处理，不会上传任何信息。

**Q：`usage_log.json` 可以自定义路径吗？**
A：当前版本要求数据文件与可执行文件位于同一目录。

---

## 📧 联系我

有任何问题、建议或合作意向，欢迎通过以下方式联系：

- **Email：** [your-email@example.com](mailto:your-email@example.com)
- **GitHub Issues：** [提交 Issue](https://github.com/yourname/DeepSeekDashboard/issues)
- **博客 / 个人主页：** [https://your-blog.com](https://your-blog.com)

---

## ☕ 请我喝杯咖啡

如果这个项目对你有帮助，欢迎打赏支持！你的每一份鼓励都是我持续更新的动力 ❤️
打赏：软件内-设置页面


## ⭐ 支持项目

如果觉得有用，请给一个 **Star** ⭐，让更多人看到！


*

