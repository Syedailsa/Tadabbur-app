import os
import base64
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

def pil_to_base64(image):
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    img_str = base64.b64encode(buffer.read()).decode("utf-8")
    return img_str

def save_image_local(image, counter: int):
    image.save(f"image{counter}.png")
    counter += 1

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