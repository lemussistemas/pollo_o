from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from .models import Cliente, DiaRuta, Equipo, EstadoEquipo, PuntoVenta

User = get_user_model()
CREDIT_FIELDS = ("credito_habilitado", "limite_credito")


def pair_or_empty(latitud, longitud, label):
    if (latitud is None) ^ (longitud is None):
        raise serializers.ValidationError(f"{label}: indica latitud y longitud juntas.")
    for value, name in ((latitud, "latitud"), (longitud, "longitud")):
        if value is None:
            continue
        if name == "latitud" and not Decimal("-90") <= value <= Decimal("90"):
            raise serializers.ValidationError("La latitud debe estar entre -90 y 90.")
        if name == "longitud" and not Decimal("-180") <= value <= Decimal("180"):
            raise serializers.ValidationError("La longitud debe estar entre -180 y 180.")


class PuntoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PuntoVenta
        fields = ("id", "code", "name")


class VendedorBriefSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "full_name")

    def get_full_name(self, user):
        return user.get_full_name().strip() or user.username


class EquipoSerializer(serializers.ModelSerializer):
    foto = serializers.SerializerMethodField()

    class Meta:
        model = Equipo
        fields = (
            "id",
            "modelo",
            "placa",
            "foto",
            "ubicacion",
            "latitud",
            "longitud",
            "estado",
            "ubicacion_bloqueada",
            "retirado_en",
        )

    def get_foto(self, equipo):
        if not equipo.foto:
            return ""
        return equipo.foto.url


class ClienteSerializer(serializers.ModelSerializer):
    punto = PuntoSerializer(read_only=True)
    vendedor = VendedorBriefSerializer(read_only=True)
    credito_autorizado_por = VendedorBriefSerializer(read_only=True)
    equipos = EquipoSerializer(many=True, read_only=True)
    es_nuevo = serializers.SerializerMethodField()
    dia_ruta_label = serializers.CharField(source="get_dia_ruta_display", read_only=True)

    class Meta:
        model = Cliente
        fields = (
            "id",
            "codigo",
            "nombre",
            "rtn",
            "telefono",
            "direccion",
            "punto",
            "dia_ruta",
            "dia_ruta_label",
            "vendedor",
            "latitud",
            "longitud",
            "credito_habilitado",
            "limite_credito",
            "credito_autorizado_por",
            "credito_autorizado_en",
            "notas",
            "activo",
            "es_nuevo",
            "creado_en",
            "equipos",
        )

    def get_es_nuevo(self, cliente):
        return cliente.creado_en >= timezone.now() - timedelta(days=7)


class ClienteWriteSerializer(serializers.ModelSerializer):
    punto_id = serializers.PrimaryKeyRelatedField(source="punto", queryset=PuntoVenta.objects.all())
    vendedor_id = serializers.PrimaryKeyRelatedField(
        source="vendedor",
        queryset=User.objects.filter(role__code="vendedor", is_active=True),
        allow_null=True,
        required=False,
    )
    limite_credito = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )

    class Meta:
        model = Cliente
        fields = (
            "nombre",
            "rtn",
            "telefono",
            "direccion",
            "punto_id",
            "dia_ruta",
            "vendedor_id",
            "latitud",
            "longitud",
            "credito_habilitado",
            "limite_credito",
            "notas",
            "activo",
        )
        extra_kwargs = {
            "dia_ruta": {"required": False, "allow_blank": True},
            "rtn": {"required": False, "allow_blank": True},
            "telefono": {"required": False, "allow_blank": True},
            "direccion": {"required": False, "allow_blank": True},
            "notas": {"required": False, "allow_blank": True},
            "credito_habilitado": {"required": False},
            "activo": {"required": False},
            "latitud": {"required": False, "allow_null": True},
            "longitud": {"required": False, "allow_null": True},
        }

    def validate_nombre(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("El nombre es obligatorio.")
        return value

    def validate_dia_ruta(self, value):
        if value and value not in DiaRuta.values:
            raise serializers.ValidationError("Ese día de ruta no existe.")
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        instance = self.instance
        latitud = attrs.get("latitud", instance.latitud if instance else None)
        longitud = attrs.get("longitud", instance.longitud if instance else None)
        pair_or_empty(latitud, longitud, "Ubicación del cliente")

        current_enabled = instance.credito_habilitado if instance else False
        current_limit = instance.limite_credito if instance else None
        next_enabled = attrs.get("credito_habilitado", current_enabled)
        next_limit = attrs.get("limite_credito", current_limit)
        credit_changed = next_enabled != current_enabled or next_limit != current_limit
        if credit_changed and not user.has_access("clientes.credito", "operate"):
            raise serializers.ValidationError("Solo gerencia puede autorizar o quitar el crédito.")
        if next_enabled and (next_limit is None or next_limit <= 0):
            raise serializers.ValidationError({"limite_credito": "Indica un límite de crédito mayor que cero."})
        if not next_enabled:
            attrs["limite_credito"] = None
        attrs["_credit_changed"] = credit_changed
        return attrs

    def create(self, validated_data):
        credit_changed = validated_data.pop("_credit_changed", False)
        cliente = Cliente(**validated_data)
        cliente.creado_por = self.context["request"].user
        if credit_changed:
            cliente.credito_autorizado_por = self.context["request"].user
            cliente.credito_autorizado_en = timezone.now()
        cliente.save()
        return cliente

    def update(self, instance, validated_data):
        credit_changed = validated_data.pop("_credit_changed", False)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if credit_changed:
            instance.credito_autorizado_por = self.context["request"].user
            instance.credito_autorizado_en = timezone.now()
        instance.save()
        return instance


class EquipoWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipo
        fields = ("modelo", "placa", "foto", "ubicacion", "latitud", "longitud", "estado")
        extra_kwargs = {
            "placa": {"required": False, "allow_blank": True},
            "foto": {"required": False, "allow_null": True},
            "ubicacion": {"required": False, "allow_blank": True},
            "latitud": {"required": False, "allow_null": True},
            "longitud": {"required": False, "allow_null": True},
            "estado": {"required": False},
        }

    def validate_modelo(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("El modelo del equipo es obligatorio.")
        return value

    def validate_estado(self, value):
        if value not in EstadoEquipo.values:
            raise serializers.ValidationError("Ese estado no existe.")
        return value

    def validate(self, attrs):
        instance = self.instance
        latitud = attrs.get("latitud", instance.latitud if instance else None)
        longitud = attrs.get("longitud", instance.longitud if instance else None)
        pair_or_empty(latitud, longitud, "Ubicación del equipo")
        reinstalling = (
            instance
            and instance.estado == EstadoEquipo.RETIRADO
            and attrs.get("estado") == EstadoEquipo.INSTALADO
        )
        if instance and instance.ubicacion_bloqueada and not reinstalling:
            for field in ("ubicacion", "latitud", "longitud"):
                if field not in attrs:
                    continue
                if attrs[field] != getattr(instance, field):
                    raise serializers.ValidationError(
                        "La ubicación quedó cerrada cuando se retiró el equipo."
                    )
        return attrs
