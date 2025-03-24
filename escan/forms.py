# from django import forms
# from .models import Category, Product
# from django.conf import settings
# import logging
# from .supabase_helper import upload_image_to_supabase

# logger = logging.getLogger(__name__)

# class CategoryForm(forms.ModelForm):
#     class Meta:
#         model = Category
#         fields = ['name', 'description']

# class ProductForm(forms.ModelForm):
#     image = forms.ImageField(required=True)  # Handle file input

#     class Meta:
#         model = Product
#         fields = ['name', 'description', 'price', 'stock', 'category'] 
    
#     def save(self, commit=True):
#         product = super().save(commit=False)
        
#         image_file = self.cleaned_data.get('image')  # Get image file
#         if image_file:
#             image_name = f"product_{product.name.replace(' ', '_')}.png"
#             image_url = upload_image_to_supabase(image_file, image_name)
#             if image_url:
#                 product.image_url = image_url  # Save image URL in DB

#         if commit:
#             product.save()
#         return product
from django import forms
from .models import  Category, Product
from .supabase_helper import upload_image_to_supabase
import logging

logger = logging.getLogger(__name__)

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']

class ProductForm(forms.ModelForm):
    image = forms.ImageField(required=True)  # Handle file input

    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'category'] 
    
    def save(self, commit=True):
        product = super().save(commit=False)  # Create instance but don't save yet
        
        image_file = self.cleaned_data.get('image')  # Get uploaded image file
        if image_file:
            image_name = f"product_{product.name.replace(' ', '_')}.png"
            image_url = upload_image_to_supabase(image_file, image_name)  # Upload to Supabase
            
            if image_url:
                product.image_url = image_url  # Save image URL in DB

        if commit:
            product.save()  # Now save the product with image URL
        return product
