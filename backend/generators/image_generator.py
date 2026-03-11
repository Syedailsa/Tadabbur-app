import os
import base64
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
import uuid
from supabase import create_client, Client
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_GENERATED_IMAGES_BUCKET = os.getenv("GENERATED_IMAGES_BUCKET", "generated-images")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def pil_to_img_url(image: Image.Image) -> str:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    image_bytes = buffer.getvalue()

    unique_filename = f"{uuid.uuid4()}.png"

    supabase.storage.from_(SUPABASE_GENERATED_IMAGES_BUCKET).upload(
        path=unique_filename,
        file=image_bytes,
        file_options={"content-type": "image/png", "upsert": "true"}
    )

    signed = supabase.storage.from_(SUPABASE_GENERATED_IMAGES_BUCKET).create_signed_url(
        path=unique_filename,
        expires_in=60 * 60 * 24  
    )

    url = signed["signedURL"]
    print(f" Generated image URL: {url}")
    return url


client = InferenceClient(
    provider="fal-ai",
    api_key=os.getenv("HUGGING_FACE_API"),
)

# output is a PIL.Image object
def generate_image(prompt: str) -> Image.Image:
    image = client.text_to_image(
        prompt,
        model="black-forest-labs/FLUX.1-dev",
    )
    return image