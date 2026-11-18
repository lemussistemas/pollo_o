from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    LoginView,
    MeView,
    RoleListView,
    SistemaView,
    UserDetailView,
    UserListCreateView,
)

urlpatterns = [
    path("auth/login/", LoginView.as_view()),
    path("auth/refresh/", TokenRefreshView.as_view()),
    path("auth/me/", MeView.as_view()),
    path("sistema/", SistemaView.as_view()),
    path("roles/", RoleListView.as_view()),
    path("usuarios/", UserListCreateView.as_view()),
    path("usuarios/<int:pk>/", UserDetailView.as_view()),
]
