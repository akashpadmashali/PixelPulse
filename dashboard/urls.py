from django.urls import path
from .views import *

# Add these if you want to create them later
# from .views import (
#     GeneratedAdDetailView,
#     GeneratedAdDeleteView,
#     similar_products_api,
#     preview_ad_api,
# )

urlpatterns = [
    # Dashboard Home
    path('', dashboard_home, name='dashboard_home'),
    
    # Liked Posts Management
    path('liked-posts/', LikedPostListView.as_view(), name='liked_posts'),
    
    # Product Management
    path('products/', ProductListView.as_view(), name='products'),
    # Future product management URLs
    # path('products/create/', ProductCreateView.as_view(), name='product_create'),
    # path('products/<uuid:pk>/edit/', ProductUpdateView.as_view(), name='product_edit'),
    # path('products/<uuid:pk>/delete/', ProductDeleteView.as_view(), name='product_delete'),
    
    # Ad Generation Flow
    path('create-ad/<uuid:post_id>/', create_ad_from_post, name='create_ad'),
    
    # Generated Ads Management
    path('generated-ads/', GeneratedAdListView.as_view(), name='generated_ads'),
    # Future generated ads management URLs
    # path('generated-ads/<uuid:pk>/', GeneratedAdDetailView.as_view(), name='generated_ad_detail'),
    # path('generated-ads/<uuid:pk>/delete/', GeneratedAdDeleteView.as_view(), name='generated_ad_delete'),
    
    # Future API Endpoints (for AJAX/JS functionality)
    # path('api/similar-products/', similar_products_api, name='similar_products_api'),
    # path('api/preview-ad/', preview_ad_api, name='preview_ad_api'),
    path('regenerate/<int:ad_id>/', regenerate_ad_image, name='regenerate_ad_image'),
    path('generated-ads/<uuid:pk>/', AdDetailView.as_view(), name='ad_detail'),
]