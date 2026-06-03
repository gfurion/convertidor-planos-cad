# Plan de Mejora — Convertidor de Planos CAD

> Documento de planificación para las próximas versiones del producto.
> Versión: 1.0 — Mayo 2026

---

## Visión General

Evolucionar de una herramienta funcional básica a un producto profesional:
con mejor UX, más funcionalidades, distribución pulida y modelo de negocio claro.

---

## Fase 1: Arquitectura y Calidad (Semanas 1-3)

### Refactorización del código
- [ ] Dividir `convertidor.py` en módulos con responsabilidades claras:
  - `gui/` — Interfaz de usuario
  - `engine/` — Lógica de conversión con ODA
  - `models/` — Modelos de datos (versiones, configuraciones)
  - `utils/` — Utilidades (logging, i18n, helpers)
- [ ] Eliminar deuda técnica acumulada

### Testing y CI/CD
- [ ] Tests unitarios para el motor de conversión
- [ ] Tests de integración para la GUI
- [ ] GitHub Actions: correr tests en cada PR
- [ ] Linting con ruff + type checking con mypy

### Logging robusto
- [ ] Archivo `.log` rotativo con niveles (INFO, WARNING, ERROR)
- [ ] Contexto por archivo convertido
- [ ] Modo debug activable por bandera

### Control de versiones
- [x] Git inicializado y primer commit realizado
- [ ] Semver estricto (MAJOR.MINOR.PATCH)
- [ ] Changelog en cada release
- [ ] Tags en git para cada versión

---

## Fase 2: UX de Primera Clase (Semanas 4-6)

### Vista previa de planos
- Generar thumbnail al seleccionar archivos
- Mostrar en cuadrícula o lista con íconos
- Información útil: versión actual del DWG, tamaño, fecha

### Progreso granular
- [x] Barra de progreso por archivo (no solo "procesando...")
- [x] Indicador: "Archivo 3 de 15: proyecto_planta.dwg"
- [ ] Tiempo estimado restante

### Drag & drop
- [x] Arrastrar archivos .dwg/.dxf directamente a la ventana
- [ ] Arrastrar carpetas completas
- [x] Feedback visual (highlight) al pasar sobre la zona de drop

### Modo carpeta completa
- [ ] Botón "Seleccionar carpeta" además de "Seleccionar archivos"
- [ ] Procesar recursivamente todos los DXF/DWG dentro
- [ ] Mantener estructura de subcarpetas en el destino

### Historial de conversiones
- [ ] Tabla persistente (JSON local) con:
  - Fecha y hora
  - Archivo origen
  - Versión destino
  - Estado (éxito/error)
  - Ruta del archivo resultado
- [ ] Botón "Limpiar historial"
- [ ] Opción de re-convertir desde el historial

### Apariencia
- [x] Tema oscuro (superhero) implementado
- [ ] Alternar modo oscuro/claro
- [ ] Recordar preferencia del usuario
- [ ] Botón de cambio rápido en la barra de herramientas

### Panel de log expandible
- [ ] Sección plegable en la parte inferior
- [ ] Muestra salida en tiempo real de ODA
- [ ] Útil para diagnosticar archivos problemáticos
- [ ] Botón "Copiar log al portapapeles"

### Indicación de selección múltiple
- [x] Texto informativo al lado del botón: *"Puedes seleccionar uno o varios archivos DXF/DWG"*
- [x] Badge dinámico después de seleccionar: *"12 archivos seleccionados"*
- [x] Tooltip en el botón de selección
- [x] Placeholder vacío: *"Arrastra aquí tus planos o haz clic en 'Buscar y Convertir Planos'"*
- [x] Título personalizado en la ventana `filedialog`: *"Selecciona uno o varios archivos DXF/DWG"*

### Notificaciones
- [ ] Toast al completar: "15 archivos convertidos exitosamente"
- [ ] Notificación incluso si la app está minimizada
- [ ] Sonido opcional al finalizar

---

## Fase 3: Nuevas Capacidades (Semanas 7-9)

### Conversión bidireccional
- [ ] DWG → DXF además de DXF → DWG (actual)
- [ ] Selector de formato de salida: DWG / DXF
- [ ] Mismas opciones de versión para ambos formatos

### Procesamiento paralelo
- [ ] Usar `concurrent.futures.ProcessPoolExecutor`
- [ ] Lanzar N conversiones simultáneas (según núcleos de CPU)
- [ ] Control de concurrencia: opción "Usar [1-8] hilos"
- [ ] Benchmark automático: detectar óptimo

### Presets de conversión
- [ ] Guardar combinaciones frecuentes como perfiles:
  - Versión destino
  - Carpeta destino
  - Formato de salida (DWG/DXF)
  - Opciones de auditoría/purga
- [ ] Presets por defecto + personalizados
- [ ] Selector rápido tipo dropdown

### Exportar resumen
- [ ] Generar CSV con: nombre, origen, destino, versión, estado, timestamp
- [ ] Opción "Abrir carpeta de destino" al finalizar
- [ ] Copiar resumen al portapapeles

### Purgado y limpieza
- [ ] Opción de purgar: capas vacías, bloques no usados, estilos redundantes
- [ ] Vía parámetros adicionales de ODA
- [ ] Checkbox en la UI: "Limpiar planos (purga)"

### CLI (interfaz de línea de comandos)
```
convertidor.exe --input "C:\planos" --output "C:\convertidos" ^
                --version ACAD2018 --format DWG --recurse --purge
```
- [ ] Útil para integraciones con otros softwares
- [ ] Modo silencioso (sin GUI) con logging a archivo
- [ ] Códigos de salida estándar (0=éxito, 1=error parcial, 2=error total)

---

## Fase 4: Distribución Profesional (Semanas 10-12)

### Instalador Inno Setup ✅ COMPLETADO
- [x] Registrar asociación de archivos .dwg y .dxf
- [x] Acceso directo en menú inicio / escritorio
- [x] Desinstalador limpio
- [x] Personalización de ruta de instalación
- [x] Script `instalador.iss` creado
- [x] Instalador generado: `Setup_Convertidor_CAD_v2.exe` (59.4 MB)

### Auto-actualizador
- [ ] Consultar GitHub Releases al inicio
- [ ] Mostrar "Nueva versión disponible: v2.3.0"
- [ ] Descargar e instalar con un clic
- [ ] Verificación de integridad (SHA-256)
- [ ] Política de actualización: automatic/manual/disabled

### Firma digital
- [ ] Obtener certificado Authenticode (Comodo, DigiCert, etc.)
- [ ] Firmar el ejecutable en el pipeline de build
- [ ] Eliminar advertencias de SmartScreen

### Dos versiones ✅ COMPLETADO
- [x] **Portable**: Un solo EXE con ODA dentro (`dist\convertidor.exe` — 78.5 MB)
- [x] **Instalable**: Inno Setup (`installer\Setup_Convertidor_CAD_v2.exe` — 59.4 MB)

### Canal de distribución
- [ ] GitHub Releases (gratuito)
- [ ] Web propia con landing page (opcional)
- [ ] Documentación técnica y de usuario

---

## Fase 5: Estrategia de Negocio (Post-lanzamiento)

### Modelo Freemium
| Producto | Precio | Diferenciación |
|---|---|---|
| Convertidor CAD Free | Gratis | Máx 5 archivos/lote, 1 hilo, sin presets |
| Convertidor CAD Pro | $29 USD perpetua | Ilimitado, paralelo, presets, historial, CLI |
| Convertidor CAD Enterprise | $99 USD/año | Lo anterior + actualizaciones automáticas, soporte prioritario, licencias volumen |

### Canales de venta
- [ ] Venta directa (Gumroad / Lemon Squeezy)
- [ ] Licencias por volumen para empresas
- [ ] Trials de 14 días para Pro

### Soporte
- [ ] Email para Pro/Enterprise
- [ ] FAQ online
- [ ] Reporte anónimo de errores (opt-in telemetry)

---

## Roadmap Visual

```
Sem 1-3     Sem 4-6      Sem 7-9       Sem 10-12     Post
══════════   ══════════   ═══════════   ═══════════   ═══════════════
Refactor     UX v2        Features      Distribución  Negocio
┌─────────┐  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐
│ Módulos  │ │ Previews │ │ DWG→DXF  │ │ MSI/WiX  │ │ Freemium     │
│ Tests    │ │ Progreso │ │ Paralelo │ │ Updater  │ │ Precios      │
│ Logging  │ │ Drag&drop│ │ Presets  │ │ Firma    │ │ Ventas       │
│ CI/CD    │ │ Historial│ │ CLI      │ │ 2 vars   │ │ Soporte      │
└─────────┘  └─────────┘  └──────────┘  └──────────┘  └──────────────┘
```

---

## Notas Técnicas

- **ODA File Converter**: Verificar compatibilidad de versión con cada release
- **Qt6**: ODA usa Qt6 — mantener sincronizadas las DLLs empaquetadas
- **PyInstaller**: Evaluar Nuitka como alternativa (mejor rendimiento, antimalware)
- **Python**: Migrar de Python 3.x → 3.x+ según necesidad
- **Packaging**: Investigar `briefcase` o `NSIS` como alternativas a PyInstaller
