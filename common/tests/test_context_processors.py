from django.conf import settings

from ..cases import BaseTestCase


class SiteNameContextProcessorTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()

    def test_site_name_context_processor(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("site_name", response.context)
        self.assertEqual(response.context["site_name"], settings.SITE_NAME)
