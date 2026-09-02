"""
Management command: backfill_embeddings

Generates OpenAI embeddings for all products that don't have one yet.
Batched, rate-limited, and resumable.

Usage:
    python manage.py backfill_embeddings
    python manage.py backfill_embeddings --batch-size=50 --dry-run
    python manage.py backfill_embeddings --force   # re-embed everything
"""

import time
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Generate OpenAI embeddings for products missing them (RazorHubSeller vectorization)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Number of products to embed per API call (max 2048). Default: 100.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-generate embeddings even for products that already have one.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making API calls.",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=0.5,
            help="Seconds to wait between batches (rate limiting). Default: 0.5.",
        )

    def handle(self, *args, **options):
        from products.models import Product

        api_key = settings.OPENAI_API_KEY
        if not api_key:
            self.stderr.write(self.style.ERROR(
                "OPENAI_API_KEY is not set. Add it to your .env file."
            ))
            return

        model = getattr(settings, "EMBEDDING_MODEL", "text-embedding-3-small")
        batch_size = options["batch_size"]
        force = options["force"]
        dry_run = options["dry_run"]
        delay = options["delay"]

        # Query products needing embeddings
        qs = Product.objects.filter(is_active=True)
        if not force:
            qs = qs.filter(embedding__isnull=True)

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS("All products already have embeddings. Nothing to do."))
            return

        self.stdout.write(f"Found {total} products to embed (model={model}, batch_size={batch_size})")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no API calls will be made."))
            for p in qs[:10]:
                self.stdout.write(f"  Would embed: [{p.id}] {p.name}")
            if total > 10:
                self.stdout.write(f"  ... and {total - 10} more")
            return

        # Initialize OpenAI client
        import openai
        client = openai.OpenAI(api_key=api_key)

        embedded_count = 0
        error_count = 0

        # Process in batches
        product_ids = list(qs.values_list("id", flat=True))

        for batch_start in range(0, len(product_ids), batch_size):
            batch_ids = product_ids[batch_start : batch_start + batch_size]
            products = list(Product.objects.filter(id__in=batch_ids))

            # Build embedding input: name + description + category + specs
            texts = []
            for p in products:
                parts = [p.name]
                if p.description:
                    parts.append(p.description[:500])  # Truncate long descriptions
                if p.category:
                    parts.append(f"Category: {p.category.name}")
                if p.brand:
                    parts.append(f"Brand: {p.brand.name}")
                if p.specifications:
                    parts.append(p.specifications[:300])
                texts.append(" | ".join(parts))

            try:
                response = client.embeddings.create(
                    model=model,
                    input=texts,
                )

                for product, embedding_data in zip(products, response.data):
                    product.embedding = embedding_data.embedding
                    product.ai_metadata = {
                        **(product.ai_metadata or {}),
                        "embedding_model": model,
                        "embedded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    }

                Product.objects.bulk_update(products, ["embedding", "ai_metadata"], batch_size=500)
                embedded_count += len(products)

                self.stdout.write(
                    f"  ✓ Batch {batch_start // batch_size + 1}: "
                    f"embedded {len(products)} products ({embedded_count}/{total})"
                )

            except Exception as e:
                error_count += len(products)
                self.stderr.write(self.style.ERROR(
                    f"  ✗ Batch {batch_start // batch_size + 1} failed: {e}"
                ))

            # Rate limiting
            if batch_start + batch_size < len(product_ids):
                time.sleep(delay)

        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Embedded: {embedded_count}, Errors: {error_count}"
        ))
