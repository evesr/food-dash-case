# -*- coding: utf-8 -*-
"""
============================================================================
 PROTOTIPO FUNCIONAL (MVP) - Clasificador de Tickets de Soporte "FoodDash"
 Postulación: AI Solutions Expert · Healthatom
============================================================================

Arquitectura de 3 capas:
  - CAPA 1 (Python puro):  Filtro determinista. Descarta / marca tickets
                           sin información suficiente ANTES de gastar una
                           llamada al LLM.
  - CAPA 2 (LLM Llama):    Diagnóstico de causa raíz cruzando la queja del
                           usuario contra la telemetría de los logs.
                           Usa Llama 3.1 (gratis) vía la API de Groq.
  - CAPA 3 (Python puro):  Motor de reglas que mapea la clasificación a una
                           acción concreta del árbol de decisiones.

Salida: tickets_clasificados_mvp.csv
Entrada: tickets.json (los campos ausentes se manejan como NaN)

Diseñado para ejecutarse en Google Colab.
  Instalar dependencia (en Colab):  !pip install -q groq pandas
============================================================================
"""

import json
import os
import re
import time

import pandas as pd
from groq import Groq

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Usar esta key temporal.
API_KEY = "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"

# Rutas ancladas a la ubicación de ESTE script, no al directorio de ejecución.
# Así la lectura del JSON y la escritura del CSV funcionan sin importar desde
# dónde se ejecute el programa (terminal, botón Run de VS Code, etc.).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_JSON = os.path.join(BASE_DIR, "tickets.json")
OUTPUT_CSV = os.path.join(BASE_DIR, "tickets_clasificados_mvp.csv")

# Modelo y control de rate-limit.
MODEL_NAME = "llama-3.1-8b-instant"
SLEEP_BETWEEN_CALLS = 2    # segundos entre llamadas (holgado para 30 req/min)

# Cliente global de Groq.
client = Groq(api_key=API_KEY)


# ============================================================================
# TOOLS DEL AGENTE (Entregable 6)
# ----------------------------------------------------------------------------
# En producción cada función haría una llamada real (API de telemetría, Jira,
# CRM, mensajería). En este MVP se SIMULAN: registran su invocación y devuelven
# un payload representativo. Así el prototipo demuestra CUÁNDO y CÓMO el agente
# usaría cada herramienta, sin depender de infraestructura externa.
# ============================================================================

# Estado en memoria que simula la base de datos de tickets de soporte.
# Se usa para la detección de duplicados (buscar_tickets_abiertos / merge).
_TICKETS_ABIERTOS = {}  # order_id -> ticket_id original


def consultar_logs_pedido(order_id: str, logs_adjuntos: str = "") -> str:
    """
    TOOL de lectura. Recupera la telemetría del sistema para un order_id.
    En el MVP: si el ticket ya trae logs, los devuelve; si no, simula que la
    base de telemetría no tiene registros (retorna cadena vacía).
    """
    if logs_adjuntos:
        return logs_adjuntos
    print(f"        [TOOL] consultar_logs_pedido(order_id={order_id}) -> sin registros en telemetría")
    return ""


def buscar_tickets_abiertos(order_id: str, ticket_id: str) -> str:
    """
    TOOL de negocio. Verifica si ya existe un ticket abierto para ese order_id.
    Retorna el ticket_id original si es duplicado, o "" si es nuevo.
    """
    if not order_id:
        return ""
    original = _TICKETS_ABIERTOS.get(order_id)
    if original and original != ticket_id:
        print(f"        [TOOL] buscar_tickets_abiertos(order_id={order_id}) -> DUPLICADO de {original}")
        return original
    # Registrar este order_id como caso abierto.
    _TICKETS_ABIERTOS.setdefault(order_id, ticket_id)
    return ""


def merge_tickets(ticket_id: str, ticket_original: str) -> None:
    """TOOL de negocio. Fusiona el ticket nuevo con el caso original abierto."""
    print(f"        [TOOL] merge_tickets({ticket_id} -> {ticket_original})")


def crear_incidencia_jira(ticket_id: str, order_id: str, logs: str) -> str:
    """
    TOOL de integración. Crea una incidencia en el backlog de Ingeniería (Jira)
    adjuntando order_id, logs y stacktrace. Retorna un id de incidencia simulado.
    """
    jira_id = f"BUG-{ticket_id.split('-')[-1]}"
    print(f"        [TOOL] crear_incidencia_jira({jira_id}) order={order_id}")
    return jira_id


def enviar_resolucion_automatica(ticket_id: str, mensaje: str) -> None:
    """
    TOOL de comunicación. Envía la respuesta al canal de origen y cierra el caso.
    Se usa para Errores de Configuración (Capa 8) y resoluciones de Capa 1.
    """
    print(f"        [TOOL] enviar_resolucion_automatica({ticket_id}) -> caso cerrado")


def escalar_a_soporte_humano(ticket_id: str, cola: str) -> None:
    """
    TOOL de enrutamiento. Cambia el estado del ticket en el CRM y lo reasigna
    a la cola humana correspondiente (Operaciones / Servicio al Cliente).
    """
    print(f"        [TOOL] escalar_a_soporte_humano({ticket_id}) -> cola '{cola}'")


# ============================================================================
# REGLAS DE CLASIFICACIÓN (System Prompt del Agente)
# Estas son mis reglas, no las del modelo. El LLM solo las aplica.
# ============================================================================

SYSTEM_PROMPT = """
Eres un agente de diagnóstico de soporte técnico para una app de delivery (FoodDash).
Tu trabajo es determinar la CAUSA RAÍZ de un ticket cruzando la queja del usuario
contra la telemetría real de los logs del sistema.

PRINCIPIO RECTOR: El log del sistema es la FUENTE DE VERDAD. Si la queja del usuario
contradice al log, prevalece el log.

Debes clasificar el ticket en EXACTAMENTE una de estas 3 categorías:

1. "Bug"
   - El código o la infraestructura FALLÓ de forma inesperada.
   - Señales en logs: stacktrace, NullPointerException, js_error, crash,
     timeout, errores HTTP 500/5xx, o fallas transaccionales graves
     (ej. cobro duplicado / reuso de idempotency_key).
   - Regla: si el software se rompió, es Bug.

2. "Configuracion"
   - El sistema funcionó correctamente y bloqueó o denegó una acción por una
     regla de negocio válida, o el usuario configuró algo mal.
   - Señales en logs: estados BLOCKED / REJECTED con motivo claro
     (ej. below_min_order, expired, cancelacion fuera de plazo),
     published=FALSE, draft_state=UNPUBLISHED, notificaciones en OFF.
   - Regla: si el bloqueo es el comportamiento ESPERADO por política, es Configuracion.

3. "Operacion"
   - El software NO falló, pero la logística/operación en terreno no funcionó.
   - Señales en logs: anomalías de GPS (distancia alta al marcar entrega),
     baja confianza de geocoding, tiempo real de entrega muy superior al
     prometido, pocos repartidores activos vs pedidos abiertos.
   - Regla: si el problema es físico/operativo y no de código, es Operacion.

FORMATO DE RESPUESTA OBLIGATORIO:
Responde ÚNICA y EXCLUSIVAMENTE con un objeto JSON válido, sin texto adicional,
sin markdown, sin ```json. El objeto debe tener EXACTAMENTE estas dos llaves:
{
  "clasificacion": "Bug" | "Configuracion" | "Operacion",
  "razon": "explicación breve de máximo 15 palabras basada en la regla detectada"
}
"""


# ============================================================================
# CAPA 1 · FILTRO DETERMINISTA (Python puro)
# ----------------------------------------------------------------------------
# Antes de gastar una llamada al LLM se resuelven, con reglas baratas, los
# casos de borde del árbol de decisiones: spam/ruido, duplicados y falta de
# información. Solo lo que sobrevive a este filtro llega a la Capa 2.
# ============================================================================

def campo_vacio(valor) -> bool:
    """Devuelve True si el campo es NaN, None o cadena vacía/espacios."""
    if valor is None:
        return True
    if isinstance(valor, float) and pd.isna(valor):
        return True
    if pd.isna(valor):
        return True
    if isinstance(valor, str) and valor.strip() == "":
        return True
    return False


def es_spam(ticket: dict) -> bool:
    """
    Detección determinista de ruido/spam: texto de prueba o sin sentido,
    sin logs asociados. Ej: 'asdkjh test test'.
    """
    if not campo_vacio(ticket.get("system_logs")):
        return False  # si hay telemetría, no lo tratamos como ruido

    subject = "" if campo_vacio(ticket.get("subject")) else str(ticket["subject"]).lower()
    body = "" if campo_vacio(ticket.get("body")) else str(ticket["body"]).lower()
    texto = f"{subject} {body}".strip()

    if len(texto) < 6:
        return True

    # Palabras clave típicas de pruebas/ruido.
    patrones_ruido = r"\b(test|prueba|asdf|asdkjh|ignorar|qwerty|lorem ipsum)\b"
    hits = len(re.findall(patrones_ruido, texto))
    # Consideramos spam si el texto es corto y está dominado por ruido.
    if hits >= 2 or (hits >= 1 and len(texto) < 25):
        return True
    return False


def capa1_filtro(ticket: dict) -> dict:
    """
    Ejecuta las reglas deterministas de la Capa 1 en orden de prioridad.

    Retorna:
      - {"resuelto": True, "clasificacion": ..., "razon": ..., "extra": {...}}
        si el ticket se resolvió aquí (spam, duplicado o falta de info).
      - {"resuelto": False, "logs": <logs efectivos>} si debe pasar a Capa 2.
    """
    ticket_id = ticket.get("ticket_id", "")
    order_id = None if campo_vacio(ticket.get("order_id")) else str(ticket["order_id"])
    logs = "" if campo_vacio(ticket.get("system_logs")) else str(ticket["system_logs"])

    # 1) Spam / ruido -> cerrar sin respuesta al usuario.
    if es_spam(ticket):
        return {"resuelto": True, "clasificacion": "Spam",
                "razon": "Texto de prueba o sin sentido, sin logs asociados.",
                "extra": {}}

    # 2) Duplicado -> merge con el caso original abierto.
    original = buscar_tickets_abiertos(order_id, ticket_id) if order_id else ""
    if original:
        return {"resuelto": True, "clasificacion": "Duplicado",
                "razon": f"Reclamo en curso para {order_id} (ticket {original}).",
                "extra": {"ticket_original": original}}

    # 3) Sin telemetría adjunta -> intentar recuperarla con la tool de logs.
    if not logs and order_id:
        logs = consultar_logs_pedido(order_id, logs_adjuntos="")

    # 4) Falta de información -> sin order_id Y sin logs, imposible diagnosticar.
    if not order_id and not logs:
        return {"resuelto": True, "clasificacion": "Falta de Informacion",
                "razon": "Sin order_id y sin system_logs: imposible diagnosticar.",
                "extra": {}}

    # Pasa a Capa 2 con los logs efectivos (adjuntos o recuperados por la tool).
    return {"resuelto": False, "logs": logs}


# ============================================================================
# CAPA 2 · DIAGNÓSTICO CON LLM (Gemini)
# ============================================================================

def _limpiar_json(texto: str) -> str:
    """
    Limpieza estricta: el LLM a veces envuelve el JSON en Markdown (```json ...```)
    o agrega texto basura antes/después. Extraemos únicamente lo que está entre
    la primera '{' y la última '}' usando regex, para que json.loads() no falle.
    """
    if texto is None:
        return ""
    m = re.search(r"\{.*\}", texto, re.DOTALL)
    if m:
        return m.group(0).strip()
    return texto.strip()


def _parsear_respuesta(texto: str) -> dict:
    """
    Convierte la respuesta cruda del LLM en {'clasificacion', 'razon'}.
    1) Intenta json.loads sobre el bloque {...} extraído por regex.
    2) Si falla (típicamente por comillas sin escapar dentro de 'razon'),
       cae a una extracción por regex campo a campo como último recurso.
    Lanza ValueError si no logra recuperar la clasificación.
    """
    crudo = _limpiar_json(texto)
    try:
        return json.loads(crudo)
    except json.JSONDecodeError:
        clasif_m = re.search(r'"clasificacion"\s*:\s*"([^"]+)"', crudo)
        razon_m = re.search(r'"razon"\s*:\s*"(.+?)"\s*}', crudo, re.DOTALL)
        if clasif_m:
            return {
                "clasificacion": clasif_m.group(1),
                "razon": razon_m.group(1).strip() if razon_m else "",
            }
        raise ValueError("No se pudo extraer la clasificación de la respuesta")


def capa2_diagnostico(ticket: dict, logs: str) -> dict:
    """
    Construye el prompt inyectando subject, body y system_logs de la fila,
    llama al modelo Llama (vía Groq) y devuelve un dict con 'clasificacion' y
    'razon'. Maneja errores de red / parseo devolviendo una clasificación segura.
    """
    subject = "" if campo_vacio(ticket.get("subject")) else str(ticket["subject"])
    body = "" if campo_vacio(ticket.get("body")) else str(ticket["body"])
    logs = logs or ""

    user_prompt = f"""
TICKET A DIAGNOSTICAR:

Asunto: {subject}
Mensaje del usuario: {body}
Logs del sistema: {logs if logs else "(sin logs disponibles)"}

Aplica las reglas y responde solo con el JSON solicitado.
"""

    try:
        respuesta = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        texto = respuesta.choices[0].message.content
        data = _parsear_respuesta(texto)

        clasif = str(data.get("clasificacion", "")).strip().capitalize()
        if clasif not in ("Bug", "Configuracion", "Operacion"):
            clasif = "Revision Manual"

        return {
            "clasificacion": clasif,
            "razon": str(data.get("razon", "")).strip(),
        }

    except (json.JSONDecodeError, ValueError) as e:
        # El modelo respondió algo no parseable.
        return {"clasificacion": "Revision Manual",
                "razon": f"Respuesta del LLM no parseable: {e}"}
    except Exception as e:
        # Error de red / API.
        return {"clasificacion": "Revision Manual",
                "razon": f"Error al llamar al LLM: {str(e)[:120]}"}


# ============================================================================
# CAPA 3 · DECISIÓN Y ACCIÓN (Árbol de decisiones completo, Python puro)
# ----------------------------------------------------------------------------
# Mapea la clasificación a: severidad, acción, respuesta al usuario y la TOOL
# concreta a invocar. Se implementan TODAS las ramas (capas 1, 2 y de borde).
# ============================================================================

def capa3_decision(ticket: dict, clasificacion: str, logs: str, extra: dict) -> dict:
    """
    Devuelve un dict con: severidad, accion, respuesta_usuario y tool_ejecutada.
    Además invoca (simuladamente) la herramienta correspondiente.
    """
    ticket_id = ticket.get("ticket_id", "")
    order_id = "" if campo_vacio(ticket.get("order_id")) else str(ticket["order_id"])
    extra = extra or {}

    if clasificacion == "Bug":
        # Bug técnico - Prioridad Alta. Escalar a Ingeniería vía Jira.
        jira_id = crear_incidencia_jira(ticket_id, order_id, logs)
        return {
            "severidad": "Alta",
            "accion": f"Escalar a Ingeniería/Soporte. Incidencia {jira_id} creada con order_id, log y stacktrace.",
            "respuesta_usuario": ("Hemos detectado un inconveniente técnico con tu solicitud. "
                                  "Nuestro equipo de ingeniería ya fue notificado y está "
                                  "trabajando en una solución urgente."),
            "tool_ejecutada": f"crear_incidencia_jira -> {jira_id}",
        }

    elif clasificacion == "Operacion":
        # Problema operativo / efectividad - Prioridad Alta. Derivar a humano.
        escalar_a_soporte_humano(ticket_id, cola="Logística/Reembolsos")
        return {
            "severidad": "Alta",
            "accion": "Derivar a cola de Operaciones/Servicio al Cliente. etiquetar_ticket('Logística/Reembolsos').",
            "respuesta_usuario": ("Lamentamos el inconveniente con tu pedido. Hemos derivado tu caso "
                                  "a un especialista de operaciones que te contactará a la brevedad "
                                  "para gestionar una solución."),
            "tool_ejecutada": "escalar_a_soporte_humano -> Logística/Reembolsos",
        }

    elif clasificacion == "Configuracion":
        # Error de configuración / Capa 8 - Prioridad Media-Baja. Auto-resolver.
        mensaje = ("Revisamos tu caso: la plataforma funcionó correctamente. El resultado se debe "
                   "a una configuración o política (por ejemplo cupón expirado, monto mínimo, "
                   "horario o notificaciones). Te indicamos cómo corregirlo y cerramos el ticket.")
        enviar_resolucion_automatica(ticket_id, mensaje)
        return {
            "severidad": "Media-Baja",
            "accion": "Resolución automática. Explicar causa raíz y cerrar el ticket.",
            "respuesta_usuario": mensaje,
            "tool_ejecutada": "enviar_resolucion_automatica -> ticket cerrado",
        }

    elif clasificacion == "Falta de Informacion":
        # Rama de Capa 1 - Bloqueado por falta de datos.
        mensaje = ("Para poder investigar tu caso y darte una solución rápida, necesitamos que nos "
                   "indiques el número de pedido (ORD-XXXX) asociado a este inconveniente.")
        return {
            "severidad": "Baja",
            "accion": "Pedir más info. Suspender clasificación. Estado: pendiente de respuesta del cliente.",
            "respuesta_usuario": mensaje,
            "tool_ejecutada": "ninguna (esperando respuesta del cliente)",
        }

    elif clasificacion == "Duplicado":
        # Rama de Capa 1 - Reiteración. Fusionar con el caso original.
        original = extra.get("ticket_original", "")
        merge_tickets(ticket_id, original)
        return {
            "severidad": "Baja",
            "accion": f"merge_tickets con {original}. Añadir nueva info al caso original y cerrar este ticket.",
            "respuesta_usuario": ("Gracias por escribir. Ya tenemos un caso abierto para este pedido; "
                                  "sumamos tu nueva información y le damos seguimiento allí."),
            "tool_ejecutada": f"merge_tickets -> {original}",
        }

    elif clasificacion == "Spam":
        # Rama de Capa 1 - Ruido. Etiquetar como inválido y cerrar sin respuesta.
        return {
            "severidad": "Nula",
            "accion": "Etiquetar como 'Inválido' y cerrar automáticamente sin respuesta al usuario.",
            "respuesta_usuario": "(sin respuesta)",
            "tool_ejecutada": "etiquetar_ticket('Inválido') + cierre",
        }

    else:  # "Revision Manual" u otros
        # Salvaguarda: cualquier caso no resuelto va a un humano.
        escalar_a_soporte_humano(ticket_id, cola="Triage Manual")
        return {
            "severidad": "Media",
            "accion": "El agente no pudo clasificar con confianza. Derivar a un analista humano para triage.",
            "respuesta_usuario": ("Estamos revisando tu caso con más detalle; un agente te contactará "
                                  "a la brevedad."),
            "tool_ejecutada": "escalar_a_soporte_humano -> Triage Manual",
        }


# ============================================================================
# ORQUESTADOR PRINCIPAL
# ============================================================================

def main():
    print("Cargando tickets desde:", INPUT_JSON)
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    # El dataset entrega los tickets bajo la llave "tickets".
    # Si el archivo fuera una lista plana, se usa tal cual.
    tickets = data["tickets"] if isinstance(data, dict) else data

    # Normalizamos a DataFrame: los campos ausentes en el JSON quedan como NaN,
    # lo que es coherente con el manejo de nulos de las tres capas.
    df = pd.DataFrame(tickets)

    # --- MODO DE EJECUCIÓN: todo el archivo o un solo ticket (test) ---
    print(f"\nDataset con {len(df)} tickets disponibles.")
    seleccion = input(
        "Escribe un ID de ticket para testear solo ese (ej. TCK-1004), "
        "o presiona ENTER para procesar TODO el archivo: "
    ).strip()

    if seleccion:
        df = df[df["ticket_id"] == seleccion]
        if df.empty:
            print(f"⚠ No se encontró el ticket '{seleccion}'. Nada que procesar.")
            return
        print(f"Modo TEST: procesando únicamente {seleccion}\n")
    else:
        print("Modo COMPLETO: procesando todos los tickets\n")

    resultados = []

    for idx, fila in df.iterrows():
        ticket = fila.to_dict()
        ticket_id = ticket.get("ticket_id", f"ROW-{idx}")

        # --- CAPA 1: Filtro determinista (spam / duplicados / falta de info) ---
        c1 = capa1_filtro(ticket)

        if c1["resuelto"]:
            # El ticket se resolvió en Capa 1, no se llama al LLM.
            clasificacion = c1["clasificacion"]
            razon = c1["razon"]
            extra = c1.get("extra", {})
            logs = "" if campo_vacio(ticket.get("system_logs")) else str(ticket["system_logs"])
            print(f"[{ticket_id}] CAPA 1 -> {clasificacion} (sin LLM)")
        else:
            # --- CAPA 2: Diagnóstico con LLM ---
            logs = c1["logs"]
            extra = {}
            print(f"[{ticket_id}] CAPA 2 -> consultando a Llama (Groq)...")
            diagnostico = capa2_diagnostico(ticket, logs)
            clasificacion = diagnostico["clasificacion"]
            razon = diagnostico["razon"]
            print(f"           -> {clasificacion}: {razon}")
            # Estrategia anti rate-limit: máx. 2 llamadas por minuto.
            # Solo esperamos cuando el ticket realmente llamó al LLM.
            time.sleep(SLEEP_BETWEEN_CALLS)

        # --- CAPA 3: Decisión y acción (severidad + tool + respuesta) ---
        decision = capa3_decision(ticket, clasificacion, logs, extra)

        resultados.append({
            "ticket_id": ticket_id,
            "clasificacion": clasificacion,
            "severidad": decision["severidad"],
            "razon": razon,
            "accion": decision["accion"],
            "respuesta_usuario": decision["respuesta_usuario"],
            "tool_ejecutada": decision["tool_ejecutada"],
        })

    # --- Exportar resultado ---
    columnas = ["ticket_id", "clasificacion", "severidad", "razon",
                "accion", "respuesta_usuario", "tool_ejecutada"]
    df_out = pd.DataFrame(resultados, columns=columnas)
    df_out.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print("\n============================================================")
    print(f"✔ Proceso completado. {len(df_out)} tickets clasificados.")
    print(f"✔ Archivo generado: {os.path.abspath(OUTPUT_CSV)}")
    print("============================================================")
    print("\nResumen por categoría:")
    print(df_out["clasificacion"].value_counts().to_string())


if __name__ == "__main__":
    main()
