from django.urls import path, include
from escan import views
from django.conf import settings
from django.conf.urls.static import static
from escan.views import login_view, user_dashboard


urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('accounts/', include('allauth.urls')),
    path("login/", views.login_view, name="login"),
    path("signup_view/", views.signup_view, name="signup_view"), 
    
    # for user
    path("user_dashboard/", views.user_dashboard, name="user_dashboard"),
    path("user_base/", views.user_base, name="user_base"),
    path("scan/", views.scan, name="scan"),
    
    # for admin
    path("admin_dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("update_profile/", views.update_profile, name="update_profile"),
    
    # User list Management
    path("user_table/", views.user_table, name="user_table"),
    path("add_user/", views.add_user, name="add_user"),
    path("edit_user/<int:user_id>/", views.edit_user, name="edit_user"),
    path("delete_user/<int:user_id>/", views.delete_user, name="delete_user"),
    path("undo_last_action_user/", views.undo_last_action_user, name="undo_last_action_user"),
    path('search_users/', views.search_users, name='search_users'),
    path('user_print/', views.user_print, name='user_print'),

     # Categories
    path('categories/', views.category_list, name='category_list'),
    path('add-category/', views.add_category, name='add_category'),
    path('edit-category/<int:category_id>/', views.edit_category, name='edit_category'),
    path('delete-category/<int:category_id>/', views.delete_category, name='delete_category'),

    #  Products
    path('products/', views.product_list, name='product_list'),
    path('add_product/', views.add_product, name='add_product'),
    path('edit_product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete_product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('undo/', views.undo_last_action, name='undo_last_action'),
    path('search_products/', views.search_products, name='search_products'),
    path('product_print/', views.product_print, name='product_print'),


    # Oders
    path('orders_part/', views.orders_part, name='orders_part'),
    path('orders/update/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('user_product_list/', views.user_product_list, name='user_product_list'),
    path('update_item/', views.update_item, name='update_item'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name = 'cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('add_shipping_address/<int:cart_id>/', views.add_shipping_address, name='add_shipping_address'),
    path('edit_shipping_address/<int:address_id>/', views.edit_shipping_address, name='edit_shipping_address'),


    # Customers
    path("customer_table/", views.customer_table, name="customer_table"),
    
    #Graphs
     path('user_graph/', views.user_graph_view, name='user_graph'),


    #  User Parts
      path("update_userprofile/", views.update_userprofile, name="update_userprofile"),

    # Scan Parts
    path("diseasedetect/", views.diseasedetect, name="diseasedetect"), 
    path("varietydetect/", views.varietydetect, name="varietydetect"), 
    path('predict/', views.predict, name='predict'),
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


