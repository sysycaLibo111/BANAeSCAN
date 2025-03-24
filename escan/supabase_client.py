from supabase import create_client
from django.conf import settings
from dotenv import load_dotenv

supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_API_KEY)

def google_auth_redirect():
    return f"{settings.SUPABASE_URL}/auth/v1/authorize?provider=google"
