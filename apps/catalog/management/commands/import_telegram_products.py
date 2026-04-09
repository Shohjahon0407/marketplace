import random
from pathlib import Path

from bs4 import BeautifulSoup
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalog.models.category import Category
from apps.catalog.models.product import Product, ProductCount, ProductImage
from common.enums.enums import Status


class Command(BaseCommand):
    help = "Import products from Telegram chat export HTML"

    def add_arguments(self, parser):
        parser.add_argument(
            "export_dir",
            type=str,
            help="Path to Telegram export directory",
        )
        parser.add_argument(
            "--quantity",
            type=int,
            default=20,
            help="Default stock quantity for all imported products",
        )
        parser.add_argument(
            "--category-ids",
            nargs="+",
            type=int,
            default=[1, 2],
            help="Category IDs to choose randomly from",
        )
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            help="Skip product if same name already exists in selected category",
        )

    def handle(self, *args, **options):
        export_dir = Path(options["export_dir"]).expanduser().resolve()
        default_quantity = options["quantity"]
        category_ids = options["category_ids"]
        skip_existing = options["skip_existing"]

        if not export_dir.exists() or not export_dir.is_dir():
            raise CommandError(f"Export papka topilmadi: {export_dir}")

        categories = list(Category.objects.filter(id__in=category_ids))
        if not categories:
            raise CommandError(f"Berilgan category id lar topilmadi: {category_ids}")

        html_files = sorted(export_dir.glob("messages*.html"))
        if not html_files:
            raise CommandError(f"{export_dir} ichida messages*.html topilmadi")

        created_count = 0
        skipped_count = 0
        seen_image_paths = set()

        for html_file in html_files:
            self.stdout.write(self.style.NOTICE(f"Parsing: {html_file.name}"))
            created, skipped, seen_image_paths = self._parse_html_file(
                html_file=html_file,
                export_dir=export_dir,
                categories=categories,
                quantity=default_quantity,
                skip_existing=skip_existing,
                seen_image_paths=seen_image_paths,
            )
            created_count += created
            skipped_count += skipped

        self.stdout.write(self.style.SUCCESS(
            f"Finished. Created: {created_count}, Skipped: {skipped_count}"
        ))

    def _parse_html_file(self, html_file, export_dir, categories, quantity, skip_existing, seen_image_paths):
        created_count = 0
        skipped_count = 0

        content = html_file.read_text(encoding="utf-8", errors="ignore")
        soup = BeautifulSoup(content, "html.parser")

        messages = soup.select("div.message")
        for message in messages:
            image_rel_path = self._extract_image_path(message)
            if not image_rel_path:
                continue

            if image_rel_path in seen_image_paths:
                skipped_count += 1
                continue

            image_path = (export_dir / image_rel_path).resolve()
            if not image_path.exists():
                self.stdout.write(self.style.WARNING(
                    f"Image topilmadi: {image_rel_path}"
                ))
                skipped_count += 1
                continue

            raw_text = self._extract_text(message)
            name, description = self._build_name_description(raw_text, image_path)

            if not name:
                skipped_count += 1
                continue

            category = random.choice(categories)

            if skip_existing:
                exists = Product.all_objects.filter(
                    name__iexact=name,
                    category=category,
                ).exists()
                if exists:
                    skipped_count += 1
                    continue

            try:
                with transaction.atomic():
                    product = Product.objects.create(
                        category=category,
                        name=name[:200],
                        description=description,
                        price=self._generate_price_from_text(raw_text),
                        discount_price=None,
                        status=Status.IN_STOCK if quantity > 0 else Status.OUT_OF_STOCK,
                    )

                    ProductCount.objects.create(
                        product=product,
                        stock=quantity,
                    )

                    with image_path.open("rb") as f:
                        ProductImage.objects.create(
                            product=product,
                            image=File(f, name=image_path.name),
                        )

                created_count += 1
                seen_image_paths.add(image_rel_path)
                self.stdout.write(self.style.SUCCESS(
                    f"Created: {product.name} | category={category.id}"
                ))

            except Exception as exc:
                skipped_count += 1
                self.stdout.write(self.style.ERROR(
                    f"Xato: {name} -> {exc}"
                ))

        return created_count, skipped_count, seen_image_paths

    def _extract_image_path(self, message):
        photo_link = message.select_one("a.photo_wrap")
        if photo_link and photo_link.get("href"):
            return photo_link.get("href").strip()

        photo_img = message.select_one("img.photo")
        if photo_img and photo_img.get("src"):
            return photo_img.get("src").strip()

        media_link = message.select_one(".media_wrap a")
        if media_link and media_link.get("href"):
            href = media_link.get("href").strip()
            if href.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                return href

        return None

    def _extract_text(self, message):
        text_node = message.select_one("div.text")
        if text_node:
            return " ".join(text_node.get_text("\n", strip=True).split())

        caption_node = message.select_one(".media_details")
        if caption_node:
            return " ".join(caption_node.get_text("\n", strip=True).split())

        return ""

    def _build_name_description(self, raw_text, image_path: Path):
        raw_text = (raw_text or "").strip()

        if not raw_text:
            fallback_name = image_path.stem.replace("_", " ").replace("-", " ").strip()
            return fallback_name[:200], ""

        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        if not lines:
            return raw_text[:200], ""

        first_line = lines[0]
        other_lines = lines[1:]

        words = first_line.split()
        if len(words) <= 6:
            name = first_line
            description = "\n".join(other_lines).strip()
        else:
            name = " ".join(words[:6])
            description = raw_text

        return name[:200], description[:1000]

    def _generate_price_from_text(self, raw_text):
        """
        Agar text ichida narx topilsa ishlatadi.
        Topilmasa random test price beradi.
        """
        import re

        if raw_text:
            match = re.search(r"(\d+[.,]?\d*)", raw_text)
            if match:
                value = match.group(1).replace(",", ".")
                try:
                    number = float(value)
                    if number > 0:
                        # Telegramdagi '4.8' kabi qiymat juda kichik bo'lishi mumkin,
                        # shuning uchun test uchun ko'paytiramiz
                        if number < 1000:
                            number = number * 10000
                        return round(number, 2)
                except ValueError:
                    pass

        return random.choice([
            12000,
            18000,
            25000,
            32000,
            45000,
            67000,
            89000,
        ])