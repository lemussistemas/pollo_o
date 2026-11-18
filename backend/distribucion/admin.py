from django.contrib import admin

from .models import Carga, CargaLinea, Vehiculo


class CargaLineaInline(admin.TabularInline):
    model = CargaLinea
    extra = 0


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "vendedor", "activo")


@admin.register(Carga)
class CargaAdmin(admin.ModelAdmin):
    list_display = ("fecha", "vehiculo", "creado_por")
    inlines = [CargaLineaInline]
