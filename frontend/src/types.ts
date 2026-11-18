export type AccessLevel = "none" | "view" | "own" | "operate" | "full"

export type Grant = {
  code: string
  module: string
  module_label: string
  name: string
  description: string
  level: AccessLevel
  level_label: string
  sort_order: number
}

export type RoleBrief = {
  id: number
  code: string
  name: string
  summary: string
}

export type Role = RoleBrief & {
  description: string
  sort_order: number
  active_users: number
  permissions: Grant[]
}

export type User = {
  id: number
  username: string
  first_name: string
  last_name: string
  full_name: string
  email: string
  phone: string
  is_active: boolean
  role: RoleBrief | null
  permissions: Grant[]
  last_login: string | null
  date_joined: string
}

export type FlowStep = {
  order: number
  code: string
  title: string
  detail: string
  participa: boolean
  nivel: AccessLevel
  nivel_label: string
}

export type PuntoVenta = {
  id?: number
  code: string
  name: string
}

export type Sistema = {
  nombre: string
  puntos_de_venta: number
  puntos: PuntoVenta[]
  vehiculos: { camiones: number; motocarga: number }
  politica_devolucion: string
  flujo: FlowStep[]
}

export type Equipo = {
  id: number
  modelo: string
  placa: string
  foto: string
  ubicacion: string
  latitud: string | null
  longitud: string | null
  estado: "instalado" | "retirado"
  ubicacion_bloqueada: boolean
  retirado_en: string | null
}

export type Cliente = {
  id: number
  codigo: string
  nombre: string
  rtn: string
  telefono: string
  direccion: string
  punto: PuntoVenta
  dia_ruta: string
  dia_ruta_label: string
  vendedor: { id: number; full_name: string } | null
  latitud: string | null
  longitud: string | null
  credito_habilitado: boolean
  limite_credito: string | null
  credito_autorizado_por: { id: number; full_name: string } | null
  credito_autorizado_en: string | null
  notas: string
  activo: boolean
  es_nuevo: boolean
  creado_en: string
  equipos: Equipo[]
}

export type ClienteOpciones = {
  puntos: PuntoVenta[]
  dias: { code: string; name: string }[]
  vendedores?: { id: number; full_name: string }[]
  nuevos: number
}

export type LibroResumen = {
  razon_social: string
  nombre: string
  desde: string | null
  hasta: string | null
  documentos: number
  vigentes: number
  anulados: number
  clientes: number
  cajas: string[]
  ventas_netas: string
  exentas: string
  exoneradas: string
  gravada_15: string
  isv_15: string
  gravada_18: string
  isv_18: string
  descuentos: string
  contado: { documentos: number; total: string }
  credito: { documentos: number; total: string }
}

export type DocumentoVenta = {
  id: number
  registro: number
  fecha: string
  caja: string
  tipo: string
  serie: string
  numero: string
  cai: string
  fecha_limite: string | null
  rtn: string
  cliente: string
  condicion: string
  forma_pago: string
  moneda: string
  exenta: string
  exonerada: string
  gravada_15: string
  isv_15: string
  gravada_18: string
  isv_18: string
  descuento: string
  total: string
  estado: string
}

export type ReporteMensual = {
  meses: string[]
  proveedores?: { id: number; nombre: string; meses: string[]; total: string }[]
  vendedores?: { id: number; nombre: string; meses: string[]; total: string }[]
}

export type CierreDiario = {
  id: number
  fecha: string
  numero: number | null
  factura_desde: string
  factura_hasta: string
  concepto: string
  venta_libre: string
  venta_gravada: string
  impuesto: string
  total: string
}

export type PrecioCliente = {
  id: number
  cliente: number
  cliente_nombre: string
  cliente_codigo: string
  precio: string
  actualizado_en: string
}

export type Producto = {
  id: number
  codigo: string
  nombre: string
  unidad: string
  unidad_label: string
  precio_base: string
  controla_lote: boolean
  activo: boolean
  notas: string
  precios: PrecioCliente[]
}

export type Existencia = {
  id: number
  producto: number
  producto_nombre: string
  producto_codigo: string
  unidad: string
  unidad_label: string
  lote: string
  fecha_vencimiento: string | null
  cantidad: string
}

export type MovimientoBodega = {
  id: number
  tipo: string
  tipo_label: string
  producto: number
  producto_nombre: string
  unidad_label: string
  lote: string
  fecha_vencimiento: string | null
  cantidad: string
  nota: string
  creado_por_nombre: string
  creado_en: string
}

export type Vehiculo = {
  id: number
  codigo: string
  nombre: string
  tipo: string
  tipo_label: string
  vendedor: number | null
  vendedor_nombre: string
  activo: boolean
}

export type CargaLinea = {
  id: number
  producto: number
  producto_nombre: string
  unidad: string
  unidad_label: string
  lote: string
  fecha_vencimiento: string | null
  cantidad: string
}

export type Carga = {
  id: number
  vehiculo: number
  vehiculo_nombre: string
  fecha: string
  nota: string
  lineas: CargaLinea[]
  creado_en: string
}

export type BodegaProducto = {
  id: number
  nombre: string
  codigo: string
  unidad: string
  unidad_label: string
  controla_lote: boolean
}

export type ProductoOpciones = {
  unidades: { code: string; name: string }[]
  clientes?: { id: number; nombre: string; codigo: string }[]
}

export type Page<T> = {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export type LoginResponse = {
  access: string
  refresh: string
  user: User
}

const RANK: Record<AccessLevel, number> = {
  none: 0,
  view: 1,
  own: 2,
  operate: 3,
  full: 4,
}

export function allows(level: AccessLevel | undefined, minimum: AccessLevel) {
  return RANK[level ?? "none"] >= RANK[minimum]
}
