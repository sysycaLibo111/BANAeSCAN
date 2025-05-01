
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
from .models import CustomUser,Customer, Product, Category, Order, Cart, Cartitems,ShippingAddress
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
from .forms import CategoryForm,ProductForm,UserProfileForm,  EditProfileForm,ShippingAddressForm
from .supabase_helper import upload_image_to_supabase
import logging
from django.core.files.storage import FileSystemStorage
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
# def orders_part(request):
#     if request.user.role != "Admin":
#         return redirect("user_dashboard")  # Restrict non-admins
#     new_orders = Order.objects.filter(status='pending')
#     orders = Order.objects.all()
#     return render(request, "escan/Admin/E-commerce/orders_part.html", {"new_orders": new_orders,"orders": orders})


# def update_order_status(request, order_id):
#     order = get_object_or_404(Order, id=order_id)
#     if request.method == 'POST':
#         new_status = request.POST.get('status')
#         order.status = new_status
#         order.save()
#     return redirect('orders_part') 

def orders_part(request):
    new_orders = Order.objects.filter(status='pending')
    total_orders = Order.objects.exclude(status='pending').order_by('status')

    return render(request, 'escan/Admin/E-commerce/orders_part.html', {
        'new_orders': new_orders,
        'total_orders': total_orders
    })

def update_order_status(request, order_id):
    if request.method == 'POST':
        new_status = request.POST.get('status')
        order = get_object_or_404(Order, pk=order_id)
        order.status = new_status
        order.save()
        return redirect('orders_part')  
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


#user E-commerce side
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


# @login_required
# def user_dashboard(request):
#     customer, created = Customer.objects.get_or_create(user=request.user)
#     cart, created = Cart.objects.get_or_create(customer=customer, completed=False)
#     products = Product.objects.filter(is_deleted=False) 
#     return render(request, 'escan/User/user_dashboard.html', {'products': products,'cart': cart})

# @login_required
# def update_item(request):
#     data = json.loads(request.body)
#     productId = data['productId']
#     action = data['action']
    
#     customer = request.user.customer
#     product = Product.objects.get(id=productId)
#     cart, created = Cart.objects.get_or_create(customer=customer, completed=False)
#     cart_item, created = cart.cartitems_set.get_or_create(product=product)

#     if action == 'add':
#         cart_item.quantity += 1
#         cart_item.save()
    
#     # Return the updated cart item count
#     cart_item_count = cart.get_itemtotal()  # Use the method to get the total count
#     return JsonResponse({'cartItemCount': cart_item_count}, safe=False)

# def cart(request):
#     if request.user.is_authenticated:
#         customer, created = Customer.objects.get_or_create(user=request.user)
#         cart, created = Cart.objects.get_or_create(customer = customer, completed = False)
#         cartitems = cart.cartitems_set.all()
#     else:
#         cartitems = []
#         cart = {"get_cart_total": 0, "get_itemtotal": 0}

#     return render(request, 'escan/User/E-commerceUser/cart.html', {'cartitems' : cartitems, 'cart':cart})

# @csrf_exempt
# @login_required
# def checkout(request):
#     if request.method == 'POST':
#         customer = Customer.objects.get(user=request.user)
#         cart_items = Cart.objects.filter(customer=customer)
#         total_amount = sum(item.total_price for item in cart_items)

#         # Create an order
#         order = Order.objects.create(customer=customer, total_amount=total_amount)

#         # Update the customer's total spent
#         customer.total_spent += total_amount
#         customer.save()

#         for item in cart_items:
#             item.product.stock -= item.quantity
#             item.product.save()
#         cart_items.delete()  # Clear the cart after checkout

#         return redirect('order_summary')

#     product_id = request.GET.get('product_id')
#     quantity = request.GET.get('quantity')
#     if product_id and quantity:
#         product = get_object_or_404(Product, id=product_id)
#         total_amount = product.price * int(quantity)
#         return render(request, 'E-commerceUser', {'product': product, 'quantity': quantity, 'total_amount': total_amount})

#     return render(request, 'escan/User/E-commerceUser/checkout.html')



@login_required
def user_dashboard(request):
    customer, created = Customer.objects.get_or_create(user=request.user)
    cart, created = Cart.objects.get_or_create(customer=customer, completed=False)
    products = Product.objects.filter(is_deleted=False) 
    return render(request, 'escan/User/user_dashboard.html', {'products': products, 'cart': cart})

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
    elif action == 'remove':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()  # Remove item if quantity is 0

    # Return the updated cart item count
    cart_item_count = cart.get_itemtotal()  # Use the method to get the total count
    return JsonResponse({'cartItemCount': cart_item_count}, safe=False)

@login_required
def add_to_cart(request, product_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        quantity = data.get('quantity', 1)

        customer = request.user.customer
        product = get_object_or_404(Product, id=product_id)
        cart, created = Cart.objects.get_or_create(customer=customer, completed=False)

        cart_item, created = cart.cartitems_set.get_or_create(product=product)
        cart_item.quantity += int(quantity)
        cart_item.save()

        # Return the updated cart item count
        cart_item_count = cart.get_itemtotal()  # Use the method to get the total count
        return JsonResponse({'success': True, 'item_count': cart_item_count})
    
    return JsonResponse({'success': False}, status=400)

def cart(request):
    if request.user.is_authenticated:
        customer, created = Customer.objects.get_or_create(user=request.user)
        cart, created = Cart.objects.get_or_create(customer=customer, completed=False)
        cartitems = cart.cartitems_set.all()
    else:
        cartitems = []
        cart = {"get_cart_total": 0, "get_itemtotal": 0}

    return render(request, 'escan/User/E-commerceUser/cart.html', {'cartitems': cartitems, 'cart': cart})

@login_required
def remove_item(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(Cartitems, id=item_id)
        cart_item.delete()  # Remove the item from the cart

        # Return the updated cart item count
        cart = Cart.objects.get(customer=request.user.customer, completed=False)
        cart_item_count = cart.get_itemtotal()
        return JsonResponse({'success': True, 'cartItemCount': cart_item_count})

    return JsonResponse({'success': False}, status=400)

@csrf_exempt
@login_required
def checkout(request):
    if request.method == 'POST':
        customer = Customer.objects.get(user=request.user)
        cart = Cart.objects.get(customer=customer, completed=False)
        cart_items = cart.cartitems_set.all()
        total_amount = sum(item.total_price for item in cart_items)

        # Create an order
        order = Order.objects.create(customer=customer, total_amount=total_amount)

        # Update the product stock and clear the cart
        for item in cart_items:
            item.product.stock -= item.quantity
            item.product.save()
        cart_items.delete()  # Clear the cart after checkout

        return redirect('cart')

    return render(request, 'escan/User/E-commerceUser/checkout.html')

@login_required
def add_shipping_address(request, cart_id):
    customer = request.user.customer
    cart = get_object_or_404(Cart, id=cart_id, customer=customer, completed=False)

    # Check if the customer already has a shipping address
    existing_address = ShippingAddress.objects.filter(customer=customer).first()

    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        province = request.POST.get('state', '').strip()
        zipcode = request.POST.get('zipcode', '').strip()

        # Check if all required fields are filled
        if not all([phone_number, address, city, province, zipcode]):
            messages.error(request, "Please fill out all shipping address fields.")
            return redirect('cart')

        if existing_address:
            # If there's an existing address, update it
            existing_address.phone_number = phone_number
            existing_address.address = address
            existing_address.city = city
            existing_address.province = province
            existing_address.zipcode = zipcode
            existing_address.save()
            messages.success(request, "Shipping address updated successfully.")
        else:
            # If no existing address, create a new one
            ShippingAddress.objects.create(
                customer=customer,
                cart=cart,
                phone_number=phone_number,
                address=address,
                city=city,
                province=province,
                zipcode=zipcode
            )
            messages.success(request, "Shipping address added successfully.")

        return redirect('cart', cart_id=cart.id)  # Assuming you have a checkout page view

    return render(request, 'escan/User/E-commerceUser/cart.html', {'cart': cart})

@login_required
def edit_shipping_address(request, address_id):
    address = get_object_or_404(ShippingAddress, id=address_id)

    if request.method == 'POST':
        form = ShippingAddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()  # Save the updated address
            messages.success(request, 'Shipping address updated.')
            return redirect('cart')
    else:
        form = ShippingAddressForm(instance=address)

    return render(request, 'escan/User/E-commerceUser/cart.html', {'form': form})
# Scan
def diseasedetect(request):
    return render(request, "escan/User/Scan/diseasedetect.html")

def varietydetect(request):
    return render(request, "escan/User/Scan/varietydetect.html")

def predict(request):
    if request.method == 'POST' and request.FILES['image']:
        image = request.FILES['image']
        
        # Save the uploaded image
        fs = FileSystemStorage()
        filename = fs.save(image.name, image)
        uploaded_file_url = fs.url(filename)
        
        # Make the prediction based on the uploaded image
        predicted_class, confidence = predict_plant_disease(os.path.join(settings.MEDIA_ROOT, filename))
        
        # Store the result in context to send it to the result page
        context = {
            'uploaded_file_url': uploaded_file_url,
            'predicted_class': predicted_class,
            'confidence': confidence,
        }
        
        return render(request, 'result.html', context)  # Result page to show the result
    
    return render(request, 'home.html')  # The page to upload the image

def predict_plant_disease(image_path):
    # Load the image using PIL
    img = Image.open(image_path)
    
    # Resize the image to match the input shape of your model (150x150 pixels)
    img = img.resize((150, 150))  # Update this size based on your model's input shape
    img = np.array(img)  # Convert image to a numpy array

    # If the image has an alpha channel (RGBA), remove it (convert to RGB)
    if img.shape[-1] == 4:
        img = img[..., :3]

    # Normalize the image (you may need to adjust this based on your model's training)
    img = img / 255.0
    
    # Expand dimensions to match the batch size required by the model
    img = np.expand_dims(img, axis=0)  # Shape becomes (1, 150, 150, 3)
    
    # Make the prediction using your trained model
    prediction = model.predict(img)
    
    # Map prediction to the class labels
    class_labels = [
        "Aphids",
        "Aphids",
        "Cercospora Leaf Spot",
        "Defect Eggplant",
        "Flea Beetles",
        "Healthy Eggplant Leaf",
        "Insect Pest Disease",
        "Leaf Spot Disease",
        "Mosaic Virus Disease",
        "Phytophora Blight",
        "Powdery Mildew",
        "White Mold Disease",
        "Wilt Disease"
    ]
    
    # Get the predicted class and the confidence score (percentage)
    predicted_class_idx = np.argmax(prediction)  # Get index of the highest probability
    predicted_class = class_labels[predicted_class_idx]  # Map index to class label
    confidence = round(100 * np.max(prediction), 2)  # Confidence in percentage

    return predicted_class, confidence

def diseaseresult(request):
    # This view can be left empty or used if you decide to separate logic further
    return render(request, 'diseaseresult.html')





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


