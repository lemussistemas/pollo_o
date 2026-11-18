"""Catálogo operativo de Distribuidora Pollo Rey.

La bodega seca abastece cinco puntos con facturación independiente.
En ruta salen tres camiones y una motocarga. El transportista factura
en el dispositivo y la factura entra al sistema cuando hay internet.
El producto dañado no lleva un registro aparte: se le da salida.
"""

from .models import LEVEL_RANK, AccessLevel, RoleCode

NOMBRE = "Distribuidora Pollo Rey"

PUNTOS = [
    {"code": "ruta_foranea", "name": "Ruta foránea"},
    {"code": "pulperias", "name": "Pulperías"},
    {"code": "bodegas", "name": "Bodegas"},
    {"code": "sala_de_ventas", "name": "Sala de ventas"},
    {"code": "opl", "name": "OPL"},
]
PUNTOS_DE_VENTA = len(PUNTOS)
VEHICULOS = {"camiones": 3, "motocarga": 1}
POLITICA_DEVOLUCION = (
    "El producto dañado no tiene un registro aparte: se le da salida de inventario."
)

MODULE_LABELS = {
    "inventario": "Inventario",
    "distribucion": "Distribución",
    "facturacion": "Facturación",
    "cierre": "Cierres",
    "reportes": "Reportes",
    "usuarios": "Usuarios",
    "clientes": "Clientes",
    "contabilidad": "Contabilidad",
    "productos": "Productos",
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
        "Salida por producto dañado",
        "Dar salida al producto dañado. No se abre un registro aparte.",
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
    (
        "clientes.ver",
        "clientes",
        "Ver clientes",
        "Consultar clientes, su ruta, su crédito y sus equipos.",
        170,
    ),
    (
        "clientes.gestionar",
        "clientes",
        "Registrar clientes",
        "Crear y editar clientes, su ubicación y el equipo instalado.",
        180,
    ),
    (
        "clientes.credito",
        "clientes",
        "Autorizar crédito",
        "Decidir qué cliente puede comprar a crédito y hasta qué límite. No es para todos.",
        190,
    ),
    (
        "contabilidad.libros",
        "contabilidad",
        "Libros contables",
        "Consultar el libro de ventas, las compras por proveedor, las ventas por vendedor y los cierres.",
        200,
    ),
    (
        "productos.ver",
        "productos",
        "Ver productos",
        "Consultar el catálogo, la unidad de medida y el precio de cada cliente.",
        210,
    ),
    (
        "productos.gestionar",
        "productos",
        "Registrar productos",
        "Crear productos por unidad o por libra, y marcar los que llevan lote y vencimiento.",
        220,
    ),
    (
        "productos.precios",
        "productos",
        "Precios por cliente",
        "Fijar el precio de un producto para un cliente. No es el mismo para todos.",
        230,
    ),
]

ROLES = [
    {
        "code": RoleCode.GERENCIA,
        "name": "Admin",
        "summary": "Administra usuarios, clientes y toda la operación.",
        "description": (
            "Ve bodega, rutas, facturación y cierres. Crea los usuarios y, junto con "
            "facturación, registra clientes, el equipo instalado y su ubicación. "
            "Solo este rol autoriza el crédito, cliente por cliente."
        ),
        "sort_order": 1,
    },
    {
        "code": RoleCode.CONTADOR,
        "name": "Contabilidad",
        "summary": "Revisa cierres, cobros, saldos y reportes.",
        "description": (
            "Revisa lo que salió de bodega, lo facturado en cada punto y lo facturado en ruta. "
            "Consulta cuentas por cobrar, abonos y el estimado de cada ruta. "
            "No mueve inventario ni emite facturas."
        ),
        "sort_order": 2,
    },
    {
        "code": RoleCode.FACTURACION,
        "name": "Facturación",
        "summary": "Factura cada punto con su propio CAI y registra clientes.",
        "description": (
            "Emite facturas, recibos, notas de crédito, devoluciones y cotizaciones. "
            "Cada punto factura por su cuenta, con CAI independiente. "
            "Registra clientes, la foto del equipo, la placa y la ubicación. "
            "No autoriza crédito: eso lo decide gerencia."
        ),
        "sort_order": 3,
    },
    {
        "code": RoleCode.VENDEDOR,
        "name": "Vendedor",
        "summary": "Factura en ruta y sincroniza cuando hay internet.",
        "description": (
            "Entrega con los camiones o la motocarga y emite la factura en el dispositivo "
            "con impresora, aunque no haya señal. Cuando vuelve el internet, esa factura "
            "entra al sistema. Cobra en efectivo, transferencia, crédito o una combinación, "
            "y hace su propio cierre."
        ),
        "sort_order": 4,
    },
    {
        "code": RoleCode.INVENTARIO,
        "name": "Inventario",
        "summary": "Cuenta la bodega seca por unidad y por libra.",
        "description": (
            "Recibe el producto, lo carga al sistema y arma los tres camiones y la motocarga. "
            "Lleva lotes, vencimiento, mermas y pérdidas. Al producto dañado le da salida, "
            "sin abrir otro registro. Al regreso vuelve a inventariar la bodega seca."
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
        "clientes.ver": AccessLevel.VIEW,
        "contabilidad.libros": AccessLevel.FULL,
        "productos.ver": AccessLevel.VIEW,
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
        "clientes.ver": AccessLevel.VIEW,
        "clientes.gestionar": AccessLevel.OPERATE,
        "contabilidad.libros": AccessLevel.VIEW,
        "productos.ver": AccessLevel.VIEW,
        "productos.precios": AccessLevel.OPERATE,
    },
    RoleCode.VENDEDOR: {
        "distribucion.carga": AccessLevel.OWN,
        "distribucion.despacho": AccessLevel.OWN,
        "distribucion.retorno": AccessLevel.OWN,
        "facturacion.ruta": AccessLevel.OWN,
        "cierre.vendedor": AccessLevel.OWN,
        "reportes.operacion": AccessLevel.OWN,
        "clientes.ver": AccessLevel.OWN,
        "productos.ver": AccessLevel.OWN,
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
        "productos.ver": AccessLevel.VIEW,
        "productos.gestionar": AccessLevel.OPERATE,
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
        "detail": "La bodega seca abastece Ruta foránea, Pulperías, Bodegas, Sala de ventas y OPL.",
        "permissions": ["distribucion.despacho"],
    },
    {
        "order": 4,
        "code": "facturacion_pdv",
        "title": "Facturan los puntos de venta",
        "detail": "Cada punto emite sus documentos con facturación independiente y su propio CAI.",
        "permissions": ["facturacion.pdv"],
    },
    {
        "order": 5,
        "code": "facturacion_ruta",
        "title": "El transportista factura en ruta",
        "detail": "La factura se imprime en el dispositivo y entra al sistema cuando hay internet.",
        "permissions": ["facturacion.ruta"],
    },
    {
        "order": 6,
        "code": "regreso",
        "title": "El camión regresa a bodega",
        "detail": "Se confirma lo entregado. El producto dañado sale del inventario, sin un registro aparte.",
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
