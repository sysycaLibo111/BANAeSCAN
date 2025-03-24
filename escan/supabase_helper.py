import supabase
from io import BytesIO
from django.conf import settings
import logging

# Supabase configuration
SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_ROLE_KEY = settings.SUPABASE_ROLE_KEY
SUPABASE_BUCKET = settings.SUPABASE_BUCKET  # Set in settings.py

# Initialize Supabase client
supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_ROLE_KEY)

# Logger setup
logger = logging.getLogger(__name__)

def upload_image_to_supabase(image_file, image_name):
    try:
        # Read image file bytes
        image_bytes = image_file.read()

        # ✅ Upload to Supabase storage
        response = supabase_client.storage.from_(SUPABASE_BUCKET).upload(
            f"product-images/{image_name}", image_bytes, file_options={"content-type": image_file.content_type}
        )

        # ✅ Debugging log
        logger.info(f"Supabase Response: {response}")

        if "error" in response:
            logger.error(f"Supabase Upload Error: {response['error']}")
            return None

        # ✅ Generate and return the public URL
        image_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/product-images/{image_name}"
        logger.info(f"Generated Image URL: {image_url}")
        

    except Exception as e:
        logger.error(f"Upload Error: {e}")
        return None

