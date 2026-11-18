from django.urls import path

from .views import PrecioDetailView, PrecioListCreateView, ProductoDetailView, ProductoListCreateView, ProductoOpcionesView

urlpatterns = [
    path("productos/opciones/", ProductoOpcionesView.as_view(), name="productos-opciones"),
    path("productos/", ProductoListCreateView.as_view(), name="productos"),
    path("productos/<int:pk>/", ProductoDetailView.as_view(), name="producto-detail"),
    path("productos/<int:producto_id>/precios/", PrecioListCreateView.as_view(), name="producto-precios"),
    path(
        "productos/<int:producto_id>/precios/<int:pk>/",
        PrecioDetailView.as_view(),
        name="producto-precio-detail",
    ),
]
