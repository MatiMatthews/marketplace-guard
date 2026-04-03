# Marketplace Guard

## 1. Qué es Marketplace Guard

Marketplace Guard es un POC para detectar problemas de pricing en marketplaces y volverlos accionables en una interfaz simple. Está pensado para un `ecommerce manager` que necesita ver rápido qué SKU tiene margen roto, qué diferencia de precio entre canales merece revisión y qué acción conviene tomar primero.

El problema que resuelve es directo: en marketplace es fácil vender con pérdida sin darse cuenta. Eso puede pasar por promos agresivas, fees mal considerados, subsidios de envío o desalineación de precios entre canales. Marketplace Guard toma esos datos, detecta anomalías, las prioriza y las muestra en un cockpit operativo.

## 2. Qué hace hoy

Hoy el proyecto ya incluye:

- backend en Python/FastAPI para detección de alertas
- modelo SQLite con productos, listings, precios, costos, promociones y alertas
- motor de reglas determinístico para:
  - margen roto
  - promo que rompe margen
  - inconsistencia de precio entre canales
- scoring de prioridad con:
  - `estimated_loss`
  - `priority_score`
  - breakdown por pérdida, margen negativo y volumen
- acciones simuladas:
  - bloquear SKU
  - bloquear publicación
  - marcar revisión
- frontend en React/Vite/Tailwind con dashboard único

Importante: la detección no depende de LLM. La lógica es explícita, trazable y hoy corre con datos mock.

## 3. Flujo demo

El flujo demo actual es este:

1. levantas el backend
2. levantas el frontend
3. abres el dashboard en el navegador
4. haces click en `Cargar demo`
5. el frontend llama a `POST /simulate-run`
6. aparecen alertas reales en la inbox
7. seleccionas una alerta para ver detalle, score y timeline
8. pruebas acciones como `Bloquear SKU`, `Bloquear publicación` o `Marcar revisión`

En menos de 10 segundos ya se entiende el valor del sistema:

- qué SKU está mal
- en qué canal
- cuánta pérdida potencial tiene
- qué tan prioritaria es
- qué acción conviene ejecutar

## 4. Arquitectura simple

Sin tecnicismos innecesarios, hoy el sistema tiene estas piezas:

### Backend

- Python + FastAPI
- expone endpoints para alertas, detalle, simulación y acciones

### Base de datos

- SQLite
- guarda catálogo, listings, precios, costos, promociones, alertas y action runs

### Runtime

- usa el starter kit existente de `runtime`, `tools`, `sessions` y `policy`
- corre el flujo:

```text
datos mock -> detección -> alerta -> scoring -> acción sugerida -> acción simulada
```

### Frontend

- React + Vite + Tailwind + TypeScript
- dashboard único tipo cockpit
- consume el backend por API

## 5. Cómo correrlo paso a paso

Todo se corre desde la raíz del repo.

### Backend

#### 1. Crear entorno e instalar dependencias

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e .
```

#### 2. Levantar la API

```bash
PYTHONPATH=src .venv/bin/uvicorn marketplace_guard.api:app --host 127.0.0.1 --port 8000
```

La API queda disponible en:

- `http://127.0.0.1:8000`
- docs: `http://127.0.0.1:8000/docs`

### Frontend

#### 1. Instalar dependencias

```bash
cd frontend
npm install
```

#### 2. Levantar el dashboard

```bash
npm run dev -- --host 127.0.0.1 --port 5173
```

Abrir en el navegador:

- `http://127.0.0.1:5173`

El frontend usa proxy a `/api`, así que por defecto espera el backend local en `127.0.0.1:8000`.

### Demo rápida completa

Si ya tienes backend y frontend arriba:

1. abre `http://127.0.0.1:5173`
2. haz click en `Cargar demo`
3. selecciona una alerta
4. prueba una acción

## 6. Endpoints principales

### `GET /alerts`

Lista las alertas actuales, ordenadas por `priority_score`.

### `GET /alerts/{id}`

Devuelve el detalle de una alerta:

- datos de la alerta
- pricing si aplica
- timeline
- acciones ejecutadas

### `POST /simulate-run`

Dispara una corrida de detección con los datos mock y crea o actualiza alertas.

Body mínimo:

```json
{
  "requested_by": "demo-user"
}
```

### `POST /alerts/{id}/actions`

Ejecuta una acción simulada sobre una alerta.

Ejemplos:

```json
{
  "action_type": "mark_review",
  "requested_by": "demo-user",
  "approved": false
}
```

```json
{
  "action_type": "simulate_block_sku",
  "requested_by": "demo-user",
  "approved": true
}
```

## 7. Qué muestra el frontend

El frontend actual es un dashboard único con 3 zonas:

### Inbox

Lista de alertas ordenada por `priority_score desc`, mostrando:

- SKU
- canal
- tipo de alerta
- `estimated_loss`
- `currency`
- `priority_score`
- acción sugerida

### Detail

Panel central con:

- SKU
- canal / publicación
- costo
- precio
- margen
- `estimated_loss`
- `currency`
- breakdown del `priority_score`
- explicación del problema

### Action Panel y Timeline

A la derecha:

- botones de acción
- approval cuando aplica
- timeline de eventos de la alerta

## 8. Ejemplo real de alerta

Ejemplo real del sistema hoy, después de correr `Cargar demo`:

```json
{
  "id": 1,
  "alert_type": "broken_margin",
  "severity": "critical",
  "status": "open",
  "product_id": 1,
  "listing_id": 101,
  "currency": "CLP",
  "sku": "SKU-RUN-001",
  "product_name": "Nike Pegasus 40 Black 42",
  "channel_code": "ml_cl",
  "channel_name": "Mercado Libre Chile",
  "title": "Margen roto en SKU-RUN-001 / ml_cl",
  "explanation": "El listing SKU-RUN-001 en ml_cl queda con margen -4958.5 CLP y un gap de 8958.5 CLP contra el margen mínimo requerido.",
  "estimated_loss": 55542.7,
  "impact_score": 55.54,
  "priority_score": 77.86,
  "estimated_loss_component": 55.54,
  "negative_margin_component": 9.92,
  "volume_component": 12.4,
  "suggested_action": "simulate_block_sku"
}
```

Qué significa:

- `estimated_loss`: pérdida potencial estimada en dinero
- `currency`: moneda del cálculo
- `priority_score`: prioridad total de la alerta
- `estimated_loss_component`: peso de la pérdida en la prioridad
- `negative_margin_component`: peso del margen negativo
- `volume_component`: peso del volumen

## 9. Limitaciones actuales

Hoy el proyecto todavía tiene estas limitaciones:

- las acciones son simuladas, no pegan a marketplaces reales
- `bloquear SKU` y `bloquear publicación` comparten el mismo endpoint backend
- falta `publication_id` nativo en el detail; hoy la UI cae a `listing_id` o `N/A`
- los datos siguen siendo mock
- no hay autenticación
- la UI es funcional y limpia, pero no está pulida como producto final

También es importante:

- no es un sistema de producción
- no hay integraciones reales
- no hay observabilidad ni hardening

## 10. Próximos pasos

Los siguientes pasos razonables son:

- refinamiento visual del dashboard
- distinguir en backend `bloquear SKU` vs `bloquear publicación`
- agregar capa copilot/LLM para explicar cada alerta en lenguaje simple
- correr la demo con datos más cercanos a operación real

Importante para la capa copilot:

- no detecta anomalías
- no reemplaza reglas
- solo explica problema, impacto y acción sugerida

---

Si quieres validar el proyecto rápido, estos son los dos procesos mínimos:

Terminal 1:

```bash
PYTHONPATH=src .venv/bin/uvicorn marketplace_guard.api:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Después abre:

- [http://127.0.0.1:5173](http://127.0.0.1:5173)

y usa `Cargar demo`.
