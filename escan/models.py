from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
# from django.contrib.auth.models import 
from django.conf import settings
import uuid
import os

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('User', 'User'),
    ]

    id = models.AutoField(primary_key=True)  # Unique ID for each user
    first_name = models.CharField(max_length=50)  # First name field
    last_name = models.CharField(max_length=50)  # Last name field
    username = models.CharField(max_length=50, unique=True)  # Unique username
    email = models.EmailField(unique=True)  # Unique email
    password = models.CharField(max_length=255)  # Hashed password storage
    is_deleted = models.BooleanField(default=False)  # Soft delete field
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='User')

    def soft_delete(self):
        self.is_deleted = True
        self.save()

    def restore(self):
        self.is_deleted = False
        self.save()

    class meta:
        bd_table = 'user_account'
        

class PasswordReset(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reset_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_when = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Password reset for {self.user.username} at {self.created_when}"
    
    class Meta:
        app_label = 'escan'




# E-commerce related models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'category'

    def __str__(self):
        return self.name


class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        db_table = 'customer'

    def __str__(self):
        return self.user.username

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image_url = models.URLField(blank=True, null=True)  # Store image URL from Supabase
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def soft_delete(self):
        self.is_deleted = True
        self.save()

    def restore(self):
        self.is_deleted = False
        self.save()
    

    class Meta:
        db_table = 'product'

    def __str__(self):
        return self.name


class Order(models.Model):
    product= models.ForeignKey(Product, on_delete=models.CASCADE)
    customer= models.ForeignKey(Customer, on_delete=models.CASCADE)
    quantity=models.IntegerField()
    order_date= models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status=models.BooleanField(default=False)
    

    class Meta:
        db_table = 'order'

    def __str__(self):
        return f"Order {self.id} by {self.customer.user.username}"

