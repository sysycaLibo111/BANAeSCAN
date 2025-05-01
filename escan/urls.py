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
    # path("scan/banana_detection", views.banana_detection, name="banana_detection"),
    path('banana_disease/', views.banana_disease, name='banana_disease'),
    # path('banana_disease_result/', views.banana_disease_result, name='banana_disease_result'),
    path('banana_variety/', views.banana_variety, name='banana_variety'),
    # path('banana_variety_result/', views.banana_variety_result, name='banana_variety_result'),
    # path('detection-detail/<int:record_id>/', views.detection_detail, name='detection_detail'),  # New view for result detail
    path('disease_scan-history/', views.disease_scan_history, name='disease_scan_history'),
    path('variety_scan-history/', views.variety_scan_history, name='variety_scan_history'),
    path('scan-result/<int:record_id>/', views.view_scan_result, name='view_scan_result'),
    
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
    path('user_product_list/', views.user_product_list, name='user_product_list'),
    path('cart/', views.cart, name = 'cart'),
     path('update_item/', views.update_item, name='update_item'),
    # Customers
    path("customer_table/", views.customer_table, name="customer_table"),
    
    #Graphs
     path('user_graph/', views.user_graph_view, name='user_graph'),


    #  User Parts
      path("update_userprofile/", views.update_userprofile, name="update_userprofile"),

    # Scan Parts
    path("detect/", views.detect, name="detect"), 
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

    #messages/inbox
    # path('messages/', views.inbox, name='inbox'),
    path('compose/', views.compose_message, name='compose_message'),
    path('thread/<int:thread_id>/', views.thread_view, name='thread'),
    path('messages/send/', views.send_message, name='send_message'),
    path('unread-message-count/', views.unread_message_count, name='unread_message_count'),
    path('mark-messages-as-read/', views.mark_messages_as_read, name='mark_messages_as_read'),
    path('mark-single-message-as-read/', views.mark_single_message_as_read, name='mark_single_message_as_read'),
    path('latest_message/', views.latest_message_for_thread, name='latest_message_for_thread'),
    path('thread/', views.thread_placeholder, name='thread_placeholder'),
    # path('mark-as-read/<int:message_id>/', views.mark_as_read, name='mark_as_read'),

    #Logout
     path('logout/', views.user_logout, name='logout'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


