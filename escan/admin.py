from django.contrib import admin
from django import forms
from .models import CustomUser, Product, Customer, Category,Order 

admin.site.register(CustomUser)
admin.site.register(Category)
admin.site.register(Customer)
admin.site.register(Order)
