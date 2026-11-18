from django.contrib import admin

from .models import PrecioCliente, Producto


class PrecioClienteInline(admin.TabularInline):
    model = PrecioCliente
    extra = 0


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "unidad", "precio_base", "controla_lote", "activo")
    list_filter = ("unidad", "controla_lote", "activo")
    search_fields = ("nombre", "codigo")
    inlines = [PrecioClienteInline]
