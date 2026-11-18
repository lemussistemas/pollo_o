# Distribuidora de pollo

Sistema de bodega, reparto y facturación. Este primer módulo cubre usuarios y roles.

El producto entra a la bodega principal, se carga al sistema, sale en camiones y se reparte a **5 puntos de venta**. Facturación atiende los puntos. El vendedor factura en ruta con una tablet Android y una impresora integrada. Al regresar se vuelve a inventariar: lo que salió, lo facturado y lo que queda tienen que cuadrar. No se devuelve producto, salvo que esté en mal estado. El punto de venta y el vendedor hacen cada uno su propio cierre.

## Roles

| Rol | Qué hace |
| --- | --- |
| Gerencia | Ve toda la operación y administra usuarios. |
| Contador | Revisa los cierres y lleva los reportes financieros. No mueve inventario ni factura. |
| Facturación | Factura los puntos de venta y hace el cierre de cada punto. |
| Vendedor | Factura en la tablet lo suyo y hace su propio cierre. Solo reporta producto en mal estado. |
| Inventario | Recibe, carga camiones, despacha y cuadra la bodega. Recibe lo que vuelve en mal estado. |

Facturación hace el cierre del punto porque todavía no hay un rol aparte de cajero de punto de venta. Si cada punto tiene su propia persona, ese rol se agrega en el siguiente ajuste.

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

Si vuelves a correr `seed_roles`, no cambia la contraseña de un usuario que ya existe. Cámbialas antes de usarlo con datos reales. Gerencia también puede entrar al administrador de Django en http://127.0.0.1:8000/admin/

La zona horaria está en `America/Guatemala` (UTC−6). Si operan en otra zona, cámbiala en `backend/config/settings.py`.

## Siguiente módulo

Ingreso de producto a bodega, carga de camiones y despacho a los cinco puntos.
