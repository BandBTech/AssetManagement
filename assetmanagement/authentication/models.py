from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser, BaseUserManager


class User(AbstractUser):
    email = models.EmailField(
        _("email"),
        unique=True,
        error_messages={"unique": _("A user with that email already exists.")},
    )
    email_verified = models.BooleanField(_("email verified"), default=False)

    class Meta:
        db_table = "auth_user"


# Create your models here.
