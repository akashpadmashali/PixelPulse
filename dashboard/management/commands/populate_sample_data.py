from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from ...models import LikedPost, BrandProduct, ProductImage, BrandCampaign
import requests
from io import BytesIO
from django.core.files import File
import uuid

class Command(BaseCommand):
    help = 'Populates database with sample ads, products, and campaigns'

    def handle(self, *args, **kwargs):
        # Create test user
        user, _ = User.objects.get_or_create(
            username='testuser',
            defaults={'email': 'test@example.com'}
        )

        # Sample Liked Posts
        liked_posts = [
            {
                'image_url': 'https://images.unsplash.com/photo-1600185365483-26d7a4cc7519',
                'description': 'Trendy streetwear sneakers on urban background',
                'labels': ['sneakers', 'streetwear', 'urban', 'fashion']
            },
            {
                'image_url': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff',
                'description': 'Professional running shoes isolated on white',
                'labels': ['running', 'shoes', 'sports', 'performance']
            }
        ]

        for post_data in liked_posts:
            post = LikedPost.objects.create(
                user=user,
                email=user.email,
                image_url=post_data['image_url'],
                description=post_data['description'],
                labels=post_data['labels']
            )
            self.stdout.write(f'Created liked post: {post.id}')

        # Sample Products
        products = [
            {
                'name': 'Nike SB Dunk Low Pro',
                'category': 'Skateboarding Shoes',
                'description': 'Premium skate shoes with Zoom Air cushioning',
                'features': ['Zoom Air', 'Reinforced toe', 'Gum rubber sole'],
                'images': [
                    'https://static.nike.com/a/images/t_PDP_1280_v1/f_auto,q_auto:eco/skwgyqrbfzhu6uyeh0gg/dunk-low-pro-shoes-2k1nqD.png',
                    'https://static.nike.com/a/images/t_PDP_1280_v1/f_auto,q_auto:eco/aff2530b-fc8e-4b81-b8a1-5f8a9010f1a3/dunk-low-pro-shoes-2k1nqD.png'
                ]
            },
            {
                'name': 'Adidas Ultraboost Light',
                'category': 'Running Shoes',
                'description': 'Energy-returning running shoes with Primeknit+',
                'features': ['Boost midsole', 'Primeknit+', 'Continental rubber'],
                'images': [
                    'https://assets.adidas.com/images/h_840,f_auto,q_auto,fl_lossy,c_fill,g_auto/4505df81b1d248b392c1af8f00bd1e2a_9366/Ultraboost_Light_Shoes_Black_HP9207_01_standard.jpg',
                    'https://assets.adidas.com/images/h_840,f_auto,q_auto,fl_lossy,c_fill,g_auto/1a9e7a5b1a9d4b6c8d0baf8f00e5d1e2_9366/Ultraboost_Light_Shoes_Black_HP9207_42_detail.jpg'
                ]
            }
        ]

        for product_data in products:
            product = BrandProduct.objects.create(
                name=product_data['name'],
                category=product_data['category'],
                description=product_data['description'],
                features=product_data['features']
            )

            for i, img_url in enumerate(product_data['images']):
                response = requests.get(img_url)
                img_name = f"{product_data['name'].replace(' ', '_')}_{i}.jpg"
                
                img = ProductImage.objects.create(
                    product=product,
                    is_primary=(i == 0)
                )
                img.image.save(img_name, File(BytesIO(response.content)), save=True)
            
            self.stdout.write(f'Created product: {product.name}')

        # Sample Campaign
        campaign = BrandCampaign.objects.create(
            name='Summer 2023 Collection',
            brand_voice='Youthful, energetic, and rebellious',
            color_scheme={
                'primary': '#000000',
                'secondary': '#66B933',
                'text': '#FFFFFF'
            }
        )

        # Download and save logo
        logo_url = 'https://www.freepnglogos.com/uploads/adidas-logo-png-black-0.png'
        response = requests.get(logo_url)
        campaign.logo.save('campaign_logo.png', File(BytesIO(response.content)), save=True)

        self.stdout.write(f'Created campaign: {campaign.name}')
        self.stdout.write(self.style.SUCCESS('Successfully populated sample data!'))