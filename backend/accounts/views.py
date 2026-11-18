from django.contrib.auth import authenticate
from django.db.models import Count, Q
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .catalog import NOMBRE, POLITICA_DEVOLUCION, PUNTOS, VEHICULOS, flujo_for
from .models import Role, User
from .permissions import require_access
from .serializers import RoleSerializer, UserSerializer, UserWriteSerializer


class LoginView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        username = str(request.data.get("username") or "").strip()
        password = request.data.get("password") or ""
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {"detail": "Usuario o contraseña incorrectos."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if user.role_id is None:
            return Response(
                {"detail": "Este usuario no tiene rol. Pide a gerencia que le asigne uno."},
                status=status.HTTP_403_FORBIDDEN,
            )
        user = User.objects.with_access().get(pk=user.pk)
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            }
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = User.objects.with_access().get(pk=request.user.pk)
        return Response(UserSerializer(user).data)


class SistemaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = User.objects.with_access().get(pk=request.user.pk)
        return Response(
            {
                "nombre": NOMBRE,
                "puntos_de_venta": len(PUNTOS),
                "puntos": PUNTOS,
                "vehiculos": VEHICULOS,
                "politica_devolucion": POLITICA_DEVOLUCION,
                "flujo": flujo_for(user),
            }
        )


class RoleListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RoleSerializer

    def get_queryset(self):
        return (
            Role.objects.annotate(
                active_users=Count("users", filter=Q(users__is_active=True))
            )
            .prefetch_related("grants__permission")
            .order_by("sort_order")
        )


class UserListCreateView(generics.ListCreateAPIView):
    def get_permissions(self):
        if self.request.method == "POST":
            permission = require_access("usuarios.gestionar", "operate")
        else:
            permission = require_access("usuarios.ver", "view")
        return [IsAuthenticated(), permission()]

    def get_queryset(self):
        return User.objects.with_access().order_by("first_name", "last_name", "username")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return UserWriteSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user = User.objects.with_access().get(pk=user.pk)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.with_access()
    http_method_names = ["get", "patch", "head", "options"]

    def get_permissions(self):
        if self.request.method == "PATCH":
            permission = require_access("usuarios.gestionar", "operate")
        else:
            permission = require_access("usuarios.ver", "view")
        return [IsAuthenticated(), permission()]

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return UserWriteSerializer
        return UserSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user = User.objects.with_access().get(pk=user.pk)
        return Response(UserSerializer(user).data)
