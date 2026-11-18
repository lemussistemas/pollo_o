from django.db import transaction
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import require_access
from productos.models import Producto

from .models import Existencia, Movimiento, TipoMovimiento
from .serializers import ExistenciaSerializer, MovimientoSerializer, MovimientoWriteSerializer
from .services import StockError, aplicar_movimiento


class MovimientoPagination(PageNumberPagination):
    page_size = 25


class BodegaOpcionesView(APIView):
    permission_classes = [IsAuthenticated, require_access("inventario.ingreso")]

    def get(self, request):
        products = Producto.objects.filter(activo=True).order_by("nombre")
        return Response(
            {
                "productos": [
                    {
                        "id": product.id,
                        "nombre": product.nombre,
                        "codigo": product.codigo,
                        "unidad": product.unidad,
                        "unidad_label": product.get_unidad_display(),
                        "controla_lote": product.controla_lote,
                    }
                    for product in products
                ]
            }
        )


class ExistenciaListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, require_access("inventario.ingreso")]
    serializer_class = ExistenciaSerializer
    pagination_class = None

    def get_queryset(self):
        return Existencia.objects.select_related("producto").filter(cantidad__gt=0)


class MovimientoListCreateView(generics.ListCreateAPIView):
    pagination_class = MovimientoPagination

    def get_permissions(self):
        return [IsAuthenticated(), require_access("inventario.ingreso")()]

    def get_queryset(self):
        return Movimiento.objects.select_related("producto", "creado_por")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return MovimientoWriteSerializer
        return MovimientoSerializer

    def create(self, request, *args, **kwargs):
        write = MovimientoWriteSerializer(data=request.data)
        write.is_valid(raise_exception=True)
        tipo = write.validated_data["tipo"]
        if tipo == TipoMovimiento.INGRESO and not request.user.has_access("inventario.ingreso", "operate"):
            raise PermissionDenied("No tienes permiso para esta acción.")
        if tipo == TipoMovimiento.SALIDA_DANADO and not request.user.has_access("inventario.mal_estado", "operate"):
            raise PermissionDenied("No tienes permiso para esta acción.")
        with transaction.atomic():
            movimiento = write.save(creado_por=request.user)
            try:
                aplicar_movimiento(movimiento)
            except StockError as exc:
                raise ValidationError({"cantidad": exc.message}) from exc
        movimiento = Movimiento.objects.select_related("producto", "creado_por").get(pk=movimiento.pk)
        return Response(MovimientoSerializer(movimiento).data, status=status.HTTP_201_CREATED)
