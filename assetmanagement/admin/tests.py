from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from admin.permissions import IsSuperUser

User = get_user_model()


class IsSuperUserPermissionTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = IsSuperUser()
        self.superuser = User.objects.create_superuser(
            username="super", email="super@example.com", password="password"
        )
        self.regular_user = User.objects.create_user(
            username="regular", email="regular@example.com", password="password"
        )

    def test_superuser_has_permission(self):
        request = self.factory.get("/")
        request.user = self.superuser
        self.assertTrue(self.permission.has_permission(request, None))

    def test_regular_user_denied_permission(self):
        request = self.factory.get("/")
        request.user = self.regular_user
        self.assertFalse(self.permission.has_permission(request, None))

    def test_anonymous_user_denied_permission(self):
        from django.contrib.auth.models import AnonymousUser
        request = self.factory.get("/")
        request.user = AnonymousUser()
        self.assertFalse(self.permission.has_permission(request, None))
