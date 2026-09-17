from django.contrib import admin
from .models import AboutContent


@admin.register(AboutContent)
class AboutContentAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not AboutContent.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
