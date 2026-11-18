from django.urls import path

from .views import BodegaOpcionesView, ExistenciaListView, MovimientoListCreateView

urlpatterns = [
    path("bodega/opciones/", BodegaOpcionesView.as_view(), name="bodega-opciones"),
    path("bodega/existencias/", ExistenciaListView.as_view(), name="bodega-existencias"),
    path("bodega/movimientos/", MovimientoListCreateView.as_view(), name="bodega-movimientos"),
]
