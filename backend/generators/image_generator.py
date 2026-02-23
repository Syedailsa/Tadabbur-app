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
    provider="nscale",
    api_key=os.getenv("HUGGING_FACE_API"),
)

# output is a PIL.Image object
def generate_image(prompt: str) -> Image.Image:
    image = client.text_to_image(
        """Cinematic historical illustration of Prophet Nuh (peace be upon him) building a massive wooden ark in an ancient desert landscape. 
        The prophet is shown respectfully from the back view only, wearing modest loose earth-toned robes and a simple head covering, holding a wooden tool while supervising construction. 
        Several early believers assist him, carrying planks and ropes. 
        The ark is enormous, partially constructed, made of dark aged wood beams. 
        Sand-covered plain with distant hills, warm golden sunlight, dramatic sky with soft clouds. 
        Emotion: perseverance, faith, determination.

        Art style: highly detailed, realistic yet respectful historical illust
    """,
        model="stabilityai/stable-diffusion-xl-base-1.0",
    )
    return image