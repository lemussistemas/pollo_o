from decimal import Decimal

from rest_framework import serializers

from clientes.models import Cliente

from .models import PrecioCliente, Producto, UnidadMedida


def precios_visibles(user, producto):
    precios = producto.precios.all()
    level = user.access_map().get("productos.ver", "none")
    if level == "own" and not user.has_access("productos.precios", "operate"):
        return [precio for precio in precios if precio.cliente.vendedor_id == user.id]
    return list(precios)


class PrecioClienteSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="cliente.nombre", read_only=True)
    cliente_codigo = serializers.CharField(source="cliente.codigo", read_only=True)

    class Meta:
        model = PrecioCliente
        fields = ["id", "cliente", "cliente_nombre", "cliente_codigo", "precio", "actualizado_en"]


class ProductoSerializer(serializers.ModelSerializer):
    unidad_label = serializers.CharField(source="get_unidad_display", read_only=True)
    precios = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = [
            "id",
            "codigo",
            "nombre",
            "unidad",
            "unidad_label",
            "precio_base",
            "controla_lote",
            "activo",
            "notas",
            "precios",
        ]

    def get_precios(self, producto):
        visibles = precios_visibles(self.context["request"].user, producto)
        return PrecioClienteSerializer(visibles, many=True).data


class ProductoWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = ["nombre", "unidad", "precio_base", "controla_lote", "activo", "notas"]

    def validate_unidad(self, value):
        if value not in UnidadMedida.values:
            raise serializers.ValidationError("La unidad es unidad o libra.")
        return value

    def validate_precio_base(self, value):
        if value < 0:
            raise serializers.ValidationError("El precio de lista no puede ser negativo.")
        return value


class PrecioWriteSerializer(serializers.ModelSerializer):
    cliente_id = serializers.PrimaryKeyRelatedField(source="cliente", queryset=Cliente.objects.all())

    class Meta:
        model = PrecioCliente
        fields = ["cliente_id", "precio"]

    def validate_precio(self, value):
        if value <= Decimal("0"):
            raise serializers.ValidationError("El precio del cliente tiene que ser mayor que cero.")
        return value
