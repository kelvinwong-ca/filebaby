import os
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image


def force_image_size(
    image: Image.Image, width: int = 150, height: int = 150
) -> Image.Image:
    """
    Given a PIL Image, crops it to size by taking the center portion.

    Smaller images are enlarged to fit. Aspect ratio is preserved.

    @param image: PIL Image instance
    @param width: Desired width of the output image
    @param height: Desired height of the output image

    @returns New PIL Image
    """
    x, y = image.size
    if x == width and y == height:
        return image

    # Enlarge the image if it's smaller than the target size on any axis
    if x < width or y < height:
        scale_x = width / x
        scale_y = height / y
        scale = max(scale_x, scale_y)
        new_x = int(x * scale)
        new_y = int(y * scale)
        image = image.resize((new_x, new_y), Image.Resampling.LANCZOS)
        x, y = image.size

    # Reduce the image if it's larger than the target size on both axes
    if x > width and y > height:
        scale_x = width / x
        scale_y = height / y
        scale = max(scale_x, scale_y)
        new_x = int(x * scale)
        new_y = int(y * scale)
        image = image.resize((new_x, new_y), Image.Resampling.LANCZOS)
        x, y = image.size

    assert x >= width
    assert y >= height

    # Calculate cropping box from image center
    #
    left = (x - width) / 2
    top = (y - height) / 2
    right = (x + width) / 2
    bottom = (y + height) / 2

    # Crop and return the image
    cropped_image = image.crop((left, top, right, bottom))
    return cropped_image


def resize_uploaded_image(image, width=150, height=150):
    pil_image = Image.open(image)
    resized_image = force_image_size(pil_image, width, height)

    new_image_io = BytesIO()
    resized_image.save(new_image_io, format="PNG")

    return ContentFile(new_image_io.getvalue(), name=image.name)
