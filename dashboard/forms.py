from django import forms
from .models import BrandProduct, BrandCampaign, GeneratedAd

class AdCreationForm(forms.Form):
    campaign = forms.ModelChoiceField(
        queryset=BrandCampaign.objects.all(),
        empty_label="Select a campaign",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        })
    )
    
    products = forms.ModelMultipleChoiceField(
        queryset=BrandProduct.objects.none(),  # Start with empty queryset
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        # Extract custom parameters
        products_queryset = kwargs.pop('products_queryset', None)
        super().__init__(*args, **kwargs)
        
        # CRITICAL: Set queryset BEFORE any validation occurs
        if products_queryset is not None:
            self.fields['products'].queryset = products_queryset
        else:
            self.fields['products'].queryset = BrandProduct.objects.all().order_by('name')
        
        # Set initial queryset for campaigns
        self.fields['campaign'].queryset = BrandCampaign.objects.all().order_by('name')
    
    def clean_products(self):
        products = self.cleaned_data.get('products')
        if not products:
            raise forms.ValidationError("Please select at least one product.")
        if len(products) > 5:
            raise forms.ValidationError("Please select no more than 5 products.")
        
        # Additional validation: ensure all selected products are in the queryset
        valid_product_ids = set(self.fields['products'].queryset.values_list('id', flat=True))
        selected_product_ids = set(product.id for product in products)
        
        if not selected_product_ids.issubset(valid_product_ids):
            invalid_ids = selected_product_ids - valid_product_ids
            raise forms.ValidationError(f"Invalid product selections: {list(invalid_ids)}")
        
        return products