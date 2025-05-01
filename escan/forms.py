

from django import forms
from .models import  Category, Product, CustomUser, ShippingAddress
from .supabase_helper import upload_image_to_supabase
import logging
from supabase import create_client, Client
from django.conf import settings
from django.contrib.auth.forms import UserChangeForm

logger = logging.getLogger(__name__)

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']

class ShippingAddressForm(forms.ModelForm):
    class Meta:
        model = ShippingAddress
        fields = ['phone_number', 'address', 'city', 'province', 'zipcode']
        
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser    
        fields = ['first_name', 'last_name', 'username', 'email', 'password', 'image_url']

    def save(self, commit=True):
        user = super().save(commit=False)

        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)  # Hash the password only if it's provided

        if commit:
            user.save()

        # Handle image upload to Supabase
        image_file = self.cleaned_data.get('image_url')
        if image_file:
            print("🔍 Image File Found:", image_file.name)
            print(f"🔍 Image File Size Before Reading: {image_file.size} bytes")

            if image_file.size > 0:
                image_file.seek(0)
                file_data = image_file.read()
                print(f"🔍 File Size Before Upload: {len(file_data)} bytes")

                supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_ROLE_KEY)
                bucket_name = "profile-images"
                file_name = f"{user.id}_{image_file.name}"

                try:
                    response = supabase.storage.from_(bucket_name).upload(file_name, file_data)

                    if hasattr(response, 'full_path') and response.full_path:
                        public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{response.full_path}"
                        user.image_url = public_url
                        user.save()
                        print("✅ Image Uploaded Successfully:", public_url)
                    else:
                        print("❌ Error Uploading Image:", response)

                except Exception as e:
                    print(f"⚠️ Exception in upload: {e}")
            else:
                print("❌ File has 0 size, cannot upload image")

        return user


class EditProfileForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username', 'email', 'password', 'image_url']

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # If password is changed, hash it
        if self.cleaned_data['password']:
            user.set_password(self.cleaned_data['password'])

        if commit:
            user.save()

        # Handle image upload to Supabase
        image_file = self.cleaned_data.get('image_url')
        if image_file:
            print("🔍 Image File Found:", image_file.name)  # Debugging output
            print(f"🔍 Image File Size Before Reading: {image_file.size} bytes")

            if image_file.size > 0:
                image_file.seek(0)
                file_data = image_file.read()
                print(f"🔍 File Size Before Upload: {len(file_data)} bytes")

                supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_ROLE_KEY)
                bucket_name = "profile-images"
                file_name = f"{user.id}_{image_file.name}"  # Use username for uniqueness

                try:
                    response = supabase.storage.from_(bucket_name).upload(file_name, file_data)

                    if hasattr(response, 'full_path') and response.full_path:
                        # Construct the public URL
                        public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{response.full_path}"
                        user.image_url = public_url
                        user.save()
                        print("✅ Image Uploaded Successfully:", public_url)
                    else:
                        print("❌ Error Uploading Image:", response)

                except Exception as e:
                    print(f"⚠️ Exception in upload: {e}")
            else:
                print("❌ File has 0 size, cannot upload image")

        return user


class ProductForm(forms.ModelForm):
 
    class Meta:
        model = Product
        fields = ['category', 'name', 'description', 'price', 'stock', 'image_url'] 
    
    def save(self, commit=True):
        product = super().save(commit=False)

        if commit:
            product.save()
        
        image_file = self.cleaned_data.get('image_url')
        if image_file:
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
