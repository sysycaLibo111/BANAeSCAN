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
from supabase import create_client, Client
from django.conf import settings

logger = logging.getLogger(__name__)

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']

class ProductForm(forms.ModelForm):
    # image = forms.ImageField(required=True)

    class Meta:
        model = Product
        fields = ['category', 'name', 'description', 'price', 'stock', 'image_url'] 
    
    def save(self, commit=True):
        product = super().save(commit=False)

        if commit:
            product.save()
        
        image_file = self.cleaned_data.get('image_url')
        if image_file:
            # image_name = f"product_{product.name.replace(' ', '_')}.png"
            # image_url = upload_image_to_supabase(image_file, image_name)  # Upload to Supabase 
            # if image_url:
            #     product.image_url = image_url
        # if commit:
        #     product.save()  # Now save the product with image URL

            print("🔍 Image File Found:", image_file.name)  # Debugging output
            print(f"🔍 Image File Size Before Reading: {image_file.size} bytes")

            if image_file.size > 0:
                image_file.seek(0)
                file_data = image_file.read()
                print(f"🔍 File Size Before Upload: {len(file_data)} bytes")

                supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_ROLE_KEY)
                bucket_name = "product-images"
                file_name = f"{product.id}_{image_file.name}"

                try:
                    response = supabase.storage.from_(bucket_name).upload(file_name, file_data)

                    if hasattr(response, 'full_path') and response.full_path:
                        # Construct the public URL
                        public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{response.full_path}"
                        product.image_url = public_url
                        product.save()

                        print("✅ Image Uploaded Successfully:", public_url)
                    else:
                        print("❌ Error Uploading Image:", response)

                except Exception as e:
                    print(f"⚠️ Exception in upload: {e}")
            else:
                print("❌ File has 0 size, cannot upload image")

        return product
