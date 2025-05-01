
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
from .models import CustomUser,Customer, Product, Category, Order, Cart, Cartitems
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
from .forms import CategoryForm, ProductForm, UserProfileForm, EditProfileForm, MessageForm
from .supabase_helper import upload_image_to_supabase
import logging
import io
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from django.templatetags.static import static
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
from django.contrib.staticfiles import finders  # For finding static files
from .models import Thread, Message
from django.db.models import OuterRef, Subquery, Max
from .models import DetectionRecord
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
from django.shortcuts import render
from .forms import ImageUploadForm
import torchvision.models as models
import torch.serialization

# Track last action (undo support)
last_action = {}



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
    return render(request, 'landing.html')

# Scan Signup & Login
def signup(request):
    return render(request, "escan/User/signup.html")


# Login
def login(request):
    return render(request, "escan/login.html")


# Supabase credentials
@login_required
def update_profile(request):
    user = request.user  # Get the currently logged-in user

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=user)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')

            # Check for duplicate username or email from other users
            if CustomUser.objects.exclude(id=user.id).filter(username=username).exists():
                messages.error(request, "Username already taken by another user.")
                return redirect("admin_dashboard")

            if CustomUser.objects.exclude(id=user.id).filter(email=email).exists():
                messages.error(request, "Email already registered with another account.")
                return redirect("admin_dashboard")

            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("admin_dashboard")
        else:
            messages.error(request, "Form is invalid. Please correct the errors.")
    else:
        form =  UserProfileForm(instance=user)

    return render(request, "escan/Admin/admin_dashboard.html", {'form': form})
   
    
# User Base of Side 
def user_base(request):
    return render(request, "user_base.html")

def scan(request):
    return render(request, "escan/User/Scan/scan.html")

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

 
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Authenticate user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Log the user in BEFORE redirecting
            auth_login(request, user)

            # Ensure role is set if it's not set
            if not user.role:
                user.role = "User"
                user.save()

            # Redirect based on role
            if user.role == "Admin":
                return redirect("admin_dashboard")
            else:
                return redirect("user_dashboard")
        else:
            messages.error(request, "Invalid username or password.")
            return redirect("login")

    return render(request, "login.html")


@supabase_login_required
def admin_dashboard(request):
    if not hasattr(request.user, "role") or request.user.role != "Admin":
        return redirect("user_dashboard")

    users = CustomUser.objects.filter(is_deleted=False)  # Fetch active users
    customer = Customer.objects.all()
    total_users = users.exclude(role="Admin").count()  
    total_customer = customer.count()  


    return render(request, "escan/Admin/admin_dashboard.html", {
        "users": users,
        "total_users": total_users,  # Count only non-admin users
        "customer":customer,
        "total_customer":total_customer,
    })


# User list Views
@supabase_login_required
def user_table(request):
    if request.user.role != "Admin":
        return redirect("user_dashboard")  # Restrict non-admins

    users = CustomUser.objects.all()
    userss= users.exclude(role="Admin").order_by("first_name") 
    return render(request, "escan/Admin/user_list/user_table.html", {"userss": userss})
@supabase_login_required
def add_user(request):
    if request.user.role != "Admin":
        return redirect("user_dashboard")

    global last_action

    if request.method == "POST":
        print("🔍 Request Files:", request.FILES)
        form = UserProfileForm(request.POST, request.FILES)
        print("🔍 Form data:", form.data)

        if form.is_valid():
            user = form.cleaned_data.get('username')

            if CustomUser.objects.filter(username=user).exists():
                messages.error(request, "User already exists. Duplicate entries are not allowed.")
            else:
                form = form.save()
                messages.success(request, "User added successfully.")
                last_action = {'type': 'add', 'user_id': user.id}
                return redirect('user_table')
        else:
            messages.error(request, "Form is invalid. Please correct the errors.")
    else:
        form = UserProfileForm()

    users = CustomUser.objects.all()
    return render(request, 'escan/Admin/user_list/user_table.html', {'form': form, 'users': users})

@supabase_login_required
def edit_user(request, user_id):
    if request.user.role != "Admin":
        return redirect("user_dashboard")

    user = get_object_or_404(CustomUser, id=user_id)

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=user)

        if form.is_valid():
            user_name = form.cleaned_data.get('username')

            # Check if the username already exists (except for the current user)
            if CustomUser.objects.exclude(id=user_id).filter(username=user_name).exists():
                messages.error(request, "Username already exists. Please choose a different one.")
                return redirect('user_table')  # Prevent saving if a duplicate exists

            # Save the form data (user profile)
            form.save()

            # Optionally, track last action in a model or in session data
            # last_action = {'type': 'edit', 'user_id': user.id}

            messages.success(request, "User updated successfully.")
            return redirect('user_table')  # Redirect after successful update

        else:
            messages.error(request, "Form is invalid. Please correct the errors.")

    else:
        form = UserProfileForm(instance=user)

    return render(request, 'escan/Admin/user_list/user_table.html', {'form': form, 'user': user})


@supabase_login_required
def delete_user(request, user_id):
    if request.user.role != "Admin":
        return redirect("login")
    
    user = get_object_or_404(CustomUser, id=user_id)  # Fixed spacing and typo
    user.soft_delete()  # Assuming you have a soft delete method
    
    request.session["deleted_user"] = user.id  # Store in session for undo
    request.session["last_action"] = {"type": "delete", "user_id": user.id}
    
    messages.success(request, "User deleted successfully. <a href='/undo_delete/'>Undo</a>", extra_tags="safe")
    return redirect("user_table")


@supabase_login_required
def undo_last_action_user(request):
    global last_action
    if last_action:
        if last_action['type'] == 'delete':
            user = last_action['user']
            user.save()
            messages.success(request, "Undo successful. User restored.")
        elif last_action['type'] == 'add':
            CustomUser.objects.filter(id=last_action['user_id']).delete()
            messages.success(request, "Undo add successful.")
        elif last_action['type'] == 'edit':
            previous_data = last_action['previous_data']
            user = CustomUser.objects.get(id=last_action['user_id'])
            
            # Restore previous data for user
            user.first_name = previous_data['first_name']
            user.last_name = previous_data['last_name']
            user.username = previous_data['username']
            user.email = previous_data['email']
            
            # Only update the password if it was modified
            if previous_data['password']:
                user.set_password(previous_data['password'])
            
            user.image_url = previous_data['image_url']
            user.role = previous_data['role']  # Assuming role is a field of CustomUser
            user.save()
            messages.success(request, "Undo edit successful.")
        
        last_action = {}
    return redirect('user_table')

@supabase_login_required
def search_users(request):
    query = request.GET.get('query', '').strip()

    if query:
        users = CustomUser.objects.filter(first_name__icontains=query).union(
            CustomUser.objects.filter(last_name__icontains=query),
            CustomUser.objects.filter(username__icontains=query),
            CustomUser.objects.filter(email__icontains=query)
        )
    else:
        users = CustomUser.objects.none()

    results = [
        {
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'date_joined': u.date_joined.strftime('%Y-%m-%d'),
            'is_active': u.is_active,
            'role': u.role,
            'image_url': u.image_url.url if u.image_url else None # Supabase URL is already a string
        }
        for u in users
    ]
    return JsonResponse({'results':results})

def user_print(request):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)

    elements = []
    styles = getSampleStyleSheet()

    wrap_style = ParagraphStyle(
        name='WrapStyle',
        parent=styles['Normal'],
        fontSize=12,
        leading=12,
        alignment=0,
    )

    # === LOGO IMAGE ===
    logo_path = finders.find("img/PrintLogo.jpg")
    if logo_path and os.path.exists(logo_path):
        logo = Image(logo_path, width=60, height=60)
    else:
        logo = Spacer(1, 60)

    title = Paragraph("<b>BANAe-SCAN STORE USER LIST</b>", styles['Title'])

    header = Table([[logo, title]], colWidths=[70, 450])
    header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
    ]))
    elements.append(header)
    elements.append(Spacer(1, 12))

    date = Paragraph(datetime.now().strftime("%B %d, %Y — %I:%M %p"), styles['Normal'])
    elements.append(date)
    elements.append(Spacer(1, 12))

    # Table headers
    data = [['First Name', 'Last Name', 'Username', 'Email', 'Image','Date Joined', 'Is Active', 'Role']]

    users = CustomUser .objects.exclude(role='Admin')

    for user in users:
        # === Download product image from URL ===
        try:
            response = requests.get(user.image_url)
            if response.status_code == 200:
                img_buffer = io.BytesIO(response.content)
                user_img = Image(img_buffer, width=50, height=50)
            else:
                prod_img = Paragraph("No Image", wrap_style)
        except Exception as e:
            user_img = Paragraph("No Image", wrap_style)

        # Append row
        data.append([
            Paragraph(user.first_name, wrap_style),
            Paragraph(user.last_name, wrap_style),
            Paragraph(user.username, wrap_style),
            Paragraph(user.email,wrap_style),
            user_img,
            Paragraph(user.date_joined.strftime('%Y-%m-%d'), wrap_style),
            Paragraph("Active" if user.is_active else "Inactive", wrap_style),
            Paragraph(user.role, wrap_style),
            
        ])

    colWidths = [
        1.2* 72,  
        1.2* 72, 
        1.2* 72, 
        1.5* 72,  
        1.2 * 72,  
        1.5 * 72,  
        0.8 * 72,  
        1 * 72,  
    ]

    table = Table(data, colWidths=colWidths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))

    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    return HttpResponse(buffer, content_type='application/pdf', headers={
        'Content-Disposition': 'attachment; filename="user_list.pdf"'
    })

# Customer list Views
@supabase_login_required
# def customer_table(request):
#     if request.user.role != "Admin":
#         return redirect("user_dashboard")  # Restrict non-admins

#     customer = Customer.objects.all()
#     user = CustomUser.objects.all()
#     return render(request, "escan/Admin/E-commerce/customer_list.html", {"customer": customer, 'user': user})
def customer_table(request):
    customers = Customer.objects.select_related('user')  # Join with CustomUser
    # total_sales = sum(customer.total_spent for customer in customers)
    return render(request, 'escan/Admin/E-commerce/customer_list.html', {'customers': customers, })

# def search_customer(request):
#     query = request.GET.get('query', '').strip()
#     if query:  # Ensure query is not empty
#         products = Product.objects.filter(
#             name__icontains=query  # Search by name (case-insensitive)
#         ).union(
#             Product.objects.filter(category__name__icontains=query)  # Search by category (case-insensitive)
#         )
#     else:
#         products = Product.objects.none()  # Return empty result if query is empty

#     results = [
#         {
#             'id': p.id,
#             'name': p.name,
#             'category': p.category.name,
#             'description': p.description,
#             'price': p.price,
#             'stock': p.stock,
#             'image_url': p.image_url.url if p.image_url else None
#         }
#         for p in products
#     ]
#     return JsonResponse({'results': results})

# CATEGORY VIEWS
def category_list(request):
    categories = Category.objects.all().order_by("name")
    return render(request, 'escan/Admin/E-commerce/category_list.html', {'categories': categories})

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
    products = Product.objects.filter(is_deleted=False).order_by("category_id")
    categories = Category.objects.all()
    return render(request, 'escan/Admin/E-commerce/product_list.html', {'products': products, 'categories': categories})

def add_product(request):
    global last_action
    if request.method == 'POST':
        print("🔍 Request Files:", request.FILES)
        form = ProductForm(request.POST, request.FILES)

        print("🔍 Form cleaned_data:", form.data)

        if form.is_valid():
            product = form.cleaned_data.get('name')

            if Product.objects.filter(name=product).exists():
                messages.error(request, "Product already exists. Duplicate entries are not allowed.")

            else:
                # print("🔍 Form is valid!")
                form = form.save()
                messages.success(request, "Product added successfully.")
                return redirect('product_list')
                # print("❌ Form is invalid!")
                # print("🔍 Form Errors:", form.errors)
        else:
            messages.error(request, "Form is invalid. Please correct the errors.")

    else:
        form = ProductForm()
        
    last_action = {'type': 'add', 'product_id': product.id}
    products = Product.objects.all()
    return render(request, 'escan/Admin/E-commerce/product_list.html', {'form': form, 'products': products})

def edit_product(request, product_id):
    global last_action
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)

        if form.is_valid():
            product_name = form.cleaned_data.get('name')

            # Check if another product with the same name exists
            if Product.objects.exclude(id=product_id).filter(name=product_name).exists():
                messages.error(request, "Product with this name already exists. Please use a different name.")
                return redirect('product_list')  # Prevents saving if a duplicate exists

            form.save()  # Save only if no duplicate is found
            messages.success(request, "Product updated successfully.")
            return redirect('product_list')

        else:
            messages.error(request, "Form is invalid. Please correct the errors.")

    else:
        form = ProductForm(instance=product)

    last_action = {'type': 'edit', 'product_id': product.id}
    return render(request, 'escan/Admin/E-commerce/product_list.html', {'form': form, 'product': product})


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
    global last_action
    product = get_object_or_404(Product, id=product_id)
    last_action = {'type': 'delete', 'product': product}
    product.delete()
    messages.success(request, "Product deleted successfully.")
    return redirect('product_list')

def undo_last_action(request):
    global last_action
    if last_action:
        if last_action['type'] == 'delete':
            product = last_action['product']
            product.save()
            messages.success(request, "Undo successful. Product restored.")
        elif last_action['type'] == 'add':
            Product.objects.filter(id=last_action['product_id']).delete()
            messages.success(request, "Undo add successful.")
        elif last_action['type'] == 'edit':
            previous_data = last_action['previous_data']
            product = Product.objects.get(id=last_action['product_id'])
            product.name = previous_data['name']
            product.category = Category.objects.get(id=previous_data['category'])
            product.description = previous_data['description']
            product.price = previous_data['price']
            product.stock = previous_data['stock']
            product.image_url = previous_data['image_url']
            product.save()
            messages.success(request, "Undo edit successful.")
        last_action = {}
    return redirect('product_list')


def search_products(request):
    query = request.GET.get('query', '').strip()
    if query:  # Ensure query is not empty
        products = Product.objects.filter(
            name__icontains=query  # Search by name (case-insensitive)
        ).union(
            Product.objects.filter(category__name__icontains=query)  # Search by category (case-insensitive)
        )
    else:
        products = Product.objects.none()  # Return empty result if query is empty

    results = [
        {
            'id': p.id,
            'name': p.name,
            'category': p.category.name,
            'description': p.description,
            'price': p.price,
            'stock': p.stock,
            'image_url': p.image_url.url if p.image_url else None
        }
        for p in products
    ]
    return JsonResponse({'results': results})

def product_print(request):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)

    elements = []
    styles = getSampleStyleSheet()

    wrap_style = ParagraphStyle(
        name='WrapStyle',
        parent=styles['Normal'],
        fontSize=12,
        leading=12,
        alignment=0,
    )

    # === LOGO IMAGE ===
    logo_path = finders.find("img/PrintLogo.jpg")
    if logo_path and os.path.exists(logo_path):
        logo = Image(logo_path, width=60, height=60)
    else:
        logo = Spacer(1, 60)

    title = Paragraph("<b>BANAe-SCAN STORE PRODUCT LIST</b>", styles['Title'])

    header = Table([[logo, title]], colWidths=[70, 450])
    header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
    ]))
    elements.append(header)
    elements.append(Spacer(1, 12))

    date = Paragraph(datetime.now().strftime("%B %d, %Y — %I:%M %p"), styles['Normal'])
    elements.append(date)
    elements.append(Spacer(1, 12))

    # Table headers
    data = [['Name', 'Category', 'Description', 'Price', 'Stock', 'Image']]

    products = Product.objects.all()

    for product in products:
        # === Download product image from URL ===
        try:
            response = requests.get(product.image_url)
            if response.status_code == 200:
                img_buffer = io.BytesIO(response.content)
                prod_img = Image(img_buffer, width=50, height=50)
            else:
                prod_img = Paragraph("No Image", wrap_style)
        except Exception as e:
            prod_img = Paragraph("No Image", wrap_style)

        # Append row
        data.append([
            Paragraph(product.name, wrap_style),
            Paragraph(product.category.name, wrap_style),
            Paragraph(product.description, wrap_style),
            Paragraph(str(product.price), wrap_style),
            Paragraph(str(product.stock), wrap_style),
            prod_img,
        ])

    colWidths = [
        1.5 * 72,  # Name
        1.2 * 72,  # Category
        3.5 * 72,  # Description
        1.0 * 72,  # Price
        0.8 * 72,  # Stock
        1.2 * 72,  # Image
    ]

    table = Table(data, colWidths=colWidths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))

    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    return HttpResponse(buffer, content_type='application/pdf', headers={
        'Content-Disposition': 'attachment; filename="product_list.pdf"'
    })

# Oders

@supabase_login_required
def orders_part(request):
    if request.user.role != "Admin":
        return redirect("user_dashboard")  # Restrict non-admins

    orders = Order.objects.all()
    return render(request, "escan/Admin/E-commerce/orders_part.html", {"orders": orders})

# Graphs
def user_graph_view(request):
    # Fetch users with the role 'User '
    users = CustomUser .objects.filter(role='User ').values('first_name', 'date_joined')
    
    # Convert the queryset to a list of dictionaries
    user_data = [{'first_name': user['first_name'], 'date_joined': user['date_joined']} for user in users]
    
    return render(request, 'escan/Admin/E-commerce/product_list.html', {'users': user_data}) 


def signup_view(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES)  # Use the form to handle POST data

        if form.is_valid():
            # Check if username or email already exists
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']

            if CustomUser .objects.filter(username=username).exists():
                messages.error(request, "Username is already taken.")
                return redirect("signup_view")

            if CustomUser .objects.filter(email=email).exists():
                messages.error(request, "Email is already registered.")
                return redirect("signup_view")

            # Save the user
            form.save()
            messages.success(request, "Account created successfully! Please log in.")
            return redirect("login")  # Redirect to the login page after successful signup
        else:
            messages.error(request, "Form is invalid. Please correct the errors.")

    else:
        form = UserProfileForm()  # Create an empty form instance

    return render(request, "signup.html", {'form': form})

@login_required
def update_userprofile(request):
    user = request.user  # Get the currently logged-in user

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=user)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')

            # Check for duplicate username or email from other users
            if CustomUser.objects.exclude(id=user.id).filter(username=username).exists():
                messages.error(request, "Username already taken by another user.")
                return redirect("user_dashboard")

            if CustomUser.objects.exclude(id=user.id).filter(email=email).exists():
                messages.error(request, "Email already registered with another account.")
                return redirect("user_dashboard")

            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("user_dashboard")
        else:
            messages.error(request, "Form is invalid. Please correct the errors.")
    else:
        form =  UserProfileForm(instance=user)

    return render(request, "escan/User/user_dashboard.html", {'form': form})


# #user E-commerce side
@login_required
def user_product_list(request):
    product_list = Product.objects.filter(is_deleted=False).order_by("name")
    print(f"Retrieved products: {product_list}")  
    categories = Category.objects.all()
    paginator = Paginator(product_list, 10)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    return render(request, 'escan/User/user_dashboard.html', {
        'products': products,
        'categories': categories
    })


@login_required
def user_dashboard(request):
    customer, created = Customer.objects.get_or_create(user=request.user)
    cart, created = Cart.objects.get_or_create(customer=customer, completed=False)
    products = Product.objects.filter(is_deleted=False)
    unread_messages = Message.objects.filter(receiver=request.user, is_read=False).select_related('sender', 'thread')
    return render(request, 'escan/User/user_dashboard.html', {'products': products, 'cart': cart, 'unread_message': unread_messages})

@login_required
def update_item(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    
    customer = request.user.customer
    product = Product.objects.get(id=productId)
    cart, created = Cart.objects.get_or_create(customer=customer, completed=False)
    cart_item, created = cart.cartitems_set.get_or_create(product=product)

    if action == 'add':
        cart_item.quantity += 1
        cart_item.save()
    
    # Return the updated cart item count
    cart_item_count = cart.get_itemtotal()  # Use the method to get the total count
    return JsonResponse({'cartItemCount': cart_item_count}, safe=False)

def cart(request):
    if request.user.is_authenticated:
        customer, created = Customer.objects.get_or_create(user=request.user)
        cart, created = Cart.objects.get_or_create(customer = customer, completed = False)
        cartitems = cart.cartitems_set.all()
    else:
        cartitems = []
        cart = {"get_cart_total": 0, "get_itemtotal": 0}

    return render(request, 'escan/User/E-commerceUser/cart.html', {'cartitems' : cartitems, 'cart':cart})

@csrf_exempt
@login_required
def checkout(request):
    if request.method == 'POST':
        customer = Customer.objects.get(user=request.user)
        cart_items = Cart.objects.filter(customer=customer)
        total_amount = sum(item.total_price for item in cart_items)

        # Create an order
        order = Order.objects.create(customer=customer, total_amount=total_amount)

        # Update the customer's total spent
        customer.total_spent += total_amount
        customer.save()

        for item in cart_items:
            item.product.stock -= item.quantity
            item.product.save()
        cart_items.delete()  # Clear the cart after checkout

        return redirect('order_summary')

    product_id = request.GET.get('product_id')
    quantity = request.GET.get('quantity')
    if product_id and quantity:
        product = get_object_or_404(Product, id=product_id)
        total_amount = product.price * int(quantity)
        return render(request, 'E-commerceUser', {'product': product, 'quantity': quantity, 'total_amount': total_amount})

    return render(request, 'escan/User/E-commerceUser/checkout.html')




# Scan
def detect(request):
    return render(request, "escan/User/Scan/Detect.html")
# @login_required
# def order_summary(request):
#     customer = Customer.objects.get(user=request.user)
#     orders = Order.objects.filter(customer=customer)
#     return render(request, 'order_summary.html', {'orders': orders, 'customer': customer})
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

#MESSAGES/INBOX
# def inbox(request):
#     threads = Thread.objects.filter(user=request.user)
#     return render(request, 'escan/messages/inbox.html', {'threads': threads})

#2
# def inbox(request):
#     # Fetch all messages where the receiver is the logged-in user
#     messages = Message.objects.filter(receiver=request.user).order_by('-timestamp')

#     # Mark all messages as read
#     # messages.filter(read=False).update(read=True)

#     # Pass the messages to the template
#     return render(request, 'escan/messages/inbox.html', {'messages': messages})

# @login_required
# def inbox(request):
#     # Get all messages for the current logged-in user
#     messages = Message.objects.filter(receiver=request.user).order_by('-timestamp')

#     # Logic to filter users based on role
#     if request.user.role == 'User':
#         receivers = CustomUser.objects.filter(role='Admin')
#     elif request.user.role == 'Admin':
#         receivers = CustomUser.objects.filter(role='User')
#     else:
#         receivers = CustomUser.objects.none()  # No receivers for other roles

#     # Pass receivers to the form dynamically
#     form = MessageForm()
#     form.fields['receiver'].queryset = receivers  # Filter the receiver field

#     if request.method == 'POST':
#         form = MessageForm(request.POST)
#         if form.is_valid():
#             receiver = form.cleaned_data['receiver']
#             content = form.cleaned_data['content']
#             subject = form.cleaned_data['subject']

#             logging.debug(f"Form valid. Receiver: {receiver}, Content: {content}, Subject: {subject}")

#             # Create a new thread if it doesn't exist
#             thread, created = Thread.objects.get_or_create(user=request.user, admin=receiver)

#             # Create the message and save it
#             Message.objects.create(
#                 thread=thread,
#                 sender=request.user,
#                 receiver=receiver,
#                 content=content,
#                 subject=subject
#             )
#             logging.debug(f"Message created: {Message}")
#             return redirect('inbox')
#         else:
#             # Log the form errors if invalid
#             logging.debug(f"Form errors: {form.errors}")
#             return HttpResponse("Form is not valid")

#     return render(request, 'escan/messages/inbox.html', {'messages': messages, 'form': form, 'receivers': receivers})

def inbox(request):
    # Get all messages for the current logged-in user
    messages = Message.objects.filter(receiver=request.user).order_by('-timestamp')

    # Logic to filter users based on role
    if request.user.role == 'User':
        receivers = CustomUser.objects.filter(role='Admin')
    elif request.user.role == 'Admin':
        receivers = CustomUser.objects.filter(role='User')
    else:
        receivers = CustomUser.objects.none()  # No receivers for other roles

    # Pass receivers to the form dynamically
    form = MessageForm()
    form.fields['receiver'].queryset = receivers  # Filter the receiver field

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            receiver = form.cleaned_data['receiver']
            content = form.cleaned_data['content']
            subject = form.cleaned_data['subject']

            logging.debug(f"Form valid. Receiver: {receiver}, Content: {content}, Subject: {subject}")

            # Create a new thread if it doesn't exist
            thread, created = Thread.objects.get_or_create(user=request.user, admin=receiver)

            # Create the message and save it
            Message.objects.create(
                thread=thread,
                sender=request.user,
                receiver=receiver,
                content=content,
                subject=subject
            )
            logging.debug(f"Message created.")
            return redirect('inbox')
        else:
            logging.debug(f"Form errors: {form.errors}")
            return HttpResponse("Form is not valid")

    return render(request, 'escan/messages/inbox.html', {'messages': messages, 'form': form, 'receivers': receivers})

# def unread_message_count(request):
#     # Count the number of unread messages for the current user
#     unread_count = Message.objects.filter(receiver=request.user, is_read=False).count()
    
#     # Get the unread messages for the dropdown
#     unread_messages = Message.objects.filter(receiver=request.user, is_read=False)[:5]  # Limit to 5 messages for performance

#     # Prepare a list of message details for the frontend
#     unread_messages_data = [
#         {
#             'thread_id': msg.thread.id,
#             'sender_image_url': msg.sender.image_url.url if msg.sender.image_url else '',  # Ensure we get a URL string
#             'sender_username': msg.sender.username,
#             'content': msg.content[:30],  # Truncate message content
#         }
#         for msg in unread_messages
#     ]
    
#     return JsonResponse({
#         'unread_count': unread_count,
#         'unread_messages': unread_messages_data  # Send unread messages as a list of dictionaries
#     })

def unread_message_count(request):
    # Count all unread messages for the badge
    unread_count = Message.objects.filter(receiver=request.user, is_read=False).count()

    # Get the latest message for each sender to this user
    latest_msg_subquery = Message.objects.filter(
        receiver=request.user,
        is_read=False,
        sender=OuterRef('sender')
    ).order_by('-timestamp')

    # Get latest messages by each sender
    latest_messages = Message.objects.filter(
        id__in=Subquery(
            latest_msg_subquery.values('id')[:1]
        )
    ).order_by('-timestamp')[:5]  # Limit to top 5 most recent latest messages

    unread_messages_data = [
        {
            'thread_id': msg.thread.id,
            'sender_image_url': msg.sender.image_url.url if msg.sender.image_url else '',
            'sender_username': msg.sender.username,
            'content': msg.content[:30],
            'is_read': msg.is_read,
        }
        for msg in latest_messages
    ]

    return JsonResponse({
        'unread_count': unread_count,
        'unread_messages': unread_messages_data
    })

def mark_messages_as_read(request):
    Message.objects.filter(receiver=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})

# def mark_as_read(request, message_id):
#     if request.method == "POST":
#         try:
#             message = Message.objects.get(id=message_id)
#             if message.receiver == request.user and not message.is_read:
#                 message.is_read = True
#                 message.save()
#                 return JsonResponse({"status": "success"})
#             else:
#                 return JsonResponse({"status": "error", "message": "Unauthorized or already read."}, status=400)
#         except Message.DoesNotExist:
#             return JsonResponse({"status": "error", "message": "Message not found."}, status=404)

def thread_view(request, thread_id):
    thread = Thread.objects.get(id=thread_id)
    
    # Update 'is_read' flag for messages when viewed
    thread.messages.filter(receiver=request.user, is_read=False).update(is_read=True)
    messages = thread.messages.all()
    unread_messages = thread.messages.filter(receiver=request.user, is_read=False)

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user  # Set the logged-in user as the sender
            message.thread = thread
            message.receiver = thread.admin  # The receiver of the message (admin or user)
            message.save()

            return redirect('thread_view', thread_id=thread.id)
    
    else:
        # form = MessageForm()
        form = MessageForm(user=request.user)

    return render(request, 'escan/messages/thread.html', {'thread': thread, 'messages': messages, 'form': form, 'unread_messages': unread_messages})

def send_message(request):
    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user  # Set the logged-in user as the sender

            # Get the receiver and make sure the thread is appropriately assigned.
            receiver = form.cleaned_data['receiver']
            message.receiver = receiver

            # Check if a thread exists between the user and receiver. Create one if necessary.
            thread, created = Thread.objects.get_or_create(user=request.user, admin=receiver)

            # Assign the thread to the message.
            message.thread = thread
            message.save()

            return redirect('thread_view', thread_id=thread.id)  # Redirect to the thread view
    else:
        form = MessageForm()

    return render(request, 'escan/messages/inbox.html', {'form': form})


@csrf_exempt  # Optional if you're manually handling CSRF (best to keep CSRF check!)
def mark_single_message_as_read(request):
    if request.method == "POST":
        data = json.loads(request.body)
        thread_id = data.get('thread_id')
        Message.objects.filter(thread_id=thread_id, receiver=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'marked'})
    return JsonResponse({'error': 'Invalid request'}, status=400)


# @login_required
# def latest_messages_for_thread(request):
#     # Get all latest messages **sent to** the current user
#     latest_messages = (
#         Message.objects
#         .filter(receiver=request.user)
#         .values('sender__username', 'thread__id')
#         .annotate(latest_time=Max('timestamp'))
#         .order_by('-latest_time')
#     )

#     # Collect the actual message content
#     data = []
#     for msg in latest_messages:
#         message = (
#             Message.objects
#             .filter(sender__username=msg['sender__username'], thread_id=msg['thread__id'])
#             .order_by('-timestamp')
#             .first()
#         )
#         data.append({
#             'sender': msg['sender__username'],
#             'content': message.content,
#             'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M'),
#             'thread_id': msg['thread__id'],
#         })

#     return JsonResponse(data, safe=False)

def latest_message_for_thread(request):
    # Step 1: Get the latest messages per thread+sender to this user
    latest_messages = (
        Message.objects
        .filter(receiver=request.user)
        .values('sender__username', 'thread__id')
        .annotate(latest_time=Max('timestamp'))
    )

    # Step 2: Collect the actual message content + is_read flag
    data = []
    for msg in latest_messages:
        message = (
            Message.objects
            .filter(
                sender__username=msg['sender__username'],
                thread_id=msg['thread__id'],
                receiver=request.user  # Ensures it’s a message TO the current user
            )
            .order_by('-timestamp')
            .first()
        )

        if message:
            data.append({
                'sender': msg['sender__username'],
                'content': message.content,
                'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M'),
                'thread_id': msg['thread__id'],
                'is_read': message.is_read,
            })

    # Step 3: Sort unread messages first, then newest to oldest
    data.sort(key=lambda x: (x['is_read'], -int("".join(x['timestamp'].replace("-", "").replace(":", "").replace(" ", "")))))

    return JsonResponse(data, safe=False)

# @login_required
# def thread_placeholder(request):
#     # Get the latest message from each sender (to the current user)
#     latest_messages = (
#         Message.objects.filter(receiver=request.user)
#         .order_by('sender', '-timestamp')
#         .distinct('sender')  # Works only on PostgreSQL
#     )

#     return render(request, 'escan/messages/thread.html', {
#         'thread': None,
#         'messages': [],
#         'latest_messages': latest_messages
#     })


def thread_placeholder(request):
    messages = (
        Message.objects.filter(receiver=request.user)
        .order_by('-timestamp')
    )

    latest_by_sender = {}
    for msg in messages:
        if msg.sender_id not in latest_by_sender:
            latest_by_sender[msg.sender_id] = msg

    form = MessageForm(user=request.user)  # Pass user here

    return render(request, 'escan/messages/thread.html', {
        'thread': None,
        'messages': [],
        'latest_messages': latest_by_sender.values(),
        'form': form
    })


@login_required
def compose_message(request):
    if request.method == 'POST':
        subject = request.POST.get('subject')
        content = request.POST.get('content')
        current_user = request.user

        # Determine the recipient based on role
        if current_user.role == 'Admin':
            receiver = User.objects.filter(role='User', is_deleted=False).exclude(id=current_user.id).first()
        else:
            receiver = User.objects.filter(role='Admin', is_deleted=False).exclude(id=current_user.id).first()

        if not receiver:
            # Handle if there's no receiver found
            messages.error(request, "No recipient available.")
            return redirect('inbox')

        # Try to find existing thread
        thread = Thread.objects.filter(user__in=[current_user, receiver], admin__in=[current_user, receiver]).first()
        if not thread:
            if current_user.role == 'Admin':
                thread = Thread.objects.create(user=receiver, admin=current_user)
            else:
                thread = Thread.objects.create(user=current_user, admin=receiver)

        # Create and save the message
        Message.objects.create(
            thread=thread,
            sender=current_user,
            receiver=receiver,
            content=content
        )

        return redirect('thread_placeholder')


#SCAN SCAM
# Allow loading of ResNet model class
torch.serialization.add_safe_globals({
    'torchvision.models.resnet.ResNet': models.ResNet
})

#banana disease model
def load_disease_model():
    # Load the disease model (Replace with your actual model loading code)
    model = models.resnet18(weights=None)  # Example, change to your model
    num_ftrs = model.fc.in_features
    model.fc = torch.nn.Linear(num_ftrs, 10)  # number of classes in your disease model
    model.load_state_dict(torch.load('escan/model/banana_disease_resnet_state_dict.pth'))
    model.eval()
    return model

def banana_disease(request):
    model = load_disease_model()
    class_names = ['Banana Anthracnose Fruit disease', 'Banana Bract Mosaic Virus Disease', 'Banana Cordana Leaf Disease',
                   'Banana Fusarium Wilt Tree Disease', 'Banana Insect Pest Disease', 'Banana Naturally Leaf Dead',
                   'Banana Panama Leaf Disease', 'Banana Pestalotiopsis Disease', 'Banana Rhizome Root Tree Disease',
                   'Banana Sigatoka Leaf Disease']
    class_descriptions = {
        'Banana Anthracnose Fruit disease': {'description': 'Description of Anthracnose...', 'symptoms': 'Symptoms of Anthracnose...', 'management': 'Management of Anthracnose...', 'prevention': 'Prevention of Anthracnose...'},
        'Banana Bract Mosaic Virus Disease': {'description': 'Description of Anthracnose...', 'symptoms': 'Symptoms of Anthracnose...', 'management': 'Management of Anthracnose...', 'prevention': 'Prevention of Anthracnose...'},
        'Banana Cordana Leaf Disease': {'description': 'Banana Cordana Leaf Disease description', 'symptoms': 'Symptoms of Anthracnose...', 'management': 'Management of Anthracnose...', 'prevention': 'Prevention of Anthracnose...'},
        'Banana Anthracnose Fruit disease': {'description': 'Description of Anthracnose...', 'symptoms': 'Symptoms of Anthracnose...', 'management': 'Management of Anthracnose...', 'prevention': 'Prevention of Anthracnose...'},
        'Banana Anthracnose Fruit disease': {'description': 'Description of Anthracnose...', 'symptoms': 'Symptoms of Anthracnose...', 'management': 'Management of Anthracnose...', 'prevention': 'Prevention of Anthracnose...'},
        'Banana Anthracnose Fruit disease': {'description': 'Description of Anthracnose...', 'symptoms': 'Symptoms of Anthracnose...', 'management': 'Management of Anthracnose...', 'prevention': 'Prevention of Anthracnose...'},
        # Add other diseases here...
    }

    result = None
    confidence = None
    prediction_time = None
    image_url = None
    disease_info = None

    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.cleaned_data['image']
            img = Image.open(image).convert('RGB')
            img_tensor = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
            ])(img).unsqueeze(0)

            with torch.no_grad():
                output = model(img_tensor)
                probabilities = torch.nn.functional.softmax(output[0], dim=0)
                confidence = torch.max(probabilities).item() * 100
                _, predicted = torch.max(output, 1)
                result = class_names[predicted.item()]
                prediction_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                disease_info = class_descriptions.get(result)

            # 🔼 Upload image to Supabase
            user = request.user
            image.seek(0)  # Reset pointer
            file_data = image.read()
            file_name = f"{user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{image.name}"
            
            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_ROLE_KEY)
            bucket = supabase.storage.from_('detection-images')

            try:
                # Upload image with correct content type
                upload_response = bucket.upload(file_name, file_data, {
                    "content-type": image.content_type
                })
                print("🔍 Response from Supabase:", upload_response)

                # If response has 'path' attribute, use it to get the public URL
                if hasattr(upload_response, 'path') and upload_response.path:
                    # Construct public URL from response
                    image_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/detection-images/{upload_response.path}"

                    # Save to DB
                    DetectionRecord.objects.create(
                        user=user,
                        prediction=result,
                        confidence=confidence,
                        image_url=image_url,
                        model_type='disease'
                    )
                    print("✅ Detection record saved successfully")
                else:
                    print("❌ Upload error: No path in response")

            except Exception as e:
                print(f"⚠️ Supabase upload error: {e}")

            return render(request, 'escan/User/Scan/banana_disease_result.html', {
                'result': result,
                'confidence': confidence,
                'prediction_time': prediction_time,
                'image_url': image_url,
                'disease_info': disease_info,
            })

    else:
        form = ImageUploadForm()

    # Get current user's past records (most recent first)
    # user_records = DetectionRecord.objects.filter(user=request.user).order_by('-timestamp')[:4]

    # return render(request, 'escan/User/Scan/banana_disease.html', {'form': form, 'user_records': user_records})
    return render(request, 'escan/User/Scan/banana_disease.html', {'form': form})

#banana variety model
def load_variety_model():
    # Load the variety model (Replace with your actual model loading code)
    model = models.resnet18(weights=None)  # Example, change to your model
    num_ftrs = model.fc.in_features
    model.fc = torch.nn.Linear(num_ftrs, 8)  # number of classes in your variety model
    model.load_state_dict(torch.load('escan/model/banana_variety_resnet_state_dict.pth'))
    model.eval()
    return model

def banana_variety(request):
    model = load_variety_model()
    class_names = ['Anaji', 'Banana Lady Finger ( Señorita )', 'Banana Red', 'Bichi', 'Canvendish(Bungulan)', 'Lakatan', 'Saba', 'Sabri Kola']
    class_descriptions = {
        'Anaji': {'description': 'Description of Anaji variety...', 'symptoms': 'Symptoms of Anaji...', 'management': 'Management of Anaji...', 'prevention': 'Prevention of Anaji...'},
        # Add other varieties here...
    }

    result = None
    confidence = None
    prediction_time = None
    image_url = None
    disease_info = None

    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.cleaned_data['image']
            img = Image.open(image).convert('RGB')
            img_tensor = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
            ])(img).unsqueeze(0)

            with torch.no_grad():
                output = model(img_tensor)
                probabilities = torch.nn.functional.softmax(output[0], dim=0)
                confidence = torch.max(probabilities).item() * 100
                _, predicted = torch.max(output, 1)
                result = class_names[predicted.item()]
                prediction_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                disease_info = class_descriptions.get(result)

            # 🔼 Upload image to Supabase
            user = request.user
            image.seek(0)  # Reset pointer
            file_data = image.read()
            file_name = f"{user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{image.name}"
            
            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_ROLE_KEY)
            bucket = supabase.storage.from_('detection-images')

            try:
                # Upload image with correct content type
                upload_response = bucket.upload(file_name, file_data, {
                    "content-type": image.content_type
                })
                print("🔍 Response from Supabase:", upload_response)

                # If response has 'path' attribute, use it to get the public URL
                if hasattr(upload_response, 'path') and upload_response.path:
                    # Construct public URL from response
                    image_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/detection-images/{upload_response.path}"

                    # Save to DB
                    DetectionRecord.objects.create(
                        user=user,
                        prediction=result,
                        confidence=confidence,
                        image_url=image_url,
                        model_type='variety'
                    )
                    print("✅ Detection record saved successfully")
                else:
                    print("❌ Upload error: No path in response")

            except Exception as e:
                print(f"⚠️ Supabase upload error: {e}")

            return render(request, 'escan/User/Scan/banana_variety_result.html', {
                'result': result,
                'confidence': confidence,
                'prediction_time': prediction_time,
                'image_url': image_url,
                'disease_info': disease_info,
            })

    else:
        form = ImageUploadForm()

    # user_records = DetectionRecord.objects.filter(user=request.user).order_by('-timestamp')[:4]

    return render(request, 'escan/User/Scan/banana_variety.html', {'form': form})

@login_required
def disease_scan_history(request):
    user_records = DetectionRecord.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'escan/User/Scan/disease_scan_records.html', {'user_records': user_records})

@login_required
def variety_scan_history(request):
    user_records = DetectionRecord.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'escan/User/Scan/variety_scan_records.html', {'user_records': user_records})


@login_required
def view_scan_result(request, record_id):
    record = get_object_or_404(DetectionRecord, pk=record_id, user=request.user)

    # Use the model_type to determine which result template to render
    template = 'escan/User/Scan/banana_disease_result.html' if record.model_type == 'disease' else 'escan/User/Scan/banana_variety_result.html'

     # Disease Descriptions
    disease_descriptions = {
        'Banana Anthracnose Fruit disease': {
            'description': 'Description of Anthracnose...',
            'symptoms': 'Symptoms of Anthracnose...',
            'management': 'Management of Anthracnose...',
            'prevention': 'Prevention of Anthracnose...'
        },
        'Banana Bract Mosaic Virus Disease': {
            'description': 'banana bract...',
            'symptoms': 'Symptoms of Anthracnose...',
            'management': 'Management of Anthracnose...',
            'prevention': 'Prevention of Anthracnose...'
        },
        # Add all other disease info...
    }

    # Variety Descriptions
    variety_descriptions = {
        'Anaji': {
            'description': 'Description of Anaji...',
            'symptoms': 'Symptoms of Anaji...',
            'management': 'Management of Anaji...',
            'prevention': 'Prevention of Anaji...'
        },
        'Banana Lady Finger ( Señorita )': {
            'description': 'Description of Señorita...',
            'symptoms': 'N/A',
            'management': 'N/A',
            'prevention': 'N/A'
        },
        # Add all other variety info...
    }

    prediction_key = record.prediction.strip()

    if record.model_type == 'disease':
        disease_info = disease_descriptions.get(prediction_key, {})
    elif record.model_type == 'variety':
        disease_info = variety_descriptions.get(prediction_key, {})
    else:
        disease_info = {}

    return render(request, template, {
        'result': record.prediction,
        'confidence': record.confidence,
        'prediction_time': record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'image_url': record.image_url,
        'disease_info': disease_info
    })



