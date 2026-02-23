#!/usr/bin/env python3
"""
皮肤科信息聚合推送系统 — 主入口

使用方式:
    python main.py              # 运行一次抓取 + 推送
    python main.py --dry-run    # 仅抓取，不发送邮件 (调试用)
    python main.py --schedule   # 定时运行模式
"""

import argparse
import logging
import os
import sys
from datetime import datetime

import yaml

from sources import (
    AADSource,
    BADSource,
    ChineseDermSource,
    DermatologyTimesSource,
    HealioSource,
    YixuejieSource,
    WechatSogouSource,
)
from translator import Translator
from storage import Storage
from notifier import EmailNotifier

# ============ 日志配置 ============
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("DermMonitor")


def load_config(path: str = "config.yaml") -> dict:
    """加载配置文件"""
    if not os.path.exists(path):
        logger.error(
            f"配置文件 {path} 不存在！\n"
            f"请先复制 config.example.yaml 为 config.yaml 并填入你的配置：\n"
            f"  cp config.example.yaml config.yaml"
        )
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config


def build_sources(config: dict) -> list:
    """根据配置构建信息源列表"""
    sources_cfg = config.get("sources", {})
    sources = []

    # --- 指南来源 ---
    if sources_cfg.get("aad", {}).get("enabled", True):
        sources.append(AADSource(sources_cfg.get("aad", {}), config))

    if sources_cfg.get("bad", {}).get("enabled", True):
        sources.append(BADSource(sources_cfg.get("bad", {}), config))

    if sources_cfg.get("chinese_derm_society", {}).get("enabled", True):
        sources.append(ChineseDermSource(sources_cfg.get("chinese_derm_society", {}), config))

    # --- 行业媒体 ---
    if sources_cfg.get("dermatology_times", {}).get("enabled", True):
        sources.append(DermatologyTimesSource(sources_cfg.get("dermatology_times", {}), config))

    if sources_cfg.get("healio_dermatology", {}).get("enabled", True):
        sources.append(HealioSource(sources_cfg.get("healio_dermatology", {}), config))

    if sources_cfg.get("yixuejie", {}).get("enabled", True):
        sources.append(YixuejieSource(sources_cfg.get("yixuejie", {}), config))

    # --- 微信公众号 ---
    if sources_cfg.get("wechat", {}).get("enabled", True):
        sources.append(WechatSogouSource(sources_cfg.get("wechat", {}), config))

    return sources


def run(config: dict, dry_run: bool = False):
    """执行一次完整的 抓取 → 翻译 → 去重 → 推送 流程"""
    logger.info("=" * 60)
    logger.info(f"🩺 皮肤科信息聚合推送 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # 1. 构建信息源
    sources = build_sources(config)
    logger.info(f"已启用 {len(sources)} 个信息源")

    # 2. 抓取所有来源
    all_articles = []
    for source in sources:
        articles = source.safe_fetch()
        all_articles.extend(articles)

    logger.info(f"共抓取 {len(all_articles)} 篇文章")

    if not all_articles:
        logger.info("未抓取到任何文章，退出")
        return

    # 3. 去重
    storage = Storage(config)
    new_articles = storage.filter_new(all_articles)

    if not new_articles:
        logger.info("没有新文章需要推送")
        return

    # 4. 翻译英文标题
    translator = Translator(config.get("translation", {}))
    new_articles = translator.translate_articles(new_articles)

    # 5. 输出摘要
    logger.info(f"\n📋 本次新文章摘要 ({len(new_articles)} 篇):")
    for i, a in enumerate(new_articles, 1):
        display_title = a.title_zh or a.title
        logger.info(f"  {i}. [{a.category}] {display_title} — {a.source}")

    # 6. 推送
    if dry_run:
        logger.info("\n🔍 Dry-run 模式，跳过邮件推送")
    else:
        notifier = EmailNotifier(config)
        success = notifier.send(new_articles)
        if success:
            # 标记为已推送
            storage.mark_seen(new_articles)
            logger.info("✅ 推送完成!")
        else:
            logger.error("❌ 推送失败，文章未标记为已读，下次将重试")


def main():
    parser = argparse.ArgumentParser(description="皮肤科信息聚合推送系统")
    parser.add_argument(
        "--config", "-c",
        default="config.yaml",
        help="配置文件路径 (默认: config.yaml)"
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="仅抓取并显示，不发送邮件"
    )
    parser.add_argument(
        "--schedule", "-s",
        action="store_true",
        help="定时运行模式 (每天8:00执行)"
    )
    args = parser.parse_args()

    config = load_config(args.config)

    if args.schedule:
        import schedule
        import time

        logger.info("⏰ 进入定时运行模式，每天 08:00 执行")
        schedule.every().day.at("08:00").do(run, config=config, dry_run=False)

        # 启动时先运行一次
        run(config, dry_run=args.dry_run)

        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        run(config, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
