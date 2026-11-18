from accounts.catalog import PUNTOS

from .models import PuntoVenta


def seed_puntos():
    for index, point in enumerate(PUNTOS, start=1):
        PuntoVenta.objects.update_or_create(
            code=point["code"],
            defaults={"name": point["name"], "sort_order": index},
        )
