from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from apps.users.models import User


class CustomUserCreationForm(UserCreationForm):
    """Form for creating new users with password handling."""

    class Meta:
        model = User
        fields = ("email", "name", "role", "organization", "phone_number")


class CustomUserChangeForm(UserChangeForm):
    """Form for updating users with password handling."""

    class Meta:
        model = User
        fields = (
            "email",
            "name",
            "role",
            "organization",
            "phone_number",
            "profile_picture",
            "is_active",
            "is_staff",
        )


class UserAdmin(BaseUserAdmin):
    """Custom admin for User model with proper password handling."""

    # Forms to use for creating and changing users
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm

    # Fields to display in the user list
    list_display = (
        "email",
        "name",
        "role",
        "organization",
        "is_active",
        "is_staff",
        "created_at",
    )
    list_filter = ("role", "is_active", "is_staff", "organization")
    search_fields = ("email", "name")
    ordering = ("-created_at",)

    # Fieldsets for the change user page
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("name", "phone_number", "profile_picture")}),
        ("Organization & Role", {"fields": ("organization", "role")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important Dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )

    # Fieldsets for the add user page
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "name",
                    "password1",
                    "password2",
                    "role",
                    "organization",
                    "phone_number",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )

    # Read-only fields
    readonly_fields = ("created_at", "updated_at", "last_login")

    filter_horizontal = ("groups", "user_permissions")


admin.site.register(User, UserAdmin)
