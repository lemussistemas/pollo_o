from django.contrib import admin

from .models import CierreDiario, CompraMensual, DocumentoVenta, EmpresaFiscal, Proveedor, VendedorReporte, VentaMensual


class CompraMensualInline(admin.TabularInline):
    model = CompraMensual
    extra = 0


class VentaMensualInline(admin.TabularInline):
    model = VentaMensual
    extra = 0


@admin.register(EmpresaFiscal)
class EmpresaFiscalAdmin(admin.ModelAdmin):
    list_display = ("razon_social", "desde", "hasta")


@admin.register(DocumentoVenta)
class DocumentoVentaAdmin(admin.ModelAdmin):
    list_display = ("fecha", "serie", "numero", "cliente", "condicion", "total", "estado")
    list_filter = ("caja", "condicion", "estado", "tipo")
    search_fields = ("cliente", "numero", "rtn", "serie")
    date_hierarchy = "fecha"


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    inlines = [CompraMensualInline]


@admin.register(VendedorReporte)
class VendedorReporteAdmin(admin.ModelAdmin):
    inlines = [VentaMensualInline]


@admin.register(CierreDiario)
class CierreDiarioAdmin(admin.ModelAdmin):
    list_display = ("fecha", "numero", "factura_desde", "factura_hasta", "total")
