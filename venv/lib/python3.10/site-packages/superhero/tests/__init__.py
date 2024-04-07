from django.test import TestCase as BaseTestCase
from django.test.client import Client as BaseClient, RequestFactory
from django.contrib.auth.models import User

from superhero.models import Superhero


class TestCase(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        cls.request = RequestFactory()
        cls.client = BaseClient()

        # Editor
        cls.editor, dc = User.objects.get_or_create(
            username='editor',
            email='editor@test.com'
        )
        cls.editor.set_password("password")
        cls.editor.save()

        # Superhero
        obj, dc = Superhero.objects.get_or_create(
            title='Superhero',
            owner=cls.editor, state='published',
        )
        obj.sites = [1]
        obj.save()
        cls.superhero = obj

    def test_pagination(self):
        response = self.client.get(self.superhero.get_absolute_url())
        self.assertEquals(response.code, 200)
