from django.urls import path, include
from escan import views
from django.conf import settings
from django.conf.urls.static import static
from escan.views import login_view, user_dashboard
from .views import upload_product

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('accounts/', include('allauth.urls')),
    # for user
    path("login/", views.login_view, name="login"),
    path("signup_view/", views.signup_view, name="signup_view"), 
    path("user_dashboard/", views.user_dashboard, name="user_dashboard"),
    path("user_base/", views.user_base, name="user_base"),
    path("scan/", views.scan, name="scan"),
    
    # for admin
    path("admin_login/", views.admin_login, name="admin_login"),
    path("admin_signup/", views.admin_signup, name="admin_signup"), 
    path("base/", views.base, name="base"),
    path("admin_dashboard/", views.admin_dashboard, name="admin_dashboard"),
    
    # User list Management
    path("user_table/", views.user_table, name="user_table"),
    path("add_user/", views.add_user, name="add_user"),
    path("edit_user/<int:user_id>/", views.edit_user, name="edit_user"),
    path("delete_user/<int:user_id>/", views.delete_user, name="delete_user"),
    path("undo_delete/", views.undo_delete, name="undo_delete"),

     # Categories
    path('categories/', views.category_list, name='category_list'),
    path('add-category/', views.add_category, name='add_category'),
    path('edit-category/<int:category_id>/', views.edit_category, name='edit_category'),
    path('delete-category/<int:category_id>/', views.delete_category, name='delete_category'),

    # # Products
    path('upload/', upload_product, name='upload_product'),
    path('products/', views.product_list, name='product_list'),
    path('add_product/', views.add_product, name='add_product'),
    path('edit_product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete_product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('restore-product/<int:product_id>/', views.restore_product, name='restore_product'),


    
    # try lang
    # path("admin-dashboard/", views.admin_dashboard_view, name="admin_dashboard"),  # Admin dashboard view
    # path("farmer-dashboard/", views.farmer_dashboard_view, name="farmer_dashboard"),  # Farmer dashboard view
    # path("user-dashboard/", views.user_dashboard_view, name="user_dashboard"),

     # Google Authentication URLs
    # path("shop_signup/google/", views.google_signup, name="google_signup"),
    # path("auth/callback/", views.auth_callback, name="auth_callback"),

    # forgot password
    path('forgot-password/', views.ForgotPassword, name='forgot-password'),
    path('password-reset-sent/<str:reset_id>/', views.PasswordResetSent, name='password-reset-sent'),
    path('reset-password/<str:reset_id>/', views.ResetPassword, name='reset-password'),

    #Logout
     path('logout/', views.user_logout, name='logout'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


