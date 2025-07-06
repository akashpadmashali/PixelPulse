import uuid
from django.db import models
from django.core.exceptions import ValidationError

def user_directory_path(instance, filename):
    return f'user_{instance.user.id}/{filename}'

class LikedPost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(default='john', max_length=255)  # Stores social media user ID
    email = models.EmailField(blank=True, null=True)  # Make optional
    image_url = models.URLField(max_length=1000)
    description = models.TextField()
    labels = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']  # For consistent pagination
    
    def __str__(self):
        return f"Post {self.id} by user {self.user_id}"

class BrandProduct(models.Model):
    name = models.CharField(max_length=200)
    # Fixed: Changed default from 1 to proper string values
    category = models.CharField(default='General', max_length=100)
    sub_category = models.CharField(default='Uncategorized', max_length=100)
    description = models.TextField()
    selling_price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    features = models.JSONField(default=list)
    image_link = models.URLField(
        default='https://th.bing.com/th?id=OPAC.AdlaqX2S9AaY%2bw474C474&w=592&h=550&o=5&dpr=1.3&pid=21.1',
        max_length=1000
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    @property
    def discounted_price(self):
        """Calculate the final price after discount"""
        if self.discount_percentage > 0:
            discount_amount = self.selling_price * (self.discount_percentage / 100)
            return self.selling_price - discount_amount
        return self.selling_price
    
    @property
    def savings_amount(self):
        """Calculate the savings amount"""
        if self.discount_percentage > 0:
            return self.selling_price * (self.discount_percentage / 100)
        return 0

    def clean(self):
        """Validate model data"""
        if self.discount_percentage < 0 or self.discount_percentage > 100:
            raise ValidationError('Discount percentage must be between 0 and 100.')
        if self.selling_price < 0:
            raise ValidationError('Selling price cannot be negative.')

class BrandCampaign(models.Model):
    name = models.CharField(max_length=200)
    brand_voice = models.TextField()
    color_scheme = models.JSONField(default=dict)
    font = models.FileField(upload_to='campaign_fonts/', null=True, blank=True)
    logo = models.ImageField(upload_to='campaign_logos/', null=True, blank=True)  # Made optional
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class GeneratedAd(models.Model):
    PLATFORM_CHOICES = [
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter'),
        ('linkedin', 'LinkedIn'),
        ('pinterest', 'Pinterest'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(BrandCampaign, on_delete=models.CASCADE)
    source_post = models.ForeignKey(LikedPost, on_delete=models.SET_NULL, null=True, blank=True)
    products = models.ManyToManyField(BrandProduct)
    ad_copy = models.TextField()
    image = models.ImageField(upload_to='generated_ads/', null=True, blank=True)  # Made optional
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default='instagram')
    ai_parameters = models.JSONField(default=dict)  # Stores SD prompts/settings
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Ad {self.id} for {self.campaign.name}"
    
    def clean(self):
        """Validate model data"""
        if self.platform not in dict(self.PLATFORM_CHOICES):
            raise ValidationError('Invalid platform choice.')