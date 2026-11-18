from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
    verbose_name = "Usuarios y roles"

    def ready(self):
        from django.contrib import admin

        admin.site.site_header = "Distribuidora Pollo Rey"
        admin.site.site_title = "Distribuidora"
        admin.site.index_title = "Administración"
