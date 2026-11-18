# Distribuidora Pollo Rey

Sistema de bodega, reparto y facturación. Este primer módulo cubre usuarios y roles.

La bodega seca abastece cinco puntos, cada uno con facturación independiente y su propio CAI del SAR: Ruta foránea, Pulperías, Bodegas, Sala de ventas y OPL. En ruta salen 3 camiones y 1 motocarga. El transportista imprime la factura en el dispositivo y esa factura entra al sistema cuando hay internet. El producto dañado no lleva un registro aparte: se le da salida. Hay 157 productos, en unidades y libras, y 1,385 clientes que hoy están en Excel.

## Roles

| Rol | Qué hace |
| --- | --- |
| Admin | Ve toda la operación, administra usuarios y puede registrar clientes. |
| Contabilidad | Revisa cierres, cobros, saldos y reportes. No mueve inventario ni factura. |
| Facturación | Factura cada punto con su CAI y registra clientes, equipo y ubicación. |
| Vendedor | Factura en ruta, sincroniza al tener internet y hace su propio cierre. |
| Inventario | Recibe, carga los vehículos, da salida a lo dañado y cuadra la bodega seca. |

## Arranque

Desde la raíz del proyecto, con el entorno ya creado:

```powershell
.\.venv\Scripts\python backend\manage.py migrate
.\.venv\Scripts\python backend\manage.py seed_roles
.\.venv\Scripts\python backend\manage.py runserver
```

En otra terminal:

```powershell
cd frontend
npm install
npm run dev
```

Abre http://localhost:5173

Usuarios de demostración, todos con contraseña `Pollo2026`:

- `gerencia`
- `contador`
- `facturacion`
- `vendedor`
- `inventario`

Si vuelves a correr `seed_roles`, no cambia la contraseña de un usuario que ya existe. Cámbialas antes de usarlo con datos reales. El usuario `gerencia` también puede entrar al administrador de Django en http://127.0.0.1:8000/admin/

La zona horaria está en `America/Tegucigalpa`.

## Siguiente módulo

Ingreso de producto a bodega, carga de camiones y despacho a los cinco puntos.
