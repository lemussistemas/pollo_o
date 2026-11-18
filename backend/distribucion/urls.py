from django.urls import path

from .views import CargaLineaCreateView, CargaListCreateView, VehiculoDetailView, VehiculoListView

urlpatterns = [
    path("distribucion/vehiculos/", VehiculoListView.as_view(), name="vehiculos"),
    path("distribucion/vehiculos/<int:pk>/", VehiculoDetailView.as_view(), name="vehiculo-detail"),
    path("distribucion/cargas/", CargaListCreateView.as_view(), name="cargas"),
    path("distribucion/cargas/<int:carga_id>/lineas/", CargaLineaCreateView.as_view(), name="carga-lineas"),
]
