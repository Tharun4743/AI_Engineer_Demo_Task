import asyncio
from typing import List
from src.core.http import http_client
from src.core.models import Product
from src.resolver.entity_resolver import entity_resolver
from src.storage.db import db_manager
from src.storage.dedup import deduplicator
from src.core.logging import logger

HF_SPACES_API = "https://huggingface.co/api/spaces?limit=1200"


class ProductsCrawler:
    """Collects AI products, tools, and demos from Hugging Face Spaces and directories."""

    def __init__(self, target_count: int = 1000):
        self.target_count = target_count

    async def crawl_hf_spaces(self) -> List[Product]:
        collected: List[Product] = []
        logger.info(f"Fetching AI products from Hugging Face Spaces ({HF_SPACES_API})...")

        try:
            data = await http_client.get_json(HF_SPACES_API)
            if not isinstance(data, list):
                logger.error("Hugging Face Spaces API did not return an array.")
                return collected

            for item in data:
                space_id = item.get("id")
                if not space_id:
                    continue

                product_url = f"https://huggingface.co/spaces/{space_id}"
                if not deduplicator.mark_seen(product_url):
                    continue

                # Parse author / name
                parts = space_id.split("/")
                author = parts[0] if len(parts) > 1 else ""
                raw_name = parts[-1].replace("-", " ").replace("_", " ").title()

                canonical_entity = None
                if author:
                    canonical_entity, _ = entity_resolver.resolve(
                        raw_name=author,
                        source_url=product_url,
                    )

                likes = int(item.get("likes", 0))
                sdk = item.get("sdk", "gradio")
                created_date = item.get("createdAt", "2024")

                desc = f"Interactive AI Application on Hugging Face Spaces by {author or 'Community'} using {sdk}. Likes: {likes}."

                product = Product(
                    name=raw_name,
                    canonical_name=canonical_entity or author or "Community AI",
                    product_url=product_url,
                    source_url=HF_SPACES_API,
                    description=desc,
                    category=sdk,
                    stars_or_likes=likes,
                    created_date=created_date,
                    raw_extracted_text=f"{raw_name} ({product_url})\n{desc}",
                )
                collected.append(product)
                db_manager.save_product(product)

                if len(collected) >= self.target_count:
                    break

        except Exception as e:
            logger.error(f"Error crawling HF Spaces products: {e}")

        return collected

    async def run(self) -> List[Product]:
        logger.info(f"Starting Products crawl (Target: >= {self.target_count} unique products)...")
        results = await self.crawl_hf_spaces()
        logger.info(f"Products crawl complete. Total collected: {len(results)}")
        return results


products_crawler = ProductsCrawler()
