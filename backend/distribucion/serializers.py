from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Carga, CargaLinea, Vehiculo

User = get_user_model()


class VehiculoSerializer(serializers.ModelSerializer):
    tipo_label = serializers.CharField(source="get_tipo_display", read_only=True)
    vendedor_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Vehiculo
        fields = ["id", "codigo", "nombre", "tipo", "tipo_label", "vendedor", "vendedor_nombre", "activo"]

    def get_vendedor_nombre(self, vehiculo):
        seller = vehiculo.vendedor
        if seller is None:
            return ""
        return seller.get_full_name().strip() or seller.username


class VehiculoAssignSerializer(serializers.ModelSerializer):
    vendedor_id = serializers.PrimaryKeyRelatedField(
        source="vendedor",
        queryset=User.objects.filter(role__code="vendedor", is_active=True),
        allow_null=True,
    )

    class Meta:
        model = Vehiculo
        fields = ["vendedor_id"]


class CargaLineaSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.nombre", read_only=True)
    unidad = serializers.CharField(source="producto.unidad", read_only=True)
    unidad_label = serializers.CharField(source="producto.get_unidad_display", read_only=True)

    class Meta:
        model = CargaLinea
        fields = [
            "id",
            "producto",
            "producto_nombre",
            "unidad",
            "unidad_label",
            "lote",
            "fecha_vencimiento",
            "cantidad",
        ]


class CargaSerializer(serializers.ModelSerializer):
    vehiculo_nombre = serializers.CharField(source="vehiculo.nombre", read_only=True)
    lineas = CargaLineaSerializer(many=True, read_only=True)

    class Meta:
        model = Carga
        fields = ["id", "vehiculo", "vehiculo_nombre", "fecha", "nota", "lineas", "creado_en"]


class CargaWriteSerializer(serializers.Serializer):
    vehiculo_id = serializers.PrimaryKeyRelatedField(source="vehiculo", queryset=Vehiculo.objects.filter(activo=True))
    fecha = serializers.DateField()
    nota = serializers.CharField(required=False, allow_blank=True, max_length=200)


class LineaWriteSerializer(serializers.Serializer):
    existencia_id = serializers.IntegerField()
    cantidad = serializers.DecimalField(max_digits=14, decimal_places=3)
