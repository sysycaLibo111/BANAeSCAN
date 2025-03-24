
from django.shortcuts import render, redirect, get_object_or_404
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.hashers import check_password
from django.http import HttpResponse
from bananae.supabase_config import supabase 
from django.contrib.auth.hashers import make_password
import requests
from .models import CustomUser, Product, Category
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone
from escan.middleware import supabase_login_required
from django.urls import reverse
from .models import PasswordReset
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .forms import CategoryForm,ProductForm
from .supabase_helper import upload_image_to_supabase
import logging


logger = logging.getLogger(__name__)



User = get_user_model()

# Load environment variables
load_dotenv()
SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_API_KEY = settings.SUPABASE_API_KEY
SUPABASE_BUCKET = "product-images"
# SUPABASE_BUCKET = "uploads"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)
# Supabase Credentials


def user_logout(request):
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect('login')  # Redirect to login page after logout

# Landing Page
def landing_page(request):
    return render(request, 'escan/User/landing.html')

# Scan Signup & Login
def signup(request):
    return render(request, "escan/User/signup.html")


# Login
def login(request):
    return render(request, "escan/User/login.html")


# Supabase credentials

# Admin Log
def admin_login(request):  # ✅ Use login_view instead of login
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Authenticate user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Prevent Admin from logging in here
            if user.role == "User":
                messages.error(request, "Admins must log in through the admin portal.")
                return redirect("login")  # Redirect to admin login page

        if user is not None:
            # Ensure role is set to 'User' if it's empty
            if not user.role:
                user.role = "Admin"
                user.save()

            auth_login(request, user)  # ✅ Use Django's login function correctly
            # messages.success(request, f"Welcome, {user.username}! You are logged in as a {user.role}.")
            return redirect("admin_dashboard")  # Redirect to dashboard after login
            # return redirect(reverse("user_dashboard"))
        else:
            messages.error(request, "Invalid username or password.")
            return redirect("admin_login")

    return render(request, "escan/Admin/login.html")  

def admin_signup(request):
    return render(request, "escan/Admin/admin_dashboard.html")

# Admin Base of Side 
def base(request):
    return render(request, "base.html")
# User Base of Side 
def user_base(request):
    return render(request, "user_base.html")
def scan(request):
    return render(request, "escan/User/scan.html")

def admin_signup(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role", "Admin")  # Get the selected user role

        # Ensure the username or email is not already taken
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return redirect("admin_signup")

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return redirect("admin_signup")

        # Create the user
        user = CustomUser.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=password,  # Django automatically hashes it
            role=role  # Assign selected role
        )

        messages.success(request, "Account created successfully! Please log in.")
        return redirect("admin_login")  # Redirect to the login page after successful signup

    return render(request, "escan/Admin/admin_signup.html")

 
def login_view(request):  # ✅ Use login_view instead of login
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Authenticate user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Prevent Admin from logging in here
            if user.role == "Admin":
                messages.error(request, "Admins must log in through the admin portal.")
                return redirect("admin_login")  # Redirect to admin login page

            # Ensure role is set to 'User' if it's empty
            if not user.role:
                user.role = "User"
                user.save()

            auth_login(request, user)  # ✅ Use Django's login function correctly
            return redirect("user_dashboard")  # Redirect to user dashboard after login
        else:
            messages.error(request, "Invalid username or password.")
            return redirect("login")

    return render(request, "escan/User/login.html")

@supabase_login_required
def admin_dashboard(request):
    if not hasattr(request.user, "role") or request.user.role != "Admin":
        return redirect("user_dashboard")

    users = CustomUser.objects.filter(is_deleted=False)  # Fetch active users
    total_users = users.exclude(role="Admin").count()  


    return render(request, "escan/Admin/admin_dashboard.html", {
        "users": users,
        "total_users": total_users,  # Count only non-admin users
    })


# User list Views
@supabase_login_required
def user_table(request):
    if request.user.role != "Admin":
        return redirect("user_dashboard")  # Restrict non-admins

    users = CustomUser.objects.all()
    return render(request, "escan/Admin/user_list/user_table.html", {"users": users})

# Add User (Admin only)
@supabase_login_required
def add_user(request):
    if request.user.role != "Admin":
        return redirect("user_dashboard")

    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role", "User")  # Default to 'User'

    
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("user_table")

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("user_table")

        user = CustomUser.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=password,
            role=role,
        )
        user.save()
        messages.success(request, "User added successfully.")
        return redirect("user_table")

    return render(request, "escan/Admin/user_list/user_table.html")

# Edit User (Admin only)
@supabase_login_required
def edit_user(request, user_id):
    if request.user.role != "Admin":
        return redirect("login")

    user = get_object_or_404(CustomUser, id=user_id)

    if request.method == "POST":
        user.first_name = request.POST["first_name"]
        user.last_name = request.POST["last_name"]
        user.username = request.POST["username"]
        user.email = request.POST["email"]
        user.role = request.POST["role"]

        user.save()
        messages.success(request, "User updated successfully.")
        return redirect("user_table")  # Redirect to the main table

    return redirect("user_table")


@supabase_login_required
def delete_user(request, user_id):
    if request.user.role != "Admin":
        return redirect("login")

    user = get_object_or_404(CustomUser, id=user_id)
    user.soft_delete()  # Mark as deleted instead of actually deleting

    request.session["deleted_user"] = user.id  # Store in session for undo
    messages.success(request, "User deleted successfully. <a href='/undo_delete/'>Undo</a>", extra_tags="safe")

    return redirect("user_table")
    
@supabase_login_required
def undo_delete(request):
    user_id = request.session.get("deleted_user")
    if not user_id:
        messages.error(request, "No recent deletion to undo.")
        return redirect("user_table")

    user = get_object_or_404(CustomUser, id=user_id)
    user.restore()  # Restore user

    del request.session["deleted_user"]  # Remove from session
    messages.success(request, "User restored successfully.")

    return redirect("user_table")


# CATEGORY VIEWS
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'escan/Admin/Products/category_list.html', {'categories': categories})

@csrf_exempt
def add_category(request):
    if request.method == "POST":
        data = json.loads(request.body)
        category = Category.objects.create(name=data["name"], description=data["description"])
        return JsonResponse({"id": category.id, "name": category.name}, status=201)

@csrf_exempt
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == "POST":
        data = json.loads(request.body)
        category.name = data.get("name", category.name)
        category.description = data.get("description", category.description)
        category.save()
        return JsonResponse({"id": category.id, "name": category.name})

@csrf_exempt
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.delete()
    return JsonResponse({"message": "Category deleted successfully"})

# product

def product_list(request):
    products = Product.objects.filter(is_deleted=False)
    categories = Category.objects.all()
    return render(request, 'escan/Admin/Products/product_list.html', {'products': products, 'categories': categories})


# def add_product(request):
#     if request.method == 'POST':
#         print("🔍 Request Files:", request.FILES)
#         form = ProductForm(request.POST, request.FILES)  # Ensure image file is included

#         # print("🔍 Form cleaned_data:", form.data)
        
#         if form.is_valid():
#             print("🔍 Form is valid!")  # Debugging output

#             # Save the product, which includes image upload logic in the form's save method
#             form.save()  # The form's save method handles image upload to Supabase

#             # messages.success(request, "Product added successfully.")
#             return redirect('product_list')
#         else:
#             print("❌ Form is invalid!")  # Debugging output
#             # print("🔍 Form Errors:", form.errors)  # Print form errors to debug
#     else:
#         form = ProductForm()

#     products = Product.objects.all()  # Fetch all products to display in the table
#     return render(request, 'escan/Admin/Products/product_list.html', {'form': form, 'products': products})

# def add_product(request):
#     if request.method == 'POST':
#         form = ProductForm(request.POST, request.FILES)  # Ensure image file is included

#         if form.is_valid():
#             form.save()  # Image URL is generated & product is saved
            
#             return redirect('product_list')
#     else:
#         form = ProductForm()

#     products = Product.objects.all()  # Fetch all products to display
#     return render(request, 'escan/Admin/Products/product_list.html', {'form': form, 'products': products})

def add_product(request):
    if request.method == 'POST':
        print("🔍 Request Files:", request.FILES)
        form = ProductForm(request.POST, request.FILES)

        print("🔍 Form cleaned_data:", form.data)

        if form.is_valid():
            print("🔍 Form is valid!")
            form = form.save()
            
            # messages.success(request, "Product added successfully.")
            return redirect('product_list')
        else:
            print("❌ Form is invalid!")
            print("🔍 Form Errors:", form.errors)

    else:
        form = ProductForm()

    products = Product.objects.all()
    return render(request, 'escan/Admin/Products/product_list.html', {'form': form, 'products': products})

# def upload_product(request):
#     form = ProductForm()  # Ensure 'form' is initialized before conditions

#     if request.method == 'POST':
#         form = ProductForm(request.POST, request.FILES)
#         if form.is_valid():
#             form.save()  # The `save()` method in forms.py already handles image upload
#             return redirect('product_list')  # Redirect to product list

#     return render(request, 'escan/Admin/Products/upload_product.html', {'form': form})
    

def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_list')  # Fix: Remove .html from redirect
        else:
            print("❌ Form is invalid!")
            print("🔍 Form Errors:", form.errors)  # Debugging output
    else:
        form = ProductForm(instance=product)
    return render(request, 'escan/Admin/Products/edit_product.html', {'form': form, 'product': product})

def delete_image_from_supabase(file_name):
    """Deletes an image from Supabase Storage"""
    bucket_name = "product-images"

    try:
        response = supabase.storage.from_(bucket_name).remove([file_name])
        if response and isinstance(response, dict) and "error" in response:
            print("❌ Supabase Delete Error:", response["error"])
            return False
        print(f"✅ Image Deleted: {file_name}")
        return True

    except Exception as e:
        print("⚠️ Exception in delete:", e)
        return False


def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Delete image from Supabase storage
    if product.image_url:
        file_name = product.image_url.split("/")[-1]  # Extract file name
        delete_image_from_supabase(f"product_image/{file_name}")

    product.is_deleted = True  # Soft delete
    product.save()
    return redirect('product_list')


def restore_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.is_deleted = False  # Mark as not deleted
    product.save()
    return redirect('product_list')  # Redirect to the product list


@login_required
def user_dashboard(request):
    return render(request, "escan/User/user_dashboard.html")

# sign up for user
def signup_view(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role", "Admin")  # Get the selected user role

        # Ensure the username or email is not already taken
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return redirect("signup_view")

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return redirect("signup_view")

        # Create the user
        user = CustomUser.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=password,  # Django automatically hashes it
            role=role  # Assign selected role
        )

        messages.success(request, "Account created successfully! Please log in.")
        return redirect("admin_login")  # Redirect to the login page after successful signup

    return render(request, "escan/User/signup.html")



def upload_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)

        if form.is_valid():
            product = form.save(commit=False)  # Don't save yet

            image_file = request.FILES.get('image')  # Get the uploaded file
            if image_file:
                print(f"Uploading image: {image_file.name}")  # Debugging log
                image_name = f"product_{product.name.replace(' ', '_')}.png"
                image_url = upload_image_to_supabase(image_file, image_name)

                if image_url:
                    product.image_url = image_url  # Save image URL
                    print(f"Image uploaded: {image_url}")
                    logger.info(f"Image uploaded successfully: {image_url}")
                else:
                    logger.error("Image upload failed. Image URL is None.")

            product.save()  # Save product with image_url
            return redirect('product_list')

    else:
        form = ProductForm()

    return render(request, 'escan/Admin/Products/upload_product.html', {'form': form})
    
@login_required
def user_dashboard(request):
    return render(request, "escan/User/user_dashboard.html")

# sign up for user
def signup_view(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role", "User")  # Get the selected user role

        # Ensure the username or email is not already taken
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return redirect("signup_view")

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return redirect("signup_view")

        # Create the user
        user = CustomUser.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=password,  # Django automatically hashes it
            role=role  # Assign selected role
        )

        messages.success(request, "Account created successfully! Please log in.")
        return redirect("login")  # Redirect to the login page after successful signup

    return render(request, "escan/User/signup.html")



# def google_signup(request):
#     return redirect(google_auth_redirect())

# from django.http import JsonResponse

# def auth_callback(request):
#     """Handles authentication callback from Google Sign-In"""
#     return JsonResponse({"message": "Google Auth Callback Successful"})

# def google_signup(request):
#     """
#     Redirect users to Supabase Google authentication.
#     """
#     return redirect(f"{SUPABASE_URL}/auth/v1/authorize?provider=google&redirect_to=https://crvtfxinuvycxwgihree.supabase.co/auth/v1/callback")


# def confirm_email(request, uidb64, token):
#     try:
#          uid = urlsafe_base64_decode(uidb64)
#          user = get_user_model().objects.get(pk=uid)

#     if default_token_generator.check_token(user, token):
#         user.is_active = True
#         user.save()
#         messages.success(request, "Email confirmed! You can now log in.")
#         return redirect('login')
        
#     else:
#         messages.error(request, "The confirmation link is invalid or expired.")
#         return redirect('register')
    
#     except (TypeError, ValueError, OverflowError, User.DoesNotExist):
#         messages.error(request, "Invalid confirmation link.")
#         return redirect('register')

# def verification_email(request):
#     if not request.session.get('just_registered', False):
#         return redirect('login')

#     return render(request, 'verification_email.html')

def ForgotPassword(request):
    if request.method == "POST":
        email = request.POST.get('email')

        try:
            user = User.objects.get(email=email)

            new_password_reset = PasswordReset(user=user)
            new_password_reset.save()
            password_reset_url = reverse('reset-password', kwargs={'reset_id': new_password_reset.reset_id})

            full_password_reset_url = f'{request.scheme}://{request.get_host()}{password_reset_url}'

            context = {
                'user': user,
                'reset_url': full_password_reset_url,
            }

            email_body = render_to_string('escan/email/password_reset_email.html', context)

            email_message = EmailMessage(
                'Reset your password',
                email_body,
                settings.EMAIL_HOST_USER, 
                [email]
            )

            email_message.content_subtype = "html"

            email_message.fail_silently = True
            email_message.send()

            return redirect('password-reset-sent', reset_id=new_password_reset.reset_id)

        except User.DoesNotExist:
            messages.error(request, f"No user with email '{email}' found")
            return redirect('forgot-password')

    return render(request, 'escan/email/forgot_password.html')

def PasswordResetSent(request, reset_id):
    if PasswordReset.objects.filter(reset_id=reset_id).exists():
        return render(request, 'escan/email/password_reset_sent.html')
    else:
        messages.error(request, 'Invalid reset id')
        return redirect('forgot-password')


def ResetPassword(request, reset_id):
    try:
        reset_entry = PasswordReset.objects.get(reset_id=reset_id)
        user = reset_entry.user

        if request.method == "POST":
            new_password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')

            if new_password == confirm_password:
                user.password = make_password(new_password)  # ✅ Hash password before saving
                user.save()

                messages.success(request, "Password reset successful! You can now log in.")
                return redirect('login')
            else:
                messages.error(request, "Passwords do not match!")

        return render(request, 'escan/email/reset_password.html', {'reset_id': reset_id})

    except PasswordReset.DoesNotExist:
        messages.error(request, 'Invalid reset link.')
        return redirect('forgot-password')


