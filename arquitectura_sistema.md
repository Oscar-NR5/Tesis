# SSPM_APP — Visión general del proyecto

> Documento de orientación para personas que se incorporan al desarrollo o mantenimiento del
> sistema. Describe qué es, para qué sirve, cómo está construido y dónde vive cada cosa.
> No contiene credenciales, endpoints internos ni datos de operación.

---

## 1. Qué es

**SSPM_APP** (nombre interno histórico en el repo: *SecureDocFlow*) es el sistema de gestión
interna de la **Secretaría de Seguridad Pública Municipal de Ciudad Juárez**.

Nació como un gestor documental y creció hasta convertirse en el ERP operativo de la
dependencia: hoy concentra el expediente del personal, la flota de patrullas, el almacén,
los informes policiales, los procedimientos disciplinarios, la academia y prácticamente
todo el papeleo formal que antes circulaba impreso.

**A quién sirve:** personal administrativo de la Secretaría (RH, almacén, patrimonio,
telecomunicaciones, jurídico, academia), mandos de distrito y elementos operativos que
capturan bitácoras e informes.

**Qué resuelve, en una línea:** convierte trámites en papel (oficios, resguardos, solicitudes,
partes informativos, declaraciones) en flujos digitales con folio, historial, permisos por
zona geográfica y salida en PDF/Excel con formato oficial.

**Qué NO es:** no es un sistema ciudadano ni público. Es una herramienta interna, tras
autenticación, sin registro abierto de usuarios.

---

## 2. Estado y escala del proyecto

| Indicador | Valor aproximado |
|---|---|
| Inicio del repositorio | septiembre 2023 |
| Commits totales | ~7,900 |
| Ritmo | 2023: 288 · 2024: 2,172 · 2025: 3,409 · 2026: 2,041 |
| Contribuyentes con commits | ~20 (equipo chico, rotación alta) |
| Controladores | 116 |
| Modelos | 217 (≈65 MySQL, ≈140 MongoDB, ≈12 Patrimonio) |
| Servicios | 61 |
| Componentes Livewire | 34 |
| Exports / Imports Excel | 60 / 16 |
| Vistas Blade | ~1,250 |
| Rutas web declaradas | ~2,300 en un solo `routes/web.php` (416 KB) |
| Migraciones | 131 |
| Seeders | ~48 |
| Comandos artisan propios | ~50 (backfills y normalizaciones de datos) |

Es un sistema **en producción y en evolución continua**: cada rama `feat/` corresponde a una
petición real de un área. El repositorio conserva ~190 ramas remotas, una por feature
entregada o en curso.

---

## 3. Stack técnico

| Capa | Tecnología |
|---|---|
| Lenguaje | PHP 7.4 – 8.2 (imágenes Docker para cada versión en [docker/](docker/)) |
| Framework | Laravel 8.75 |
| Base de datos relacional | MySQL / MariaDB (Eloquent) |
| Base de datos documental | MongoDB (`jenssegers/mongodb` 3.8) |
| Autorización | `spatie/laravel-permission` + sistema propio por módulo/distrito |
| Auditoría | `owen-it/laravel-auditing` |
| UI | Blade + Bootstrap 5 + AdminLTE |
| Reactividad | Livewire 2 |
| Tablas | Yajra DataTables (server-side AJAX) |
| Build | Laravel Mix (webpack): `resources/js/app.js` → `public/js`, `resources/sass/app.scss` → `public/css` |
| PDF | DomPDF, TCPDF, mPDF y FPDF/FPDI (cuatro librerías, según el módulo) |
| Excel | `maatwebsite/excel` + PhpSpreadsheet |
| Otros | QR (`simplesoftwareio/simple-qrcode`), códigos de barras, Intervention Image, Flatpickr, Dropzone, Google Maps JS API |

---

## 4. Arquitectura

### 4.1 Ciclo de una petición

```
HTTP
 → routes/web.php  (o routes/api.php)
 → Middleware        auth · permisos · TrackPageView
 → Controller        app/Http/Controllers/
 → Service           app/Services/        ← lógica de negocio (en los módulos nuevos)
 → Repository        app/Repositories/    ← opcional, poco usado
 → Model             app/Models/ (MySQL) | app/Models/Mongo/ (MongoDB)
 → Blade / JSON / PDF / XLSX
```

En los módulos antiguos la lógica vive en el controlador; en los recientes (Refacciones,
Gasolina, Bitácoras, Cumplimiento de Asistencia, Estacionamiento) está extraída a `app/Services/`.
Esa es la dirección hacia la que se mueve el código.

### 4.2 Doble base de datos — la decisión estructural del proyecto

El sistema escribe **simultáneamente en MySQL y MongoDB**, y esto define casi todo lo demás.

- **MySQL** — datos estructurados y estables: `users`, roles y permisos de Spatie, módulos,
  distritos, agrupamientos, subáreas, plazas, catálogos, formularios IPH, evaluaciones
  de academia, settings.
- **MongoDB** — datos documentales y de volumen: bitácoras, almacén, partes informativos,
  tarjetas informativas, asistencia biométrica, historiales de cambios, métricas, y buena
  parte de los expedientes de RH.

**Consecuencia práctica:** muchos conceptos del dominio tienen **dos clases de modelo**.

```
App\Models\Bitacora        (MySQL)   vs  App\Models\Mongo\Bitacora
App\Models\User            (MySQL)   vs  App\Models\Mongo\UserM       ← perfil del empleado
App\Models\Telecomunicaciones        vs  App\Models\Mongo\Telecomunicaciones
```

Antes de tocar un módulo: **verificar qué modelo usa el controlador**. La clase padre lo dice
(`Eloquent` vs `Jenssegers\Mongodb\Eloquent\Model`).

La llave que cose ambos mundos es el **número de empleado** (`users.email` guarda el número de
empleado, y `idPersona` enlaza con los documentos de Mongo). No hay claves foráneas entre bases:
las relaciones son por convención, no por constraint.

### 4.3 Autorización — dos capas independientes

**Capa 1 — Spatie (roles y permisos nombrados).** Gates clásicos: `can()`, `@can`,
`->middleware('permission:...')`. Los roles `admin` y `RH` se saltan la mayoría de las
verificaciones.

**Capa 2 — Permisos por Módulo × ámbito organizacional.**
`App\Traits\HasModuleDistrictPermissionsTrait` sobre `User`. Concede acciones
(`create` / `edit` / `view` / `delete` / `print`) por **Módulo** cruzado con:

- **Distrito** — la zona geográfica (`UserModuleDistrictPermission`)
- **Agrupamiento** — la unidad organizacional (`UserModuleAgrupamientoPermission`)
- **Subárea** — el desglose fino (`UserModuleSubareaPermission`)

Distrito y agrupamiento son **dimensiones hermanas, no una jerarquía**. Desde 2026 los mismos
permisos pueden concederse también **a un rol completo** (`RoleModule*Permission`), y los
permisos efectivos de un usuario son la fusión de los propios con los de sus roles.

Uso típico:

```php
$user->canDoInModuleDistrict('Control de Unidades', 'edit', $districtId);
$user->getDistrictsWhereCanDo('Almacén', 'view');   // para filtrar listados
```

El middleware `admin_or_permission:<permiso>` pasa si el usuario es `admin`/`RH` **o** tiene
el permiso Spatie nombrado. Al añadir una ruta restringida hay que revisar **las dos capas**:
una sola no basta para saber quién ve qué.

Las verificaciones se cachean a nivel de request dentro del trait
(`User::forgetModulePermissionCaches()` para invalidar).

### 4.4 Frontend

- **Blade + Bootstrap 5** para todo el HTML; el menú lateral vive en
  [resources/views/layouts/menu.blade.php](resources/views/layouts/menu.blade.php) (~1,800 líneas,
  es el mapa real de módulos visible por el usuario).
- **Livewire 2** para formularios reactivos y matrices de permisos. No pasa por rutas de
  controlador: se comunica por AJAX propio.
- **DataTables server-side** para los listados grandes.
- **JS por módulo en `public/js/`** — no todo pasa por Mix; hay scripts servidos directamente.
- El parque de navegadores de la dependencia incluye equipos **pre-2020**: el JS inline debe
  evitar sintaxis ES2020 (`??`, `?.`), un `SyntaxError` deja la tabla vacía sin error visible.

### 4.5 Generación de documentos

- **PDF**: cuatro librerías conviven (DomPDF mayoritaria, TCPDF, mPDF, FPDI para estampado
  sobre formatos existentes). Revisar qué usa el controlador antes de añadir una dependencia.
- Los oficios se arman con **plantillas configurables**: hay un `config/oficio_*.php` por tipo
  de oficio (alta, baja, placa, reparación, rehabilitación, resguardante, transferencia,
  gasolina, genéricos, telecom, patrimonio) con folio, encabezados y destinatarios.
- **Excel**: `app/Exports/` (60 clases) y `app/Imports/` (16). Las exportaciones grandes usan
  escritura en streaming para no agotar memoria.

### 4.6 Observabilidad

`App\Services\MetricRecorder` registra en la colección `metrics` de MongoDB:
vistas de página (middleware `TrackPageView`), errores y eventos de frontend
(geocoding y mapas estáticos de Google Maps, para controlar el costo de la API).
Se apaga con `METRICS_ENABLED`. Índice TTL: los documentos expiran a los 180 días.

### 4.7 API de asistencia biométrica

Único endpoint máquina-a-máquina del sistema:
`POST /api/attendance/ingest/{slug}`. Los relojes biométricos empujan las checadas.
Protección: **IP en lista blanca + token Bearer** (`AttendanceApiGuard`), slug aleatorio en la
URL y sin throttle (es tráfico de una IP fija conocida). Los datos aterrizan en
`App\Models\Mongo\BiometricAttendance`.

---

## 5. Estructura de directorios

```
app/
├── Console/Commands/     ~50 comandos: backfills, normalizaciones, importaciones puntuales
├── Exports/              60 clases de exportación Excel (+ Concerns/ con el writer en streaming)
├── Imports/              16 importadores Excel
├── Helpers/              NombreHelper (autocargado globalmente), CampoHelper
├── Http/
│   ├── Controllers/      116 controladores + subcarpetas API/, Auth/, Academia/, Telecom/
│   ├── Livewire/         34 componentes reactivos
│   ├── Middleware/       AdminOrPermission, AttendanceApiGuard, TrackPageView,
│   │                     OptimizePdfGeneration, EstacionamientoLegado
│   └── Requests/         Form Requests (validación)
├── Models/
│   ├── *.php             modelos MySQL (usuarios, permisos, catálogos, oficios, patrimonio)
│   ├── Mongo/            ~140 modelos MongoDB — el grueso del dominio operativo
│   ├── Patrimonio/       activos, unidades patrulla, archivo documental
│   └── Traits/           FiltroPorDistrito
├── Observers/            UserMObserver
├── Policies/             BitacoraPolicy, CapacitacionPolicy
├── Repositories/         BaseRepository + Bitacora/Catalogo/Iph/User
├── Services/             61 clases; subcarpetas por dominio:
│                         Bitacoras/ CumplimientoAsistencia/ Estacionamiento/ Gasolina/
│                         LaCueva/ Patrimonio/ Refacciones/ Reportes/ Transparencia/
├── Support/              objetos de apoyo: scopes de dashboard, normalizadores, fechas flexibles
├── Traits/               HasModuleDistrictPermissionsTrait (permisos), accesos por módulo,
│                         TracksCrudOperations (desactivado), TimezoneHandler
└── Utils/                InputSanitizer, DateHelper, DefaultValues

config/          configuración estándar de Laravel + ~20 archivos propios:
                 metrics, attendance, alertas_*, oficio_*, permisos_control_unidades,
                 reportes_generador, cumplimiento_asistencia, estacionamiento, gasolina_proveedores

database/
├── migrations/   131 — incluye migraciones que solo crean ÍNDICES de MongoDB
└── seeders/      ~48 — roles, permisos, módulos, distritos y catálogos iniciales

resources/views/  ~1,250 Blade, una carpeta por módulo (almacen, refacciones_virtuales,
                  unidades-patrulla, telecom, RH, iphs, parte_informativa, academia,
                  declaraciones, la_cueva, patrimonio…), más layouts/ y livewire/

routes/web.php    ~2,300 rutas en un solo archivo — ver §8 (deuda conocida)
routes/api.php    solo el endpoint biométrico y el usuario Sanctum

public/           assets compilados + JS por módulo + plantillas y archivos subidos
storage/app/      documentos, resguardos, carátulas, licencias, imágenes, temporales de PDF
docker/           Dockerfiles por versión de PHP (7.4 / 8.0 / 8.1 / 8.2)
docs/ · plans/    documentación funcional y planes de módulo (declaraciones, refacciones,
                  Google Maps y métricas, oficios de gasolina)
.claude/          agentes y skills de apoyo al desarrollo (contexto, code review, seguridad)
```

---

## 6. Mapa de módulos

Agrupados como los ve el usuario en el menú lateral.

### Personal / RH
Expediente del empleado y todo lo que cuelga de él: relaciones laborales, movimientos,
cambios de adscripción, comisiones, becas, incapacidades, domicilios, licencias de conducir,
INE y cartilla militar, vacaciones, escolaridad, servicio médico, aumento anual, estado de
fuerza, hoja de servicio, reportes de altas y bajas, cumpleaños.
`RelacionesLabolesController`, `ComisionController`, `BecasController`, `ServicioMedicoController`,
`EstadoDeFuerzaController`, `MovimientosController` · vistas en `resources/views/RH/`.

### Asuntos Jurídicos y Procedimientos
Procedimientos disciplinarios, seguimiento de asuntos jurídicos, acuerdos.
`AsuntosJuridicosController`, `ProcedimientoController`.

### Asistencia
Checadas biométricas (ingesta por API), asistencia administrativa y operativa, planeación de
roles de servicio, reporte de **Cumplimiento de Asistencia** (matriz día por día que cruza el
rol planeado contra lo checado).
`AsistenciaController`, `BiometricAttendanceController`, `CumplimientoAsistenciaController`,
`ScheduleController`, `ServiceRolController` · servicios en `app/Services/CumplimientoAsistencia/`.

### Control de Unidades (flota de patrullas)
Alta y ficha de la unidad, estado operativo, mantenimientos preventivos y correctivos,
bitácoras de resguardo, **choques** (con carátula de siniestro y oficio a Jurídico),
reportes configurables, alertas de condición, movimientos de vehículo, y una familia entera de
**oficios** (alta, baja, rehabilitación, placa, reparación, cambio de resguardante,
transferencia a Presidencia).
`UnidadesPatrullaController`, `ChoquesController`, `MantenimientosVehiculosController`,
`VehicleMovementService`, `ReporteGeneradorController` · `resources/views/unidades-patrulla/`.

### Gasolina
Carga de consumos desde archivos de proveedor, dashboard, mapeo unidad↔proveedor,
**alertas de irregularidades** (consumo anómalo, unidad inactiva con carga, kilometraje) y
oficios derivados de esas alertas.
`ControlGasolinaController`, `OficioGasolinaController` · `app/Services/Gasolina/`.

### Almacén
Inventario general, entradas y salidas a distritos, resguardos de uniformes y bienes,
transferencias, requisiciones, contratos, reporte INEGI, reporte por tallas, papelera,
validación de solicitudes de material.
`AlmacenController`, `AlmacenNuevoController`, `AlmacenReportesController`,
`SolicitudesMaterialController`.

### Refacciones (submódulo de Almacén)
Doble inventario — **físico** y **virtual por distrito** —, entradas, salidas/vales,
traspasos, devoluciones, contratos, control de *cores* por artículo y solicitudes de refacción.
`SolicitudRefaccionesController`, `RefaccionesVirtualesController` · `app/Services/Refacciones/`.

### La Cueva
Almacén secundario con su propio catálogo, entradas, salidas y stock.
`LaCuevaController` · `app/Services/LaCueva/`.

### Patrimonio
Registro de activos (bienes muebles e inmuebles), resguardantes, bajas y proceso de baja,
transferencias a Presidencia, historial de cambios, auditoría de bienes, cámaras/DVR de
unidades, y el **archivo documental** (archiveros, carpetas, préstamos, transferencias).
`PatrimonioController`, `ArchivoPatrimonioController`, `BienAuditoriaController` ·
`app/Models/Patrimonio/`.

### Telecomunicaciones
Inventario de radios, resguardantes, ubicaciones, estados y oficios del área.
`TelecomunicacionesController`, `app/Http/Controllers/Telecom/` · `resources/views/telecom/`.

### Body Cams
Inventario y resguardo de cámaras corporales, con listas por distrito.
`ResguardoBodyCamController`.

### IPH / Informes policiales
**Informe Policial Homologado**, IPH de Justicia Cívica, **Parte Informativa** (v1 y v2) con
mapas, dashboards de ambos, informes de uso de fuerza, entrega de hechos, tarjetas informativas,
catálogo de delitos, colonias y calles.
`IphController`, `IphDashboardController`, `ParteInformativaController`,
`ParteInformativaDashboardController`, `TarjetaInformativaController`.

### Bitácoras
Bitácora de servicio, de autos robados y de resguardo de unidad, con firma del elemento.
`BitacoraController`, `BitacoramongoController` · Livewire en `app/Http/Livewire/Bitacoras/`,
lógica en `app/Services/Bitacoras/`.

### Academia y Capacitación
Convocatorias, aspirantes, cadetes, empleados en formación, clases a impartir, cursos y
capacitaciones, reconocimientos, evaluación de competencias básicas, estadísticas.
`AcademiaController`, `AcademiaCadetesController`, `CapacitacionController`,
`CursoCapacitacionController`, `ConvocatoriasController`.

### Declaraciones patrimoniales
Periodos de declaración, captura, revisión y generación del PDF oficial.
`DeclaracionesController`, `PeriodoDeclaracionesController`, `DeclaracionPdfService`.

### Trámites y documentos
Solicitud de documentos, constancias de nombramiento (individual y masiva), formatos,
oficios genéricos, volantes, anuncios y comunicados, historial de oficios.
`SolicitudDocController`, `FormatosController`, `OficioGenericoController`, `VolantesController`,
`AnnouncementController`.

### Estacionamiento
Plano de cajones, asignaciones, turnos, corte e importación masiva.
`EstacionamientoController`, `EstacionamientoV2Controller` · Livewire en
`app/Http/Livewire/Estacionamiento/`.

### Transparencia · INEGI · Estadística
Reportes para obligaciones de transparencia, reporte INEGI y estadísticas generales.
`TransparenciaController`, `InegiController`, `EstadisticaController`.

### Administración
Usuarios, roles, matriz de permisos, distritos, agrupamientos y subáreas, catálogos,
configuración de encabezados, cambios administrativos, métricas.
`UserController`, `PermissionsController`, `SettingController`, `CatalogosController`,
`MetricsController` · Livewire `UserPermissionMatrix`, `RoleManager`, `PermissionDistrict`.

---

## 7. Configuración del entorno

Variables relevantes (**nombres únicamente**; los valores viven en el `.env` de cada entorno y
nunca en el repositorio):

| Variable | Para qué |
|---|---|
| `DB_CONNECTION` · `DB_HOST` · `DB_PORT` · `DB_DATABASE` · `DB_USERNAME` · `DB_PASSWORD` | Conexión MySQL |
| `DB_URI` / `MONGO_DB_URI` · `MONGO_DB` | DSN y nombre de la base MongoDB — **obligatorias**, y no aparecen en `.env.example` |
| `GOOGLE_MAPS_API_KEY` | Mapas de IPH / Parte Informativa (vía `config/services.php`, nunca embebida en Blade) |
| `METRICS_ENABLED` · `METRICS_TTL_SECONDS` | Sistema de métricas |
| `ATTENDANCE_API_TOKEN` · `ATTENDANCE_ALLOWED_IP` · `ATTENDANCE_ENDPOINT_SLUG` | Ingesta biométrica |
| `SIDEBAR_COLOR` · `BAR_COLOR` | Color del menú para distinguir entornos a simple vista |
| `MAIL_*` | Envío de correo (no disponible en todos los entornos) |

Tras cambiar `.env` o `config/`: `php artisan config:clear`.

En producción, `AppServiceProvider` fuerza HTTPS cuando se accede por nombre de host, comparte
los encabezados configurables (`/settings`) con todas las vistas e inyecta los contadores de
pendientes del menú mediante *view composers*.

---

## 8. Convenciones y deuda técnica conocida

Cosas que sorprenden al llegar, dichas sin adorno:

- **`routes/web.php` tiene ~3,500 líneas y 416 KB.** Es el archivo más editado del repositorio.
  Los grupos con `prefix()` son la excepción, no la regla.
- **Idioma mixto.** Nombres de clases, rutas y columnas alternan español e inglés
  (`UnidadesPatrulla` junto a `VehicleMovementService`), a veces dentro del mismo módulo.
  Hay erratas fosilizadas en nombres de archivo (`RelacionesLaboles`, `AlmacenFisico` con
  prefijo `/`), que no se corrigen porque están referenciadas.
- **No hay entorno de pruebas usable.** `.env.testing` no tiene credenciales reales y la suite
  PHPUnit falla en `setUp()` sin importar el cambio. Los tests existentes valen como
  documentación de intención, no como verificación. **Nunca reportar "las pruebas pasan/fallan"
  como evidencia.** La verificación real es `php -l`, `php artisan tinker`, y abrir la vista en
  el navegador — un Blade con un `@if` dentro de un comentario JS revienta en runtime y `php -l`
  lo deja pasar.
- **Modelos duplicados por base de datos.** Ver §4.2. Es la fuente número uno de bugs al tocar
  un módulo desconocido.
- **Sin claves foráneas entre MySQL y MongoDB.** Las relaciones son por número de empleado o
  `idPersona`, y hay datos históricos sucios (fechas guardadas como texto con formatos mezclados,
  códigos patrimoniales a los que Excel les comió los ceros a la izquierda). Cualquier
  `whereIn` masivo debe verificarse contra el conteo esperado: un empate de 0 registros es mudo.
- **Configuración por archivo `config/` para cada variante de oficio.** Funciona, pero la
  dirección deseada es que las definiciones vivan en datos editables por el usuario, no en un
  archivo por caso.
- **JS de módulo sin cache-busting.** Un archivo en `public/js/` editado puede seguir sirviéndose
  cacheado; los síntomas llegan como "el buscador no funciona".
- **Scripts sueltos en la raíz** (`check_password.php`, `debug_mongo.php`, `reset_script.php`,
  `_probe4_tmp.php`, volcados `.json`): restos de depuración, no parte del sistema.
- **`README.md` está desactualizado** — describe el proyecto genérico "SecureDocFlow" del
  arranque, con instrucciones y datos de contacto que ya no aplican. Este documento lo sustituye
  como punto de entrada.

---

## 9. Flujo de trabajo

### Ramas y commits

- Ramas: `feat/<tema-en-kebab-case>` para funcionalidad, `fix/<tema>` para correcciones,
  ocasionalmente `refactor/`. Una rama por petición del área solicitante.
- Mensajes: Conventional Commits (`feat:`, `fix:`, `refactor:`, `style:`, `docs:`), mayoría en
  español.
- Integración a `main` por Merge Request en el GitLab autoalojado del equipo.

### Ejecución

Hay dos formas de correr el proyecto según la máquina; ambas conviven:

**Con Docker** (entorno de referencia): PHP-FPM, Nginx, MySQL y MongoDB en contenedores.
Los comandos van dentro del contenedor de la app:

```bash
docker exec <contenedor-app> php artisan migrate
docker exec <contenedor-app> php -l ruta/al/archivo.php
docker exec <contenedor-app> php artisan tinker
```

El código se monta por bind-mount: editar en el host se refleja al instante, sin rebuild.

**Con PHP en el host**:

```bash
php artisan serve
npm run watch          # compilación de assets con recarga
npm run prod           # build de producción
php artisan migrate
```

### Verificación antes de un MR

1. `php -l` sobre cada archivo PHP tocado.
2. Abrir la vista afectada en el navegador — el Blade solo falla renderizando.
3. Si el cambio toca PDFs, **medir el PDF generado**, no confiar en el CSS: las hojas tienen
   `overflow: hidden` y lo que no cabe se recorta en silencio.
4. Revisar las dos capas de permisos si se añadió o modificó una ruta restringida.
5. Las migraciones se despliegan por `--path` explícito; `php artisan migrate` a secas no es
   seguro en producción.

### Migraciones y datos

Las migraciones no solo tocan MySQL: varias crean **índices de MongoDB** (patrón
`create_*_indexes`). Los comandos de `app/Console/Commands/` son en su mayoría *backfills* de un
solo uso, conservados como registro de cómo quedaron los datos.

---

## 10. Por dónde empezar

1. Leer este documento y el `CLAUDE.md` del repositorio.
2. Abrir [resources/views/layouts/menu.blade.php](resources/views/layouts/menu.blade.php):
   es el mapa real de lo que existe, en el orden en que lo ve el usuario.
3. Elegir un módulo, localizar su controlador en [app/Http/Controllers/](app/Http/Controllers/)
   y **verificar qué modelos usa** antes de escribir una línea.
4. Buscar la ruta en `routes/web.php` por nombre (`->name('modulo.accion')`) — es más rápido que
   por URL.
5. Revisar [docs/](docs/) y [plans/](plans/): varios módulos tienen documentación funcional
   escrita durante su construcción.
