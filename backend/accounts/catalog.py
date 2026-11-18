"""Catálogo operativo de la distribuidora.

El producto entra a la bodega principal, se carga a los camiones y se reparte
a los cinco puntos de venta. No regresa, salvo que esté en mal estado. Cada
punto y cada vendedor hacen su propio cierre. Al volver el camión, bodega
vuelve a inventariar y el día tiene que cuadrar.
"""

from .models import LEVEL_RANK, AccessLevel, RoleCode

PUNTOS_DE_VENTA = 5
POLITICA_DEVOLUCION = (
    "No se devuelve producto a la bodega principal, salvo que esté en mal estado."
)

MODULE_LABELS = {
    "inventario": "Inventario",
    "distribucion": "Distribución",
    "facturacion": "Facturación",
    "cierre": "Cierres",
    "reportes": "Reportes",
    "usuarios": "Usuarios",
}

# code, module, name, description, sort_order
PERMISSIONS = [
    (
        "inventario.ingreso",
        "inventario",
        "Ingreso de producto",
        "Registrar el pollo que entra a la bodega principal.",
        10,
    ),
    (
        "inventario.cuadre",
        "inventario",
        "Cuadre de bodega",
        "Volver a inventariar cuando los camiones regresan. Lo cargado, lo facturado y lo que queda tienen que cuadrar.",
        20,
    ),
    (
        "inventario.mal_estado",
        "inventario",
        "Producto en mal estado",
        "Registrar el único producto que puede regresar: el que está en mal estado.",
        30,
    ),
    (
        "distribucion.carga",
        "distribucion",
        "Carga de camiones",
        "Armar en el sistema la carga que sale de bodega.",
        40,
    ),
    (
        "distribucion.despacho",
        "distribucion",
        "Despacho a puntos de venta",
        "Registrar la salida hacia los cinco puntos de venta.",
        50,
    ),
    (
        "distribucion.retorno",
        "distribucion",
        "Regreso a bodega",
        "Confirmar el regreso del camión después de la ruta.",
        60,
    ),
    (
        "facturacion.pdv",
        "facturacion",
        "Facturación de puntos de venta",
        "Facturar las ventas de los puntos de venta.",
        70,
    ),
    (
        "facturacion.ruta",
        "facturacion",
        "Facturación en ruta",
        "Facturar desde la tablet del vendedor, con la impresora integrada.",
        80,
    ),
    (
        "cierre.pdv",
        "cierre",
        "Cierre del punto de venta",
        "Cierre propio de cada punto de venta.",
        90,
    ),
    (
        "cierre.vendedor",
        "cierre",
        "Cierre del vendedor",
        "Cierre propio del vendedor al terminar la ruta.",
        100,
    ),
    (
        "cierre.bodega",
        "cierre",
        "Cierre de bodega",
        "Cierre de la bodega principal después del cuadre.",
        110,
    ),
    (
        "cierre.contable",
        "cierre",
        "Revisión contable",
        "Revisar que los cierres cuadren con la facturación y el inventario.",
        120,
    ),
    (
        "reportes.operacion",
        "reportes",
        "Reportes de operación",
        "Consultar cargas, facturas, regresos y cuadres.",
        130,
    ),
    (
        "reportes.finanzas",
        "reportes",
        "Reportes financieros",
        "Consultar ingresos, cortes y diferencias.",
        140,
    ),
    (
        "usuarios.ver",
        "usuarios",
        "Ver usuarios",
        "Consultar quién tiene acceso al sistema.",
        150,
    ),
    (
        "usuarios.gestionar",
        "usuarios",
        "Gestionar usuarios",
        "Crear usuarios, asignar un rol y activar o desactivar el acceso.",
        160,
    ),
]

ROLES = [
    {
        "code": RoleCode.GERENCIA,
        "name": "Gerencia",
        "summary": "Ve toda la operación y administra los usuarios.",
        "description": (
            "Dirige la distribuidora. Puede ver bodega, camiones, facturación y cierres, "
            "y es quien crea los usuarios y les asigna un rol."
        ),
        "sort_order": 1,
    },
    {
        "code": RoleCode.CONTADOR,
        "name": "Contador",
        "summary": "Revisa los cierres y lleva los reportes financieros.",
        "description": (
            "Revisa que el día cuadre: lo que salió de bodega, lo facturado en los puntos "
            "y lo facturado por los vendedores. Lleva la revisión contable y los reportes "
            "financieros. No mueve inventario ni emite facturas."
        ),
        "sort_order": 2,
    },
    {
        "code": RoleCode.FACTURACION,
        "name": "Facturación",
        "summary": "Factura los puntos de venta y cierra cada punto.",
        "description": (
            "Factura los cinco puntos de venta y hace el cierre de cada punto. "
            "Consulta lo despachado y lo que el vendedor facturó en ruta."
        ),
        "sort_order": 3,
    },
    {
        "code": RoleCode.VENDEDOR,
        "name": "Vendedor",
        "summary": "Factura en la tablet y hace su propio cierre.",
        "description": (
            "Trabaja en ruta con la tablet Android y la impresora integrada. "
            "Factura sus entregas, hace su propio cierre y solo puede reportar "
            "producto en mal estado. No devuelve producto bueno a bodega."
        ),
        "sort_order": 4,
    },
    {
        "code": RoleCode.INVENTARIO,
        "name": "Inventario",
        "summary": "Recibe el producto, carga los camiones y cuadra la bodega.",
        "description": (
            "Recibe el pollo en la bodega principal, lo carga al sistema, arma los camiones "
            "y despacha a los puntos de venta. Cuando los camiones regresan, vuelve a inventariar. "
            "Recibe únicamente producto en mal estado."
        ),
        "sort_order": 5,
    },
]

# Lo que no aparece queda en "sin acceso". Gerencia se resuelve aparte: nivel completo.
GRANTS = {
    RoleCode.CONTADOR: {
        "inventario.ingreso": AccessLevel.VIEW,
        "inventario.cuadre": AccessLevel.VIEW,
        "inventario.mal_estado": AccessLevel.VIEW,
        "distribucion.carga": AccessLevel.VIEW,
        "distribucion.despacho": AccessLevel.VIEW,
        "distribucion.retorno": AccessLevel.VIEW,
        "facturacion.pdv": AccessLevel.VIEW,
        "facturacion.ruta": AccessLevel.VIEW,
        "cierre.pdv": AccessLevel.VIEW,
        "cierre.vendedor": AccessLevel.VIEW,
        "cierre.bodega": AccessLevel.VIEW,
        "cierre.contable": AccessLevel.FULL,
        "reportes.operacion": AccessLevel.VIEW,
        "reportes.finanzas": AccessLevel.FULL,
        "usuarios.ver": AccessLevel.VIEW,
    },
    RoleCode.FACTURACION: {
        "inventario.mal_estado": AccessLevel.VIEW,
        "distribucion.despacho": AccessLevel.VIEW,
        "distribucion.retorno": AccessLevel.VIEW,
        "facturacion.pdv": AccessLevel.OPERATE,
        "facturacion.ruta": AccessLevel.VIEW,
        "cierre.pdv": AccessLevel.OPERATE,
        "cierre.vendedor": AccessLevel.VIEW,
        "reportes.operacion": AccessLevel.VIEW,
    },
    RoleCode.VENDEDOR: {
        "inventario.mal_estado": AccessLevel.OWN,
        "distribucion.carga": AccessLevel.OWN,
        "distribucion.despacho": AccessLevel.OWN,
        "distribucion.retorno": AccessLevel.OWN,
        "facturacion.ruta": AccessLevel.OWN,
        "cierre.vendedor": AccessLevel.OWN,
        "reportes.operacion": AccessLevel.OWN,
    },
    RoleCode.INVENTARIO: {
        "inventario.ingreso": AccessLevel.OPERATE,
        "inventario.cuadre": AccessLevel.OPERATE,
        "inventario.mal_estado": AccessLevel.OPERATE,
        "distribucion.carga": AccessLevel.OPERATE,
        "distribucion.despacho": AccessLevel.OPERATE,
        "distribucion.retorno": AccessLevel.OPERATE,
        "facturacion.pdv": AccessLevel.VIEW,
        "facturacion.ruta": AccessLevel.VIEW,
        "cierre.pdv": AccessLevel.VIEW,
        "cierre.vendedor": AccessLevel.VIEW,
        "cierre.bodega": AccessLevel.OPERATE,
        "reportes.operacion": AccessLevel.VIEW,
    },
}

FLOW = [
    {
        "order": 1,
        "code": "ingreso",
        "title": "Entra el producto",
        "detail": "El pollo llega a la bodega principal y se registra en el sistema.",
        "permissions": ["inventario.ingreso"],
    },
    {
        "order": 2,
        "code": "carga",
        "title": "Se cargan los camiones",
        "detail": "Inventario arma en el sistema la carga que va a salir.",
        "permissions": ["distribucion.carga"],
    },
    {
        "order": 3,
        "code": "despacho",
        "title": "Se reparte a los puntos de venta",
        "detail": "La bodega principal distribuye a los cinco puntos. El producto bueno no regresa.",
        "permissions": ["distribucion.despacho"],
    },
    {
        "order": 4,
        "code": "facturacion_pdv",
        "title": "Facturan los puntos de venta",
        "detail": "Facturación emite las facturas de cada punto de venta.",
        "permissions": ["facturacion.pdv"],
    },
    {
        "order": 5,
        "code": "facturacion_ruta",
        "title": "El vendedor factura en la tablet",
        "detail": "En la ruta factura con la tablet Android y la impresora integrada.",
        "permissions": ["facturacion.ruta"],
    },
    {
        "order": 6,
        "code": "regreso",
        "title": "El camión regresa a bodega",
        "detail": "Después de la entrega se confirma el regreso. Solo puede volver producto en mal estado.",
        "permissions": ["distribucion.retorno"],
    },
    {
        "order": 7,
        "code": "cuadre",
        "title": "Se vuelve a inventariar",
        "detail": "Bodega cuenta de nuevo. Lo que salió, lo facturado y lo que queda tienen que cuadrar.",
        "permissions": ["inventario.cuadre"],
    },
    {
        "order": 8,
        "code": "cierre_pdv",
        "title": "Cierre del punto de venta",
        "detail": "Cada punto de venta hace su propio cierre.",
        "permissions": ["cierre.pdv"],
    },
    {
        "order": 9,
        "code": "cierre_vendedor",
        "title": "Cierre del vendedor",
        "detail": "Cada vendedor cierra su ruta por separado del punto de venta.",
        "permissions": ["cierre.vendedor"],
    },
    {
        "order": 10,
        "code": "cierre_bodega",
        "title": "Cierre de bodega",
        "detail": "La bodega principal cierra cuando el cuadre del regreso ya está hecho.",
        "permissions": ["cierre.bodega"],
    },
    {
        "order": 11,
        "code": "cierre_contable",
        "title": "Revisión contable",
        "detail": "Contabilidad revisa que los cierres del punto, del vendedor y de bodega cuadren.",
        "permissions": ["cierre.contable"],
    },
]


def level_for(role_code, permission_code):
    if role_code == RoleCode.GERENCIA:
        return AccessLevel.FULL
    return GRANTS.get(role_code, {}).get(permission_code, AccessLevel.NONE)


def flujo_for(user):
    access = user.access_map()
    steps = []
    for step in FLOW:
        level = AccessLevel.NONE
        rank = 0
        for code in step["permissions"]:
            current = access.get(code, AccessLevel.NONE)
            current_rank = LEVEL_RANK[current]
            if current_rank > rank:
                rank = current_rank
                level = current
        steps.append(
            {
                "order": step["order"],
                "code": step["code"],
                "title": step["title"],
                "detail": step["detail"],
                "participa": level != AccessLevel.NONE,
                "nivel": level,
                "nivel_label": AccessLevel(level).label,
            }
        )
    return steps
