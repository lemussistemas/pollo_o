from decimal import Decimal

from django.db import transaction

from bodega.models import Existencia, Movimiento, TipoMovimiento
from bodega.services import StockError, aplicar_movimiento

from .models import CargaLinea


@transaction.atomic
def agregar_linea(carga, existencia_id, cantidad, usuario):
    if cantidad <= Decimal("0"):
        raise StockError("La cantidad tiene que ser mayor que cero.")
    existencia = Existencia.objects.select_for_update().filter(pk=existencia_id, cantidad__gt=0).first()
    if existencia is None or existencia.cantidad < cantidad:
        raise StockError("No hay suficiente existencia para esa carga.")
    linea = CargaLinea.objects.create(
        carga=carga,
        producto=existencia.producto,
        lote=existencia.lote,
        fecha_vencimiento=existencia.fecha_vencimiento,
        cantidad=cantidad,
    )
    movimiento = Movimiento.objects.create(
        tipo=TipoMovimiento.CARGA,
        producto=existencia.producto,
        lote=existencia.lote,
        fecha_vencimiento=existencia.fecha_vencimiento,
        cantidad=cantidad,
        nota=carga.vehiculo.nombre,
        creado_por=usuario,
    )
    aplicar_movimiento(movimiento)
    return linea
