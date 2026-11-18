from decimal import Decimal

from django.db import transaction

from .models import Existencia, TipoMovimiento, clave_de


class StockError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


@transaction.atomic
def aplicar_movimiento(movimiento):
    clave = clave_de(movimiento.lote, movimiento.fecha_vencimiento)
    existencia, _created = Existencia.objects.select_for_update().get_or_create(
        producto=movimiento.producto,
        clave=clave,
        defaults={
            "lote": movimiento.lote,
            "fecha_vencimiento": movimiento.fecha_vencimiento,
            "cantidad": Decimal("0"),
        },
    )
    if movimiento.tipo == TipoMovimiento.INGRESO:
        existencia.cantidad += movimiento.cantidad
    elif existencia.cantidad < movimiento.cantidad:
        raise StockError("No hay suficiente existencia.")
    else:
        existencia.cantidad -= movimiento.cantidad
    existencia.save(update_fields=["cantidad", "lote", "fecha_vencimiento", "clave"])
    return existencia
