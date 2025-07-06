import random
import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
import uuid
import logging
import os
from .models import GeneratedAd

logger = logging.getLogger(__name__)

def generate_ai_ad(liked_post, products, campaign):
    """
    Generate AI-powered advertisement using Stable Diffusion
    """
    try:
        # Get API key from environment variables (more secure)
        api_key = os.getenv('STABILITY_AI_API_KEY', 'sk-br3KwIquR53EpVtJ8vXhhMKCTor2Ms45fVY7KVAvyQ4jL9hh')
        
        # Build the prompt
        prompt = build_prompt(liked_post, products, campaign)
        
        # Correct payload format for Stability AI API
        # Using form-data instead of JSON for the newer API
        random_seed = random.randint(0, 2**32 - 1)  # Generate a random seed between 0 and 2^32-1

        files = {
            'prompt': (None, prompt),
            'output_format': (None, 'png'),
            'aspect_ratio': (None, '1:1'),
            'seed': (None, str(random_seed)),  # Use random seed
            'style_preset': (None, 'photographic'),
        }
        
        # Optional parameters
        negative_prompt = "blurry, low quality, distorted, ugly, text, watermark, logo, signature"
        if negative_prompt:
            files['negative_prompt'] = (None, negative_prompt)
        
        logger.info(f"Generating AI ad with prompt: {prompt[:100]}...")
        
        # Use the correct endpoint
        api_url = "https://api.stability.ai/v2beta/stable-image/generate/core"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "image/*"  # Accept image response
        }
        
        response = requests.post(
            api_url,
            files=files,
            headers=headers,
            timeout=120
        )
        
        # Log the response for debugging
        logger.info(f"API Response Status: {response.status_code}")
        logger.info(f"API Response Headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            logger.error(f"API Error: {response.status_code}")
            logger.error(f"Response content: {response.text}")
            return None
        
        response.raise_for_status()
        
        # Check if response contains image data
        if response.content and len(response.content) > 0:
            # Generate ad copy
            ad_copy = generate_ad_copy(liked_post, products, campaign)
            
            # Save generated ad
            ad = GeneratedAd.objects.create(
                source_post=liked_post,
                campaign=campaign,
                ad_copy=ad_copy,
                platform='instagram',
                ai_parameters={
                    'prompt': prompt,
                    'negative_prompt': negative_prompt,
                    'api_endpoint': api_url,
                    'generation_timestamp': timezone.now().isoformat()
                },
                created_at=timezone.now()
            )
            
            # Save image
            image_file = save_image(response.content)
            if image_file:
                ad.image.save(f"generated_ad_{ad.id}.png", image_file, save=True)
            
            # Set products
            ad.products.set(products)
            
            logger.info(f"Successfully generated ad with ID: {ad.id}")
            return ad
        else:
            logger.error("Empty response from Stable Diffusion API")
            return None
            
    except requests.exceptions.Timeout:
        logger.error("Timeout error when calling Stable Diffusion API")
        return None
    except requests.exceptions.ConnectionError:
        logger.error("Connection error when calling Stable Diffusion API")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error from Stable Diffusion API: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response content: {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error generating AI ad: {e}")
        return None

def build_prompt(liked_post, products, campaign):
    """Build comprehensive prompt for Stable Diffusion"""
    
    # Safely extract product information
    product_names = [getattr(product, 'name', '') for product in products]
    product_categories = list(set([
        getattr(product, 'category', '') for product in products 
        if hasattr(product, 'category') and getattr(product, 'category', '')
    ]))
    
    # Get all features from selected products
    all_features = []
    for product in products:
        if hasattr(product, 'features') and product.features:
            if isinstance(product.features, list):
                all_features.extend(product.features)
            else:
                all_features.append(str(product.features))
    
    # Build feature string (limit to top 3 features)
    features_text = ", ".join(all_features[:3]) if all_features else "premium quality"
    
    # Safely get post description
    post_description = ""
    if hasattr(liked_post, 'description') and liked_post.description:
        post_description = liked_post.description[:100]  # Shorter for better results
    
    # Build a concise, effective prompt
    prompt_parts = []
    
    # Main subject
    if product_names:
        main_products = ", ".join(product_names[:2])  # Limit to 2 products
        prompt_parts.append(f"Professional product photography of {main_products}")
    else:
        prompt_parts.append("Professional product photography")
    
    # Product details
    if product_categories:
        prompt_parts.append(f"{product_categories[0]} product")
    
    # Key features
    prompt_parts.append(f"featuring {features_text}")
    
    # Visual style
    prompt_parts.extend([
        "high quality commercial photography",
        "studio lighting",
        "clean modern background",
        "professional composition",
        "vibrant colors",
        "social media ready"
    ])
    
    # Join with commas and keep under 1000 characters
    full_prompt = ", ".join(prompt_parts)
    
    # Truncate if too long
    if len(full_prompt) > 1000:
        full_prompt = full_prompt[:1000]
    
    return full_prompt

def generate_ad_copy(liked_post, products, campaign):
    """Generate compelling ad copy based on products and campaign"""
    
    if not products:
        return "Check out our amazing products!"
    
    try:
        # Get featured product
        featured_product = products[0]  # Use first product
        
        # Build ad copy components
        product_name = getattr(featured_product, 'name', 'Amazing Product')
        
        # Get features
        features = []
        if hasattr(featured_product, 'features') and featured_product.features:
            if isinstance(featured_product.features, list):
                features = featured_product.features[:2]  # Limit to 2 features
            else:
                features = [str(featured_product.features)]
        
        # Build pricing info
        pricing_info = ""
        selling_price = getattr(featured_product, 'selling_price', 0)
        discounted_price = getattr(featured_product, 'discounted_price', 0)
        discount_percentage = getattr(featured_product, 'discount_percentage', 0)
        
        if selling_price and discounted_price and discount_percentage:
            savings = selling_price - discounted_price
            pricing_info = f"💰 Special Offer: ${discounted_price:.2f} (Save {discount_percentage}%!)"
        elif selling_price:
            pricing_info = f"💰 Price: ${selling_price}"
        
        # Build final ad copy
        ad_copy_parts = [f"🔥 {product_name}"]
        
        if features:
            features_text = "✨ " + " | ".join(features)
            ad_copy_parts.append(features_text)
        
        if pricing_info:
            ad_copy_parts.append(pricing_info)
        
        ad_copy_parts.append("🛒 Shop now!")
        ad_copy_parts.append("#sale #trending #quality")
        
        return "\n\n".join(ad_copy_parts)
        
    except Exception as e:
        logger.error(f"Error generating ad copy: {e}")
        return f"🔥 Amazing {getattr(products[0], 'name', 'Product')} - Shop now! #sale #trending"

def save_image(image_content):
    """Save image content to a file"""
    try:
        if not image_content:
            logger.warning("No image content to save")
            return None
        
        # Generate unique filename
        filename = f"generated_ad_{uuid.uuid4().hex[:8]}.png"
        
        # Create ContentFile from image content
        image_file = ContentFile(image_content, name=filename)
        
        return image_file
        
    except Exception as e:
        logger.error(f"Error saving image: {e}")
        return None

# Alternative function using different API endpoint if core doesn't work
def generate_ai_ad_alternative(liked_post, products, campaign):
    """
    Alternative implementation using different Stability AI endpoint
    """
    try:
        api_key = os.getenv('STABILITY_AI_API_KEY', 'sk-br3KwIquR53EpVtJ8vXhhMKCTor2Ms45fVY7KVAvyQ4jL9hh')
        
        prompt = build_prompt(liked_post, products, campaign)
        
        # Try the ultra endpoint with JSON payload
        payload = {
            "prompt": prompt,
            "aspect_ratio": "1:1",
            "seed": 0,  # Changed from -1 to 0
            "output_format": "png"
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "image/*"
        }
        
        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/generate/ultra",
            json=payload,
            headers=headers,
            timeout=120
        )
        
        if response.status_code == 200 and response.content:
            # Same processing as above
            ad_copy = generate_ad_copy(liked_post, products, campaign)
            
            ad = GeneratedAd.objects.create(
                source_post=liked_post,
                campaign=campaign,
                ad_copy=ad_copy,
                platform='instagram',
                ai_parameters=payload,
                created_at=timezone.now()
            )
            
            image_file = save_image(response.content)
            if image_file:
                ad.image.save(f"generated_ad_{ad.id}.png", image_file, save=True)
            
            ad.products.set(products)
            
            return ad
        else:
            logger.error(f"Alternative API failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Alternative API error: {e}")
        return None