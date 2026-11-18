from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from productos.models import Producto

from .models import Existencia, Movimiento, TipoMovimiento


class ExistenciaSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.nombre", read_only=True)
    producto_codigo = serializers.CharField(source="producto.codigo", read_only=True)
    unidad = serializers.CharField(source="producto.unidad", read_only=True)
    unidad_label = serializers.CharField(source="producto.get_unidad_display", read_only=True)

    class Meta:
        model = Existencia
        fields = [
            "id",
            "producto",
            "producto_nombre",
            "producto_codigo",
            "unidad",
            "unidad_label",
            "lote",
            "fecha_vencimiento",
            "cantidad",
        ]


class MovimientoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.nombre", read_only=True)
    unidad_label = serializers.CharField(source="producto.get_unidad_display", read_only=True)
    tipo_label = serializers.CharField(source="get_tipo_display", read_only=True)
    creado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Movimiento
        fields = [
            "id",
            "tipo",
            "tipo_label",
            "producto",
            "producto_nombre",
            "unidad_label",
            "lote",
            "fecha_vencimiento",
            "cantidad",
            "nota",
            "creado_por_nombre",
            "creado_en",
        ]

    def get_creado_por_nombre(self, movimiento):
        user = movimiento.creado_por
        if user is None:
            return ""
        return user.get_full_name().strip() or user.username


class MovimientoWriteSerializer(serializers.ModelSerializer):
    producto_id = serializers.PrimaryKeyRelatedField(
        source="producto",
        queryset=Producto.objects.filter(activo=True),
    )

    class Meta:
        model = Movimiento
        fields = ["tipo", "producto_id", "lote", "fecha_vencimiento", "cantidad", "nota"]

    def validate_tipo(self, value):
        if value not in TipoMovimiento.values:
            raise serializers.ValidationError("El movimiento es un ingreso o una salida por dañado.")
        return value

    def validate_cantidad(self, value):
        if value <= Decimal("0"):
            raise serializers.ValidationError("La cantidad tiene que ser mayor que cero.")
        return value

    def validate(self, attrs):
        producto = attrs["producto"]
        lote = (attrs.get("lote") or "").strip()
        fecha = attrs.get("fecha_vencimiento")
        if producto.controla_lote:
            errors = {}
            if not lote:
                errors["lote"] = "Este producto lleva lote."
            if fecha is None:
                errors["fecha_vencimiento"] = "Indica el vencimiento."
            elif fecha < timezone.localdate():
                errors["fecha_vencimiento"] = "El vencimiento ya pasó."
            if errors:
                raise serializers.ValidationError(errors)
        elif lote or fecha:
            raise serializers.ValidationError("Este producto no lleva lote ni vencimiento.")
        attrs["lote"] = lote
        attrs["fecha_vencimiento"] = fecha
        return attrs
