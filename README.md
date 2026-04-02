# Marketplace Guard POC

## 1. Qué es esto

Este repo es un POC en Python para detectar problemas de pricing en marketplaces: margen roto, promos que dejan pérdida e inconsistencias de precio entre canales. Hoy corre con datos mock, reglas claras y una API simple para mostrar alertas priorizadas y simular acciones como bloquear una publicación.

## 2. Problema que resuelve

En ecommerce marketplace es fácil que un SKU quede mal precificado sin que nadie lo vea a tiempo. Puede pasar por una promo agresiva, fees mal considerados, subsidio de envío, o diferencias de precio entre canales. El resultado es simple: se vende con margen roto o se genera una inconsistencia comercial que hay que revisar rápido. Este proyecto busca detectar esos casos, priorizarlos y sugerir qué hacer.

## 3. Qué hace hoy

El POC actual ya hace esto:

- guarda catálogo, canales, listings, precios, costos y promos en SQLite
- corre reglas determinísticas para detectar anomalías
- crea alertas con severidad, impacto estimado y `priority_score`
- explica por qué una alerta es prioritaria con desglose transparente
- expone todo por API
- simula acciones operativas:
  - bloquear SKU/publicación
  - marcar revisión
  - alertar

Lo importante: la lógica de detección no depende de un modelo. Es explícita y trazable.

## 4. Demo mental

Piensa en un ecommerce manager entrando a un panel.

Vería algo como esto:

- alerta crítica para `SKU-RUN-001` en Mercado Libre Chile
- el sistema dice que el margen está roto
- muestra pérdida estimada: `55.542,70 CLP`
- muestra prioridad: `77.86`
- sugiere: `bloquear publicación`

Luego entra al detalle y ve:

- costo
- precio final
- margen calculada
- explicación simple del problema
- desglose del `priority_score`
- acciones disponibles

Si intenta bloquear, el sistema puede exigir aprobación antes de ejecutar la simulación.

## 5. Arquitectura simple

Sin tecnicismos innecesarios, el sistema tiene 4 piezas:

1. Datos mock
   Guarda productos, canales, listings, precios, costos, promociones y alertas en SQLite.

2. Motor de detección
   Revisa reglas simples de negocio:
   - margen roto
   - promo que rompe margen
   - inconsistencia de precio entre canales

3. Priorización
   Cada alerta obtiene:
   - `estimated_loss`
   - `impact_score`
   - `priority_score`
   - desglose del score por pérdida, margen y volumen

4. API
   Expone alertas y acciones para que un frontend pueda consumirlas.

Flujo real:

```text
datos mock -> detección -> alerta -> prioridad -> acción sugerida -> acción simulada
```

## 6. Cómo correrlo paso a paso

Desde la raíz del repo.

### Opción recomendada: crear entorno limpio

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e .
```

### Levantar la API

```bash
PYTHONPATH=src .venv/bin/uvicorn marketplace_guard.api:app --reload
```

La API queda disponible en:

- `http://127.0.0.1:8000`
- docs automáticas: `http://127.0.0.1:8000/docs`

### Probar una corrida completa del POC

Esto ejecuta una simulación y te muestra alertas reales del sistema:

```bash
PYTHONPATH=src .venv/bin/python examples/run_marketplace_guard.py
```

### Correr tests

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_marketplace_guard
```

## 7. Endpoints disponibles

### `GET /health`

Confirma que la API levantó.

### `GET /products`

Lista productos del catálogo mock.

### `GET /alerts`

Devuelve las alertas actuales, ordenables por `priority_score`.

### `GET /alerts/{id}`

Devuelve el detalle de una alerta:

- datos del alert
- pricing si aplica
- timeline
- acciones ejecutadas

### `POST /simulate-run`

Dispara una corrida de detección sobre los datos mock y crea/refresca alertas.

Body mínimo:

```json
{
  "session_id": "demo-run",
  "requested_by": "demo-user"
}
```

### `POST /alerts/{id}/actions`

Ejecuta una acción sobre una alerta.

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

## 8. Ejemplo de respuesta real

Ejemplo real del sistema hoy para una alerta de margen roto:

```json
{
  "id": 1,
  "alert_type": "broken_margin",
  "severity": "critical",
  "status": "open",
  "currency": "CLP",
  "sku": "SKU-RUN-001",
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
- `priority_score`: prioridad operativa total
- `estimated_loss_component`: cuánto pesa la pérdida en la prioridad
- `negative_margin_component`: cuánto pesa la margen negativa
- `volume_component`: cuánto pesa el volumen de ventas

## 9. Qué NO es

Esto no es:

- un sistema productivo
- una integración real con marketplaces
- un motor de pricing automático
- un sistema con autenticación o multiusuario
- una herramienta con acciones reales sobre catálogos externos

También es importante esto:

- los datos son mock
- las acciones son simuladas
- no hay frontend final todavía
- no hay observabilidad ni hardening de producción

## 10. Próximos pasos

Los dos pasos obvios desde acá son:

### Frontend mínimo

Construir una UI simple tipo cockpit operativo para mostrar:

- inbox de alertas
- detalle
- action panel
- timeline

### Copilot

Agregar una capa de explicación en lenguaje simple para cada alerta.

Importante:

- el copilot no detecta anomalías
- no reemplaza reglas
- solo explica el problema, el impacto y la acción sugerida

---

Si solo quieres validar que el proyecto funciona, estos 2 comandos son suficientes:

```bash
PYTHONPATH=src .venv/bin/uvicorn marketplace_guard.api:app --reload
```

En otra terminal:

```bash
PYTHONPATH=src .venv/bin/python examples/run_marketplace_guard.py
```
