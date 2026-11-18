from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import require_access
from bodega.services import StockError

from .models import Carga, Vehiculo
from .serializers import CargaSerializer, CargaWriteSerializer, LineaWriteSerializer, VehiculoAssignSerializer, VehiculoSerializer
from .services import agregar_linea


def puede_operar(user):
    return user.has_access("distribucion.carga", "operate")


def vehiculos_para(user):
    queryset = Vehiculo.objects.filter(activo=True).select_related("vendedor")
    level = user.access_map().get("distribucion.carga", "none")
    if level == "own" and not puede_operar(user):
        return queryset.filter(vendedor=user)
    if user.has_access("distribucion.carga"):
        return queryset
    return queryset.none()


def cargas_para(user):
    return Carga.objects.filter(vehiculo__in=vehiculos_para(user)).select_related("vehiculo").prefetch_related("lineas__producto")


class VehiculoListView(APIView):
    permission_classes = [IsAuthenticated, require_access("distribucion.carga")]

    def get(self, request):
        vehicles = VehiculoSerializer(vehiculos_para(request.user), many=True).data
        payload = {"vehiculos": vehicles}
        if puede_operar(request.user):
            from django.contrib.auth import get_user_model

            User = get_user_model()
            payload["vendedores"] = [
                {"id": seller.id, "full_name": seller.get_full_name().strip() or seller.username}
                for seller in User.objects.filter(role__code="vendedor", is_active=True).order_by("first_name", "username")
            ]
        return Response(payload)


class VehiculoDetailView(APIView):
    permission_classes = [IsAuthenticated, require_access("distribucion.carga", "operate")]

    def patch(self, request, pk):
        vehicle = get_object_or_404(vehiculos_para(request.user), pk=pk)
        write = VehiculoAssignSerializer(vehicle, data=request.data, partial=True)
        write.is_valid(raise_exception=True)
        write.save()
        vehicle = vehiculos_para(request.user).get(pk=vehicle.pk)
        return Response(VehiculoSerializer(vehicle).data)


class CargaListCreateView(APIView):
    permission_classes = [IsAuthenticated, require_access("distribucion.carga")]

    def get(self, request):
        queryset = cargas_para(request.user)
        if request.query_params.get("vehiculo"):
            queryset = queryset.filter(vehiculo_id=request.query_params["vehiculo"])
        if request.query_params.get("fecha"):
            queryset = queryset.filter(fecha=request.query_params["fecha"])
        return Response(CargaSerializer(queryset, many=True).data)

    def post(self, request):
        if not puede_operar(request.user):
            raise PermissionDenied("No tienes permiso para esta acción.")
        write = CargaWriteSerializer(data=request.data)
        write.is_valid(raise_exception=True)
        vehicle = get_object_or_404(vehiculos_para(request.user), pk=write.validated_data["vehiculo"].pk)
        carga, created = Carga.objects.get_or_create(
            vehiculo=vehicle,
            fecha=write.validated_data["fecha"],
            defaults={"nota": write.validated_data.get("nota", ""), "creado_por": request.user},
        )
        carga = cargas_para(request.user).get(pk=carga.pk)
        return Response(CargaSerializer(carga).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class CargaLineaCreateView(APIView):
    permission_classes = [IsAuthenticated, require_access("distribucion.carga", "operate")]

    def post(self, request, carga_id):
        carga = get_object_or_404(cargas_para(request.user), pk=carga_id)
        write = LineaWriteSerializer(data=request.data)
        write.is_valid(raise_exception=True)
        try:
            agregar_linea(carga, write.validated_data["existencia_id"], write.validated_data["cantidad"], request.user)
        except StockError as exc:
            raise ValidationError({"cantidad": exc.message}) from exc
        carga = cargas_para(request.user).get(pk=carga.pk)
        return Response(CargaSerializer(carga).data, status=status.HTTP_201_CREATED)
