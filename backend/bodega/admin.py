from django.contrib import admin

from .models import Existencia, Movimiento


@admin.register(Existencia)
class ExistenciaAdmin(admin.ModelAdmin):
    list_display = ("producto", "lote", "fecha_vencimiento", "cantidad")
    search_fields = ("producto__nombre", "lote")


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ("creado_en", "tipo", "producto", "lote", "cantidad", "creado_por")
    list_filter = ("tipo",)
    search_fields = ("producto__nombre", "lote", "nota")
