from django.urls import path

from .views import (
    ClienteAvisosView,
    ClienteDetailView,
    ClienteListCreateView,
    ClienteOpcionesView,
    EquipoDetailView,
    EquipoListCreateView,
)

urlpatterns = [
    path("clientes/opciones/", ClienteOpcionesView.as_view()),
    path("clientes/avisos/", ClienteAvisosView.as_view()),
    path("clientes/", ClienteListCreateView.as_view()),
    path("clientes/<int:pk>/", ClienteDetailView.as_view()),
    path("clientes/<int:cliente_id>/equipos/", EquipoListCreateView.as_view()),
    path("clientes/<int:cliente_id>/equipos/<int:pk>/", EquipoDetailView.as_view()),
]
