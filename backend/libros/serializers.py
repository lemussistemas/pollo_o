from rest_framework import serializers

from .models import CierreDiario, DocumentoVenta


class DocumentoVentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentoVenta
        fields = [
            "id",
            "registro",
            "fecha",
            "caja",
            "tipo",
            "serie",
            "numero",
            "cai",
            "fecha_limite",
            "rtn",
            "cliente",
            "condicion",
            "forma_pago",
            "moneda",
            "exenta",
            "exonerada",
            "gravada_15",
            "isv_15",
            "gravada_18",
            "isv_18",
            "descuento",
            "total",
            "estado",
        ]


class CierreDiarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = CierreDiario
        fields = [
            "id",
            "fecha",
            "numero",
            "factura_desde",
            "factura_hasta",
            "concepto",
            "venta_libre",
            "venta_gravada",
            "impuesto",
            "total",
        ]
