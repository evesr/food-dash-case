Para que el agente de triage no sea solo un modelo que clasifica texto, sino un sistema operativo capaz de resolver problemas, se le dota de herramientas específicas. El agente puede invocar de manera autónoma estas herramientas según las necesidades detectadas en el ticket.

A continuación, detallo las herramientas indispensables para este flujo y su justificación técnica:

### 1. Tool de Lectura: consultar_logs_pedido
Qué hace: Permite al agente buscar en la base de datos de telemetría los logs del sistema asociados a un identificador específico (order_id o ticket_id).

Justificación: El agente no puede tomar decisiones basándose únicamente en el texto del usuario. Necesita esta herramienta para extraer la verdad del sistema de forma automática cuando el ticket ingresa sin logs adjuntos o incompletos, permitiendo cruzar la queja con la telemetría real.

### 2. Tool de Negocio: buscar_tickets_abiertos
Qué hace: Realiza una consulta rápida en la base de datos de soporte para verificar si existen tickets activos con el mismo order_id o el identificador del usuario.

Justificación: Es clave para el manejo de duplicados. Antes de procesar o escalar un ticket, el agente debe usar esta herramienta. Si detecta un caso abierto, activa la lógica de fusión (merge) en lugar de crear ruido operativo enviando un segundo ticket a los equipos humanos.

### 3. Tool de Integración: crear_incidencia_jira
Qué hace: Toma la información estructurada del bug (asunto, descripción, logs de error y severidad) y realiza una petición POST a la API de Jira para crear un ticket en el backlog de desarrollo.

Justificación: Automatiza el paso manual más tedioso para soporte. Cuando el agente detecta un Bug Técnico, esta herramienta asegura que la información llegue directamente al equipo de Ingeniería con todo el contexto técnico necesario (como el stacktrace), reduciendo drásticamente el tiempo medio de resolución.

### 4. Tool de Comunicación: enviar_resolucion_automatica
Qué hace: Envía una respuesta predefinida o estructurada por el LLM al canal de origen del ticket (correo, chat, WhatsApp) y marca el caso como resuelto.

Justificación: Es la herramienta principal para lidiar con los Errores de Configuración (Capa 8). Permite al agente resolver y cerrar de inmediato los casos sencillos sin que toquen la bandeja de entrada de un humano, logrando el objetivo de abaratar costos operativos.

### 5. Tool de Enrutamiento: escalar_a_soporte_humano
Qué hace: Cambia el estado del ticket en el CRM de soporte (ej. Zendesk) y lo reasigna a la cola del equipo de Operaciones o Servicio al Cliente.

Justificación: Es el puente indispensable para los Problemas de Operación/Efectividad. Permite que el agente delegue de manera segura aquellos casos donde la IA no tiene atribuciones (como gestionar reembolsos o coordinar con repartidores) asegurando que el cliente reciba atención de una persona de inmediato.