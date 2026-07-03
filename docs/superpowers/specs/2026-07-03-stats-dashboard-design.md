# Stats Dashboard — Diseño

**Fecha:** 2026-07-03  
**Proyecto:** IURISYNC  
**Alcance:** Reemplazar el panel de estadísticas matplotlib (estático, embebido en tkinter) por un dashboard interactivo que se abre en el navegador, servido por Flask local.

---

## Problema actual

El panel existente (`ui/stats_view.py`) embebe matplotlib en tkinter con 3 visualizaciones estáticas: volumen mensual, top tipos, tabla de estado. No tiene filtros, tooltips, interactividad ni KPIs. La experiencia es funcional pero no útil para tomar decisiones.

---

## Objetivo

Un dashboard que el equipo operativo pueda abrir con un clic y que responda inmediatamente preguntas como: *¿el scraper corrió ayer?, ¿qué fuente lleva más días sin capturar?, ¿cuántos documentos llevamos esta semana?*

---

## Arquitectura

### Componentes nuevos

| Archivo | Responsabilidad |
|---|---|
| `analytics/server.py` | Flask app — arranque, rutas, lógica de filtrado |
| `analytics/templates/dashboard.html` | UI completa: KPIs, filtros, gráficas (Plotly.js) |

### Componentes modificados

| Archivo | Cambio |
|---|---|
| `analytics/metrics.py` | Agregar `kpis()` y `actividad_diaria()` |
| `ui/stats_view.py` | Reemplazar matplotlib por botón que abre `localhost:5050` |
| `run_gui.py` | Arrancar Flask en hilo daemon al iniciar la app |

### Fuentes de datos

- **`memory.db`** — métricas operativas (total, recencia, actividad diaria). Siempre disponible, sin autenticación.
- **Google Sheets** — métricas analíticas (tipos de documento, volumen mensual por fuente, % en Drive). Carga asíncrona; si falla, el dashboard muestra lo que puede con memory.db.

---

## Rutas Flask

### `GET /`
Sirve `dashboard.html`. El HTML hace fetch a `/api/datos` al cargar.

### `GET /api/datos`
Parámetros opcionales: `fuente` (string), `desde` (YYYY-MM-DD), `hasta` (YYYY-MM-DD).

Respuesta JSON:
```json
{
  "kpis": {
    "total": 4231,
    "esta_semana": 127,
    "fuentes_activas": 6,
    "fuentes_total": 7,
    "pct_drive": 89
  },
  "actividad_diaria": [
    {"fecha": "2026-06-01", "total": 43},
    ...
  ],
  "volumen_mensual": {
    "meses": ["2026-01", "2026-02", ...],
    "series": {
      "Corte Constitucional": [12, 18, ...],
      ...
    }
  },
  "top_tipos": [
    {"tipo": "Auto admitiendo recurso", "total": 312},
    ...
  ],
  "estado_fuentes": [
    {
      "fuente": "Corte Constitucional",
      "ultima_captura": "2026-07-02",
      "dias_inactivo": 1,
      "estado": "Activa",
      "total_docs": 890
    },
    ...
  ]
}
```

Los filtros `fuente`, `desde`, `hasta` se aplican en el servidor antes de calcular métricas.

---

## Nuevas métricas (`analytics/metrics.py`)

### `kpis(db, df) -> dict`
- `total`: `Memory.total_docs()`
- `esta_semana`: query memory.db `WHERE downloaded_at >= date('now', '-7 days')`
- `fuentes_activas`: fuentes distintas con `downloaded_at` en los últimos 7 días
- `fuentes_total`: fuentes distintas totales en memory.db
- `pct_drive`: si df disponible, `% filas con Enlace Drive no vacío`; si no, `None`

### `actividad_diaria(db, desde, hasta) -> list[dict]`
Query memory.db agrupando `DATE(downloaded_at)` en el rango dado. Devuelve lista `[{fecha, total}]` para los últimos 30 días por defecto.

---

## UI — Dashboard HTML

### Layout

```
┌──────────────────────────────────────────────────────────┐
│  📊 IURISYNC Analytics                      [Actualizar] │
├──────────────┬──────────────┬──────────────┬────────────┤
│  4,231       │  127         │  6 / 7       │  89%       │
│  Total docs  │  Esta semana │  Fuentes OK  │  En Drive  │
├──────────────────────────────────────────────────────────┤
│  Fuente: [Todas ▼]   Desde: [____]   Hasta: [____]      │
├──────────────────────────────────────────────────────────┤
│                                                          │
│         Actividad diaria — últimos 30 días               │
│         [barras verticales, interactivas]                │
│                                                          │
├─────────────────────────────┬────────────────────────────┤
│  Volumen mensual x fuente   │  Estado de fuentes         │
│  [stacked bar interactivo]  │  [tabla con badges]        │
├─────────────────────────────┴────────────────────────────┤
│  Top tipos de documento                                  │
│  [horizontal bar, filtrable]                             │
└──────────────────────────────────────────────────────────┘
```

### KPI Tiles
4 cards con número grande, etiqueta abajo, borde izquierdo de color (azul / verde / naranja según umbral). Si `pct_drive < 80%` el tile cambia a naranja.

### Actividad diaria
Barras verticales por día (Plotly bar chart). Color azul del tema. Tooltip: fecha + cantidad. Si un día tiene 0, la barra es visible pero con color rojo tenue — señal visual de hueco.

### Volumen mensual por fuente
Stacked bar interactivo (Plotly). Leyenda clickeable para mostrar/ocultar fuentes. Mismo comportamiento que el actual pero con hover y zoom.

### Estado de fuentes
Tabla HTML (no Plotly). Badge verde "Activa" / rojo "Inactiva" en columna Estado. Columnas: Fuente, Última captura, Días inactivo, Total docs, Estado.

### Top tipos
Horizontal bar (Plotly). Limitado a 20 tipos. Labels truncados a 35 caracteres con tooltip completo.

### Filtros
`<select>` para fuente, `<input type="date">` para rango. Botón "Aplicar" dispara `fetch('/api/datos?...')`. Respuesta actualiza todos los gráficos vía `Plotly.react()`.

### Estilo
- Fondo: `#1e2130` (tema IURISYNC)
- Cards: `#252b3b`
- Acento: `#4f8ef7`
- Fuente: system-ui
- Plotly theme: `plotly_dark`
- Sin frameworks CSS externos — todo inline/`<style>`

---

## Servidor Flask (`analytics/server.py`)

```python
# arranque en run_gui.py:
from analytics.server import start_server
port = start_server()  # hilo daemon, intenta 5050-5052, retorna el puerto usado
```

- `start_server(port)`: lanza `app.run()` en `threading.Thread(daemon=True)`
- Intenta puertos 5050, 5051, 5052; si todos ocupados, loggea warning y el botón en la UI muestra "Puerto ocupado"
- `SheetsDataLoader` se llama en `/api/datos` con timeout de 10s; si falla, `df = None` y se omiten métricas de Sheets

---

## Modificaciones a `ui/stats_view.py`

El frame actual se reemplaza por una pantalla simple:
- Texto explicativo: "El dashboard se abre en tu navegador"
- Botón "Abrir dashboard" → `webbrowser.open("http://localhost:5050")`
- Indicador de estado del servidor (activo / no disponible)

---

## Modificaciones a `run_gui.py`

```python
from analytics.server import start_server
_server_port = start_server()  # antes de App()
```

El puerto se pasa a `StatsView` para construir la URL correcta.

---

## Consideraciones

- **Sin dependencias nuevas pesadas**: Flask y Plotly ya están en el entorno (o se agregan a `requirements.txt`). Plotly.js se carga desde CDN — requiere internet cada vez que se abre el dashboard.
- **Sin estado persistente en Flask**: cada request a `/api/datos` recalcula todo. Con ~5000 docs el tiempo de respuesta es < 1s.
- **Puerto hardcodeado en HTML**: el HTML generado por Jinja2 recibe el puerto como variable de template, por si cambia.
- **Seguridad**: Flask corre en `127.0.0.1` únicamente, no expuesto a la red.
