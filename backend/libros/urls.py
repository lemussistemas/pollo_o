from django.urls import path

from .views import (
    CierreListView,
    DocumentoListView,
    LibroResumenView,
    ProveedorListView,
    VendedorReporteListView,
)

urlpatterns = [
    path("libros/resumen/", LibroResumenView.as_view(), name="libros-resumen"),
    path("libros/documentos/", DocumentoListView.as_view(), name="libros-documentos"),
    path("libros/proveedores/", ProveedorListView.as_view(), name="libros-proveedores"),
    path("libros/vendedores/", VendedorReporteListView.as_view(), name="libros-vendedores"),
    path("libros/cierres/", CierreListView.as_view(), name="libros-cierres"),
]
