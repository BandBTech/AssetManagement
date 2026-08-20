from django.contrib import admin

# # Register your models here.
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [field.name for field in User._meta.concrete_fields]


#     # list_filter = ('is_staff', 'is_active', 'is_superuser', 'is_email_verified', 'role')
#     # search_fields = ('username', 'email', 'first_name', 'last_name')
#     # ordering = ('username',)
#     # filter_horizontal = ('groups', 'user_permissions')
#     # readonly_fields = ('date_joined',)
