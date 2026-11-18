from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import require_access
from clientes.models import Cliente

from .models import PrecioCliente, Producto, UnidadMedida
from .serializers import PrecioWriteSerializer, ProductoSerializer, ProductoWriteSerializer


class ProductoPagination(PageNumberPagination):
    page_size = 25


def productos_queryset():
    return Producto.objects.prefetch_related("precios__cliente")


class ProductoOpcionesView(APIView):
    permission_classes = [IsAuthenticated, require_access("productos.ver")]

    def get(self, request):
        payload = {"unidades": [{"code": code, "name": label} for code, label in UnidadMedida.choices]}
        if request.user.has_access("productos.precios", "operate"):
            payload["clientes"] = [
                {"id": client.id, "nombre": client.nombre, "codigo": client.codigo}
                for client in Cliente.objects.filter(activo=True).order_by("nombre")
            ]
        return Response(payload)


class ProductoListCreateView(generics.ListCreateAPIView):
    pagination_class = ProductoPagination

    def get_permissions(self):
        if self.request.method == "POST":
            permission = require_access("productos.gestionar", "operate")
        else:
            permission = require_access("productos.ver")
        return [IsAuthenticated(), permission()]

    def get_queryset(self):
        queryset = productos_queryset()
        params = self.request.query_params
        query = params.get("q", "").strip()
        if query:
            queryset = queryset.filter(Q(nombre__icontains=query) | Q(codigo__icontains=query))
        if params.get("unidad"):
            queryset = queryset.filter(unidad=params["unidad"])
        if params.get("activos") == "1":
            queryset = queryset.filter(activo=True)
        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProductoWriteSerializer
        return ProductoSerializer

    def create(self, request, *args, **kwargs):
        write = ProductoWriteSerializer(data=request.data)
        write.is_valid(raise_exception=True)
        product = write.save()
        product = productos_queryset().get(pk=product.pk)
        return Response(ProductoSerializer(product, context={"request": request}).data, status=status.HTTP_201_CREATED)


class ProductoDetailView(generics.RetrieveUpdateAPIView):
    def get_permissions(self):
        if self.request.method == "GET":
            permission = require_access("productos.ver")
        else:
            permission = require_access("productos.gestionar", "operate")
        return [IsAuthenticated(), permission()]

    def get_queryset(self):
        return productos_queryset()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ProductoSerializer
        return ProductoWriteSerializer

    def update(self, request, *args, **kwargs):
        product = self.get_object()
        write = ProductoWriteSerializer(product, data=request.data, partial=True)
        write.is_valid(raise_exception=True)
        write.save()
        product = productos_queryset().get(pk=product.pk)
        return Response(ProductoSerializer(product, context={"request": request}).data)


class PrecioListCreateView(APIView):
    permission_classes = [IsAuthenticated, require_access("productos.precios", "operate")]

    def post(self, request, producto_id):
        product = get_object_or_404(Producto, pk=producto_id)
        write = PrecioWriteSerializer(data=request.data)
        write.is_valid(raise_exception=True)
        PrecioCliente.objects.update_or_create(
            producto=product,
            cliente=write.validated_data["cliente"],
            defaults={"precio": write.validated_data["precio"]},
        )
        product = productos_queryset().get(pk=product.pk)
        return Response(ProductoSerializer(product, context={"request": request}).data, status=status.HTTP_200_OK)


class PrecioDetailView(APIView):
    permission_classes = [IsAuthenticated, require_access("productos.precios", "operate")]

    def delete(self, request, producto_id, pk):
        price = get_object_or_404(PrecioCliente, pk=pk, producto_id=producto_id)
        price.delete()
        product = productos_queryset().get(pk=producto_id)
        return Response(ProductoSerializer(product, context={"request": request}).data)
