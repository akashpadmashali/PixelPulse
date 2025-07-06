import csv
from decimal import Decimal
from django.utils.dateparse import parse_datetime
from ...models import BrandProduct  # Replace 'your_app' with your actual app name

def import_products_from_csv(csv_path):
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                product = BrandProduct(
                    name=row['name'],
                    category=row['category'],
                    sub_category=row['sub_category'],
                    description=row['description'],
                    selling_price=Decimal(row['selling_price']),
                    discount_percentage=Decimal(row['discount_percentage'].replace('%', '')),
                    features=[feature.strip() for feature in row['features'].split(',')],
                    image_link=row['image_link']
                )
                product.save()
                print(f"✅ Imported: {product.name}")
            except Exception as e:
                print(f"❌ Error importing {row['name']}: {e}")

# Example usage
import_products_from_csv(r'D:\ad_gen\dashboard\management\commands\product.csv')
