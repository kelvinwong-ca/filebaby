from io import BytesIO

import PIL
from PIL import Image

from common.cases import BaseTestCase

from ..utils import force_image_size, resize_uploaded_image


class ImageTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()

        self.expected_size = (150, 150)

        self.square_small = self.create_image(50, 50)
        self.square_large = self.create_image(300, 300)
        self.rect_small = self.create_image(50, 125)
        self.rect_large = self.create_image(300, 175)
        self.rect_too_wide = self.create_image(175, 150)
        self.rect_too_tall = self.create_image(150, 175)
        self.rect_not_wide = self.create_image(75, 150)
        self.rect_not_tall = self.create_image(150, 75)
        self.exact_size = self.create_image(150, 150)

    def test_force_image_size_square_reduction(self):
        """Test force_image_size with an image larger than target size"""
        resized_img = force_image_size(self.square_large)
        self.assertEqual(resized_img.size, self.expected_size)

    def test_force_image_size_square_enlargement(self):
        """Test force_image_size with an image smaller than target size"""
        resized_img = force_image_size(self.square_small)
        self.assertEqual(resized_img.size, self.expected_size)

    def test_force_image_size_rectangle_reduction(self):
        """Test force_image_size with an image larger than target size"""
        resized_img = force_image_size(self.rect_large)
        self.assertEqual(resized_img.size, self.expected_size)

    def test_force_image_size_rectangle_enlargement(self):
        """Test force_image_size with an image smaller than target size"""
        resized_img = force_image_size(self.rect_small)
        self.assertEqual(resized_img.size, self.expected_size)

    def test_force_image_size_exact(self):
        """Don't process an image that's already the correct size"""
        resized_img = force_image_size(self.exact_size)
        self.assertEqual(resized_img.size, self.expected_size)
        self.assertEqual(id(resized_img), id(self.exact_size))

    def test_force_image_size_non_square(self):
        """Test force_image_size with a non-square image"""
        resized_img = force_image_size(self.rect_too_wide)
        self.assertEqual(resized_img.size, self.expected_size)

        resized_img = force_image_size(self.rect_too_tall)
        self.assertEqual(resized_img.size, self.expected_size)

        resized_img = force_image_size(self.rect_not_wide)
        self.assertEqual(resized_img.size, self.expected_size)

        resized_img = force_image_size(self.rect_not_tall)
        self.assertEqual(resized_img.size, self.expected_size)

    def test_resize_uploaded_image_returns_png_and_keeps_name(self):
        uploaded = self.get_uploaded_file(name="avatar.jpg", image=self.rect_large)

        resized_file = resize_uploaded_image(uploaded, width=100, height=80)

        self.assertEqual(resized_file.name, uploaded.name)
        with Image.open(BytesIO(resized_file.read())) as resized_image:
            self.assertEqual(resized_image.size, (100, 80))
            self.assertEqual(resized_image.format, "PNG")

    def test_resize_uploaded_image_uses_default_dimensions(self):
        uploaded = self.get_uploaded_file(image=self.rect_small)

        resized_file = resize_uploaded_image(uploaded)

        with Image.open(BytesIO(resized_file.read())) as resized_image:
            self.assertEqual(resized_image.size, self.expected_size)

    def test_resize_uploaded_image_raises_for_invalid_image(self):
        uploaded = self.create_test_file(
            name="not-an-image.txt",
            content=b"this is not image data",
            content_type="text/plain",
        )

        with self.assertRaises(PIL.UnidentifiedImageError):
            resize_uploaded_image(uploaded)
