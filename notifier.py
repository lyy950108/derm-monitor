"""邮件推送模块"""

import logging
import os
import smtplib
from collections import OrderedDict
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from jinja2 import Environment, FileSystemLoader

from sources.base import Article

logger = logging.getLogger(__name__)


class EmailNotifier:
    """邮件推送"""

    # 分类显示顺序
    CATEGORY_ORDER = ["指南更新", "行业资讯", "微信公众号"]

    def __init__(self, config: dict):
        self.email_cfg = config.get("email", {})
        self.smtp_server = self.email_cfg.get("smtp_server", "")
        self.smtp_port = self.email_cfg.get("smtp_port", 465)
        self.use_ssl = self.email_cfg.get("use_ssl", True)
        self.sender = self.email_cfg.get("sender", "")
        self.password = self.email_cfg.get("password", "")
        self.recipients = self.email_cfg.get("recipients", [])
        self.subject_prefix = self.email_cfg.get("subject_prefix", "【皮肤科资讯】")

        # Jinja2 模板
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))

    def send(self, articles: List[Article]) -> bool:
        """发送邮件摘要"""
        if not articles:
            logger.info("没有新文章，跳过推送")
            return False

        if not self.sender or not self.password or not self.recipients:
            logger.error("邮件配置不完整，请检查 config.yaml")
            return False

        # 按分类分组 (保持顺序)
        categories = OrderedDict()
        for cat in self.CATEGORY_ORDER:
            cat_articles = [a for a in articles if a.category == cat]
            if cat_articles:
                categories[cat] = cat_articles

        # 未归类的放到最后
        categorized_articles = {a.unique_id for cat_articles in categories.values() for a in cat_articles}
        uncategorized = [a for a in articles if a.unique_id not in categorized_articles]
        if uncategorized:
            categories["其他"] = uncategorized

        # 渲染邮件模板
        template = self.jinja_env.get_template("email_template.html")
        html_content = template.render(
            date=datetime.now().strftime("%Y年%m月%d日 %A"),
            total_count=len(articles),
            categories=categories,
        )

        # 构建邮件
        today = datetime.now().strftime("%m/%d")
        subject = f"{self.subject_prefix}{today} 共{len(articles)}条新资讯"

        msg = MIMEMultipart("alternative")
        msg["From"] = self.sender
        msg["To"] = ", ".join(self.recipients)
        msg["Subject"] = subject

        # 纯文本备用
        text_content = self._build_text_fallback(articles, categories)
        msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        # 发送
        try:
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()

            server.login(self.sender, self.password)
            server.sendmail(self.sender, self.recipients, msg.as_string())
            server.quit()

            logger.info(f"邮件发送成功！共 {len(articles)} 篇文章，收件人: {self.recipients}")
            return True

        except Exception as e:
            logger.error(f"邮件发送失败: {e}", exc_info=True)
            return False

    def _build_text_fallback(self, articles: List[Article], categories: OrderedDict) -> str:
        """纯文本备用格式"""
        lines = [
            f"皮肤科资讯日报 — {datetime.now().strftime('%Y年%m月%d日')}",
            f"本期共 {len(articles)} 条新资讯",
            "=" * 50,
        ]
        for cat_name, cat_articles in categories.items():
            lines.append(f"\n▌{cat_name} ({len(cat_articles)})")
            lines.append("-" * 30)
            for i, a in enumerate(cat_articles, 1):
                title = a.title_zh or a.title
                lines.append(f"  {i}. {title}")
                if a.language == "en" and a.title_zh and a.title_zh != a.title:
                    lines.append(f"     原文: {a.title}")
                if a.url:
                    lines.append(f"     链接: {a.url}")
                lines.append("")

        lines.append("—— Derm Monitor 自动推送 ——")
        return "\n".join(lines)
