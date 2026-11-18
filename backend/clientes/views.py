from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import require_access

from .models import Cliente, DiaRuta, Equipo, PuntoVenta
from .serializers import ClienteSerializer, ClienteWriteSerializer, EquipoSerializer, EquipoWriteSerializer


class ClientePagination(PageNumberPagination):
    page_size = 25


def clientes_para(user):
    queryset = Cliente.objects.select_related("punto", "vendedor", "credito_autorizado_por").prefetch_related("equipos")
    level = user.access_map().get("clientes.ver", "none")
    if level == "own":
        return queryset.filter(vendedor=user)
    if user.has_access("clientes.ver", "view"):
        return queryset
    return queryset.none()


class ClienteOpcionesView(APIView):
    permission_classes = [IsAuthenticated, require_access("clientes.ver", "view")]

    def get(self, request):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        payload = {
            "puntos": [
                {"id": point.id, "code": point.code, "name": point.name}
                for point in PuntoVenta.objects.all()
            ],
            "dias": [{"code": code, "name": label} for code, label in DiaRuta.choices],
            "nuevos": clientes_para(request.user).filter(
                activo=True,
                creado_en__gte=timezone.now() - timedelta(days=7),
            ).count(),
        }
        if request.user.has_access("clientes.gestionar", "operate"):
            payload["vendedores"] = [
                {"id": seller.id, "full_name": seller.get_full_name().strip() or seller.username}
                for seller in User.objects.filter(role__code="vendedor", is_active=True).order_by("first_name", "username")
            ]
        return Response(payload)


class ClienteAvisosView(APIView):
    permission_classes = [IsAuthenticated, require_access("clientes.ver", "view")]

    def get(self, request):
        nuevos = clientes_para(request.user).filter(
            activo=True,
            creado_en__gte=timezone.now() - timedelta(days=7),
        ).count()
        return Response({"nuevos": nuevos, "dias": 7})


class ClienteListCreateView(generics.ListCreateAPIView):
    pagination_class = ClientePagination

    def get_permissions(self):
        if self.request.method == "POST":
            permission = require_access("clientes.gestionar", "operate")
        else:
            permission = require_access("clientes.ver", "view")
        return [IsAuthenticated(), permission()]

    def get_queryset(self):
        queryset = clientes_para(self.request.user)
        params = self.request.query_params
        text = (params.get("q") or "").strip()
        if text:
            queryset = queryset.filter(
                Q(nombre__icontains=text)
                | Q(rtn__icontains=text)
                | Q(telefono__icontains=text)
                | Q(codigo__icontains=text)
            )
        if params.get("punto"):
            queryset = queryset.filter(punto_id=params.get("punto"))
        if params.get("dia"):
            queryset = queryset.filter(dia_ruta=params.get("dia"))
        if params.get("credito") == "si":
            queryset = queryset.filter(credito_habilitado=True)
        elif params.get("credito") == "no":
            queryset = queryset.filter(credito_habilitado=False)
        if params.get("nuevos") == "1":
            queryset = queryset.filter(creado_en__gte=timezone.now() - timedelta(days=7))
        return queryset.order_by("nombre")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ClienteWriteSerializer
        return ClienteSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cliente = serializer.save()
        cliente = clientes_para(request.user).get(pk=cliente.pk)
        return Response(ClienteSerializer(cliente, context={"request": request}).data, status=status.HTTP_201_CREATED)


class ClienteDetailView(generics.RetrieveUpdateAPIView):
    http_method_names = ["get", "patch", "head", "options"]

    def get_permissions(self):
        if self.request.method == "PATCH":
            permission = require_access("clientes.gestionar", "operate")
        else:
            permission = require_access("clientes.ver", "view")
        return [IsAuthenticated(), permission()]

    def get_queryset(self):
        return clientes_para(self.request.user)

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return ClienteWriteSerializer
        return ClienteSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        cliente = serializer.save()
        cliente = Cliente.objects.select_related("punto", "vendedor", "credito_autorizado_por").prefetch_related("equipos").get(pk=cliente.pk)
        return Response(ClienteSerializer(cliente, context={"request": request}).data)


class EquipoListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, require_access("clientes.gestionar", "operate")]

    def get_cliente(self):
        queryset = Cliente.objects.all()
        if self.request.user.access_map().get("clientes.ver") == "own":
            queryset = queryset.filter(vendedor=self.request.user)
        return generics.get_object_or_404(queryset, pk=self.kwargs["cliente_id"])

    def get_queryset(self):
        return Equipo.objects.filter(cliente=self.get_cliente())

    def get_serializer_class(self):
        if self.request.method == "POST":
            return EquipoWriteSerializer
        return EquipoSerializer

    def perform_create(self, serializer):
        serializer.save(cliente=self.get_cliente())

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        equipo = serializer.save(cliente=self.get_cliente())
        return Response(EquipoSerializer(equipo, context={"request": request}).data, status=status.HTTP_201_CREATED)


class EquipoDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, require_access("clientes.gestionar", "operate")]
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        return Equipo.objects.filter(cliente_id=self.kwargs["cliente_id"])

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return EquipoWriteSerializer
        return EquipoSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        equipo = serializer.save()
        return Response(EquipoSerializer(equipo, context={"request": request}).data)
