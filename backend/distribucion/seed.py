from .models import TipoVehiculo, Vehiculo

FLOTA = [
    {"codigo": "camion-1", "nombre": "Camión 1", "tipo": TipoVehiculo.CAMION},
    {"codigo": "camion-2", "nombre": "Camión 2", "tipo": TipoVehiculo.CAMION},
    {"codigo": "camion-3", "nombre": "Camión 3", "tipo": TipoVehiculo.CAMION},
    {"codigo": "motocarga", "nombre": "Motocarga", "tipo": TipoVehiculo.MOTOCARGA},
]


def seed_vehiculos():
    for item in FLOTA:
        Vehiculo.objects.update_or_create(
            codigo=item["codigo"],
            defaults={"nombre": item["nombre"], "tipo": item["tipo"], "activo": True},
        )
    return Vehiculo.objects.filter(codigo__in=[item["codigo"] for item in FLOTA]).count()
