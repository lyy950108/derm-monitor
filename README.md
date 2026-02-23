# 🩺 Derm Monitor — 皮肤科信息聚合推送系统

> 自动抓取皮肤科领域最新指南、行业资讯，翻译英文标题并通过邮件推送每日摘要。

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Schedule](https://img.shields.io/badge/Schedule-Daily%2008%3A00-orange)

## ✨ 功能特性

- **多源聚合**：同时抓取 7 个权威信息源，覆盖指南、媒体、公众号
- **自动翻译**：英文标题自动翻译为中文（支持 Google / 百度 / DeepL）
- **智能去重**：基于文章唯一标识去重，避免重复推送
- **邮件推送**：生成精美 HTML 邮件，按分类整理推送
- **零服务器**：支持 GitHub Actions 免费定时运行，无需自建服务器

## 📦 信息源

| 分类 | 来源 | 方式 | 语言 |
|------|------|------|------|
| 指南更新 | AAD (美国皮肤病学会) | 网页抓取 | EN → 中文翻译 |
| 指南更新 | BAD (英国皮肤科协会) | 网页抓取 | EN → 中文翻译 |
| 指南更新 | 中华医学会皮肤性病学分会 | 网页抓取 | 中文 |
| 行业资讯 | Dermatology Times | RSS | EN → 中文翻译 |
| 行业资讯 | Healio Dermatology | RSS | EN → 中文翻译 |
| 行业资讯 | 医学界皮肤频道 | 网页抓取 | 中文 |
| 微信公众号 | 皮肤科杨希川教授 / 中华皮肤科杂志 | 搜狗微信搜索 | 中文 |

## 🚀 部署方式

### 方式一：GitHub Actions（推荐，免费无服务器）

**Fork 本仓库后，只需配置 4 个 Secrets 即可自动每日推送。**

1. **Fork 本仓库**

2. **配置 Secrets**：进入你 Fork 的仓库 → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`，添加以下 Secrets：

   | Secret 名称 | 说明 | 示例 |
   |-------------|------|------|
   | `SMTP_SERVER` | SMTP 服务器地址 | `smtp.qq.com` |
   | `SMTP_PORT` | SMTP 端口 | `465` |
   | `EMAIL_SENDER` | 发件人邮箱 | `you@qq.com` |
   | `EMAIL_PASSWORD` | SMTP 授权码（非邮箱密码） | `abcdefghijklmnop` |
   | `EMAIL_RECIPIENT` | 收件人邮箱 | `you@example.com` |

3. **启用 Actions**：进入 `Actions` 标签页，点击 `I understand my workflows, go ahead and enable them`

4. **手动测试**：在 Actions 页面选择 `Daily Derm Monitor` → `Run workflow` → `Run workflow`

5. **自动运行**：每天北京时间 08:00 自动执行

> **获取 SMTP 授权码**：
> - QQ 邮箱：设置 → 账户 → POP3/SMTP 服务 → 开启 → 生成授权码
> - 163 邮箱：设置 → POP3/SMTP/IMAP → 开启 → 设置授权码
> - Gmail：需开启两步验证 → 生成应用专用密码

### 方式二：本地运行

```bash
# 1. 克隆项目
git clone https://github.com/YOUR_USERNAME/derm-monitor.git
cd derm-monitor

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置
cp config.example.yaml config.yaml
# 编辑 config.yaml，填入邮箱 SMTP 信息

# 4. 测试运行（不发邮件）
python main.py --dry-run

# 5. 正式运行
python main.py
```

**设置定时任务（Linux/Mac）：**
```bash
crontab -e
# 添加以下行（每天早上 8 点运行）
0 8 * * * cd /path/to/derm-monitor && /usr/bin/python3 main.py >> log.txt 2>&1
```

## 📁 项目结构

```
derm-monitor/
├── .github/workflows/
│   └── daily-run.yml           # GitHub Actions 定时任务
├── sources/
│   ├── base.py                 # 抓取基类 & Article 数据结构
│   ├── rss_source.py           # 通用 RSS 抓取器
│   ├── aad.py                  # AAD 指南
│   ├── bad.py                  # BAD 指南
│   ├── chinese_derm.py         # 中华医学会皮肤性病学分会
│   ├── dermatology_times.py    # Dermatology Times
│   ├── healio.py               # Healio Dermatology
│   ├── yixuejie.py             # 医学界皮肤频道
│   └── wechat_sogou.py         # 搜狗微信搜索
├── templates/
│   └── email_template.html     # 邮件 HTML 模板
├── main.py                     # 主入口
├── translator.py               # 翻译模块
├── storage.py                  # 去重存储
├── notifier.py                 # 邮件推送
├── config.example.yaml         # 配置模板
├── requirements.txt
├── LICENSE
└── README.md
```

## ⚙️ 配置说明

详细配置项见 [`config.example.yaml`](config.example.yaml)，主要包括：

- **邮件推送**：SMTP 服务器、发件人、收件人列表
- **翻译后端**：`google_free`（默认免费）/ `baidu` / `deepl`
- **信息源开关**：可单独启用/禁用每个信息源
- **抓取参数**：超时时间、重试次数、请求间隔

## 🔧 自定义扩展

### 添加新信息源

继承 `BaseSource` 类，实现 `fetch()` 方法：

```python
from sources.base import Article, BaseSource

class MySource(BaseSource):
    @property
    def name(self) -> str:
        return "我的信息源"

    def fetch(self) -> list[Article]:
        # 你的抓取逻辑
        return [Article(title="...", url="...", source=self.name)]
```

然后在 `main.py` 的 `build_sources()` 中注册即可。

## ⚠️ 注意事项

- 各网站页面结构可能变化，爬虫选择器需定期检查维护
- 微信公众号抓取依赖搜狗微信搜索，有反爬限制，推荐配合 [WeRSS](https://werss.app/) 转 RSS 更稳定
- 翻译默认使用 Google 免费接口，高频使用可能被限制，建议切换百度翻译 API
- 请遵守各网站的 robots.txt 规范，建议每日仅运行 1-2 次

## 📄 License

[MIT](LICENSE)
