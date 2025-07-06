# views.py - Fixed version

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView
from django.db import models
from django.contrib import messages
from django.core.files.base import ContentFile
from .models import LikedPost, BrandProduct, GeneratedAd, BrandCampaign
from .forms import AdCreationForm
from .ad_utils import generate_ai_ad as generate_ai_ad_with_image  # Import the AI function
import requests
from PIL import Image
import io
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def dashboard_home(request):
    return render(request, 'dashboard/home.html')

class LikedPostListView(ListView):
    model = LikedPost
    template_name = 'dashboard/liked_posts.html'
    context_object_name = 'liked_posts'
    paginate_by = 10

    def get_queryset(self):
        return LikedPost.objects.all().order_by('-created_at')

class ProductListView(ListView):
    model = BrandProduct
    template_name = 'dashboard/products.html'
    context_object_name = 'products'
    ordering = ['name']
    paginate_by = 10

class GeneratedAdListView(ListView):
    model = GeneratedAd
    template_name = 'dashboard/generated_ads.html'
    context_object_name = 'generated_ads'
    ordering = ['-created_at']
    paginate_by = 10
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        processed_ads = []
        for ad in context['generated_ads']:
            # Check if image exists in storage
            image_exists = False
            image_url = None
            if ad.image:
                try:
                    if ad.image.storage.exists(ad.image.name):
                        image_url = ad.image.url
                        image_exists = True
                except Exception as e:
                    logger.error(f"Error checking image for ad {ad.id}: {e}")
            
            processed_ads.append({
                'ad': ad,
                'image_exists': image_exists,
                'image_url': image_url,
                'products_list': list(ad.products.all()),
                'products_count': ad.products.count(),
            })
        
        context['processed_ads'] = processed_ads
        return context

def get_generated_ad_with_safe_image(ad_id):
    """
    Safely get GeneratedAd with proper image handling
    """
    try:
        ad = GeneratedAd.objects.get(id=ad_id)
        
        # Check if image exists and has a file
        if ad.image and hasattr(ad.image, 'url'):
            try:
                image_url = ad.image.url
                return ad, image_url
            except ValueError:
                logger.warning(f"Ad {ad_id} has image field but no file associated")
                return ad, None
        else:
            return ad, None
            
    except GeneratedAd.DoesNotExist:
        logger.error(f"GeneratedAd with id {ad_id} does not exist")
        return None, None

def create_ad_from_post(request, post_id):
    post = get_object_or_404(LikedPost, id=post_id)
    all_products = BrandProduct.objects.all()
    
    if request.method == 'POST':
        form = AdCreationForm(request.POST, products_queryset=all_products)
        
        if form.is_valid():
            try:
                selected_products = form.cleaned_data['products']
                campaign = form.cleaned_data['campaign']
                
                if not selected_products:
                    messages.error(request, "Please select at least one product.")
                    return render_ad_creation_form(request, post, all_products, form)
                
                # Generate the ad with timeout handling
                try:
                    generated_ad = generate_ai_ad_with_image(post, selected_products, campaign)
                except requests.exceptions.Timeout:
                    messages.error(request, "The image generation service timed out. Please try again.")
                    return render_ad_creation_form(request, post, all_products, form)
                except Exception as e:
                    logger.error(f"Ad generation error: {str(e)}", exc_info=True)
                    messages.error(request, "Failed to generate ad due to a technical error.")
                    return render_ad_creation_form(request, post, all_products, form)
                
                if generated_ad:
                    # Verify the image was actually saved
                    if not generated_ad.image or not generated_ad.image.storage.exists(generated_ad.image.name):
                        logger.error(f"Generated ad {generated_ad.id} has no valid image file")
                        messages.warning(request, "Ad created but image generation failed. Please try regenerating.")
                    else:
                        messages.success(request, "Ad generated successfully!")
                    return redirect('generated_ads')
                else:
                    messages.error(request, "Failed to generate ad. Please try again.")
                    
            except Exception as e:
                logger.error(f"Error in ad generation: {str(e)}", exc_info=True)
                messages.error(request, "An unexpected error occurred. Please try again.")
        else:
            for field, errors in form.errors.items():
                logger.error(f"Form error in {field}: {errors}")
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = AdCreationForm(products_queryset=all_products)
        similar_products = find_similar_products(post)
        if similar_products.exists():
            form.fields['products'].initial = list(similar_products[:3].values_list('id', flat=True))
    
    return render_ad_creation_form(request, post, all_products, form)

def find_similar_products(post):
    """
    Find products similar to the post content
    """
    similar_products = BrandProduct.objects.none()
    
    try:
        if hasattr(post, 'labels') and post.labels:
            # Handle labels whether it's a list or string
            labels = post.labels
            if isinstance(labels, str):
                labels = [labels]
            
            if labels:
                query = models.Q()
                for label in labels[:3]:  # Use first 3 labels
                    query |= models.Q(category__icontains=label)
                    query |= models.Q(sub_category__icontains=label)
                    query |= models.Q(name__icontains=label)
                
                similar_products = BrandProduct.objects.filter(query).distinct()
        
        # If no similar products found, get all products
        if not similar_products.exists():
            similar_products = BrandProduct.objects.all()
            logger.debug("No similar products found, using all products")
        else:
            logger.debug(f"Found {similar_products.count()} similar products")
            
    except Exception as e:
        logger.error(f"Error finding similar products: {e}")
        similar_products = BrandProduct.objects.all()
    
    return similar_products

def render_ad_creation_form(request, post, similar_products, form):
    """
    Render the ad creation form with all necessary context
    """
    # Create product choices for template display
    selected_product_ids = get_selected_product_ids(request.POST if request.method == 'POST' else None)
    if not selected_product_ids and hasattr(form.fields['products'], 'initial'):
        selected_product_ids = form.fields['products'].initial or []
    
    product_choices = create_product_choices(similar_products, selected_product_ids)
    
    return render(request, 'dashboard/ad_creation.html', {
        'post': post,
        'similar_products': similar_products,
        'form': form,
        'product_choices': product_choices,
    })

def get_selected_product_ids(post_data):
    """
    Extract and validate product IDs from POST data
    """
    if not post_data:
        return []
    
    selected_ids = []
    for pid in post_data.getlist('products'):
        try:
            selected_ids.append(int(pid))
        except (ValueError, TypeError):
            logger.warning(f"Invalid product ID received: {pid}")
    
    return selected_ids

def create_product_choices(products, selected_ids):
    """
    Create a list of product choices with selection status for the template
    """
    choices = []
    selected_ids = selected_ids or []
    
    for product in products:
        choices.append({
            'id': product.id,
            'name': product.name,
            'category': getattr(product, 'category', ''),
            'image_link': getattr(product, 'image_link', ''),
            'selling_price': getattr(product, 'selling_price', 0),
            'discounted_price': getattr(product, 'discounted_price', 0),
            'discount_percentage': getattr(product, 'discount_percentage', 0),
            'features': getattr(product, 'features', []),
            'is_selected': product.id in selected_ids
        })
    
    return choices

def verify_ad_image(ad):
    """Verify that an ad's image exists in storage"""
    if not ad.image:
        return False
    
    try:
        return ad.image.storage.exists(ad.image.name)
    except Exception as e:
        logger.error(f"Error verifying image for ad {ad.id}: {str(e)}")
        return False
    
def get_context_for_ad(ad):
    """Create a consistent context dictionary for an ad"""
    image_valid = False
    image_url = None
    
    if ad.image:
        try:
            if ad.image.storage.exists(ad.image.name):
                image_url = ad.image.url
                image_valid = True
        except Exception as e:
            logger.error(f"Error processing image for ad {ad.id}: {str(e)}")
    
    return {
        'ad': ad,
        'image_valid': image_valid,
        'image_url': image_url,
        'products': list(ad.products.all()),
        'products_count': ad.products.count(),
        'created_date': ad.created_at.strftime("%b %d, %Y"),
    }

def regenerate_ad_image(request, ad_id):
    """Regenerate the image for an existing ad"""
    ad = get_object_or_404(GeneratedAd, id=ad_id)
    
    try:
        # Regenerate using the original parameters
        new_ad = generate_ai_ad_with_image(
            ad.source_post,
            list(ad.products.all()),
            ad.campaign
        )
        
        if new_ad and new_ad.image:
            # Delete old image if it exists
            if ad.image and ad.image.storage.exists(ad.image.name):
                ad.image.delete()
            
            # Update the existing ad with new image
            ad.image.save(
                f"regenerated_{ad.image.name}",
                ContentFile(new_ad.image.read()),
                save=True
            )
            messages.success(request, "Ad image regenerated successfully!")
        else:
            messages.error(request, "Failed to regenerate image.")
    
    except Exception as e:
        logger.error(f"Error regenerating image for ad {ad_id}: {str(e)}")
        messages.error(request, "Error regenerating image. Please try again.")
    
    return redirect('generated_ads')

from django.views.generic import DetailView
class AdDetailView(DetailView):
    model = GeneratedAd
    template_name = 'dashboard/ad_detail.html'
    context_object_name = 'ad'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['has_permission'] = self.request.user.has_perm('dashboard.can_generate_ads')
        return context