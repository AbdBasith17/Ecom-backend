import json
from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
from products.models import Category, Product, ProductImage


class Command(BaseCommand):
    help = "Load categories and products from JSON file"

    def handle(self, *args, **kwargs):
        file_path = Path(settings.BASE_DIR) / 'products' / 'data' / 'products.json'

        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # -------------------
        # Categories
        # -------------------
        for cat in data['categories']:
            Category.objects.get_or_create(
                slug=cat['slug'],
                defaults={'name': cat['name']}
            )

        # -------------------
        # Products
        # -------------------
        for item in data['products']:
            category = Category.objects.get(slug=item['category'])

            product, created = Product.objects.get_or_create(
                title=item['title'],
                defaults={
                    'description': item['description'],
                    'category': category,
                    'price': item['price'],
                    'stock': item['stock'],
                    'sold': item.get('sold', 0),
                    'ml': item.get('ml'),
                    'is_active': item.get('is_active', True)
                }
            )

            if created:
                for img in item.get('images', []):
                    ProductImage.objects.create(
                        product=product,
                        image=img
                    )
