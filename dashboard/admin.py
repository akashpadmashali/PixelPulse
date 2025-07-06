# admin.py
from django.contrib import admin
from .models import *

admin.site.register(LikedPost)
admin.site.register(BrandCampaign)
admin.site.register(BrandProduct)
admin.site.register(GeneratedAd)