import asyncio
import sys
import os
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.crawlers.startups import startups_crawler
from src.crawlers.products import products_crawler
from src.crawlers.papers import papers_crawler
from src.crawlers.news import news_crawler
from src.crawlers.jobs import jobs_crawler
from src.sinks.sheets import sheets_exporter
from src.core.http import http_client
from src.core.logging import logger
from src.storage.db import db_manager


async def run_phase1():
    """Phase 1: Foundational Intelligence Collection (Startups, Products, Papers)."""
    logger.info("=== Starting Execution: Phase 1 (Foundational Intelligence) ===")
    startups_task = startups_crawler.run()
    products_task = products_crawler.run()
    papers_task = papers_crawler.run()

    await asyncio.gather(startups_task, products_task, papers_task)
    counts = db_manager.get_counts()
    logger.info(f"Phase 1 Complete. Database Status: {counts}")


async def run_phase2():
    """Phase 2: Temporal Ingestion & Freshness Validation (News, Jobs <= 24h)."""
    logger.info("=== Starting Execution: Phase 2 (Real-Time Temporal Feeds) ===")
    news_task = news_crawler.run()
    jobs_task = jobs_crawler.run()

    await asyncio.gather(news_task, jobs_task)
    counts = db_manager.get_counts()
    logger.info(f"Phase 2 Complete. Database Status: {counts}")


async def run_export():
    """Export: Syncs data to Google Sheets (6 tabs) and writes CSV backups to output/."""
    logger.info("=== Starting Execution: Data Export ===")
    csv_files = sheets_exporter.export_csv_backups()
    for tab, path in csv_files.items():
        logger.info(f"Exported CSV backup for '{tab}' -> {path}")

    sheet_url = sheets_exporter.export_to_google_sheets()
    if sheet_url:
        logger.info(f"Google Sheets synchronization successful: {sheet_url}")
    else:
        logger.info("Google Sheets not synchronized (missing credentials or config). Local CSV backups ready.")


async def run_all():
    """Executes Phase 1, Phase 2, and Data Export sequentially."""
    logger.info("=== Starting Full Pipeline Execution ===")
    await run_phase1()
    await run_phase2()
    await run_export()
    logger.info("=== Full Pipeline Execution Finished Successfully ===")


def main():
    parser = argparse.ArgumentParser(description="Autonomous AI Competitive Intelligence Data Pipeline CLI")
    parser.add_argument(
        "command",
        choices=["phase1", "phase2", "all", "export"],
        help="Pipeline command to execute: phase1 | phase2 | all | export"
    )

    args = parser.parse_args()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        if args.command == "phase1":
            loop.run_until_complete(run_phase1())
        elif args.command == "phase2":
            loop.run_until_complete(run_phase2())
        elif args.command == "all":
            loop.run_until_complete(run_all())
        elif args.command == "export":
            loop.run_until_complete(run_export())
    finally:
        loop.run_until_complete(http_client.close())
        loop.close()


if __name__ == "__main__":
    main()
