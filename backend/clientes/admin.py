from django.contrib import admin

from .models import Cliente, Equipo, PuntoVenta


class EquipoInline(admin.TabularInline):
    model = Equipo
    extra = 0


@admin.register(PuntoVenta)
class PuntoVentaAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "sort_order")


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "punto", "dia_ruta", "vendedor", "credito_habilitado", "activo")
    list_filter = ("punto", "dia_ruta", "credito_habilitado", "activo")
    search_fields = ("nombre", "rtn", "codigo", "telefono")
    inlines = [EquipoInline]
