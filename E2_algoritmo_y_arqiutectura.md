Para abordar este problema optimizando tiempos de respuesta y costos computacionales, la arquitectura se basa en un único Agente Enrutador impulsado por un LLM, apoyado por un pipeline de pre-procesamiento determinista y el uso de herramientas externas.

Se evitó una estructura multi-agente compleja para reducir la latencia y la probabilidad de alucinaciones.

**Diagrama de Flujo de la Arquitectura:**
graph TD
    A([📥 Nuevo Ticket]) --> B[🛡️ CAPA 1: COMPRENSIÓN<br>Extractor Determinista]
    B --> C[Extrae: texto, logs, order_id, user_id]
    
    C --> D{¿Faltan datos<br>clave?}
    D -- Sí --> E[🛑 ACCIÓN: Pedir más info y pausar]
    
    D -- No --> F{¿Es Spam o<br>texto basura?}
    F -- Sí --> G[🗑️ ACCIÓN: Descartar y cerrar ticket]
    
    F -- No --> H[[🔍 TOOL: buscar_tickets_abiertos]]
    H --> I{¿Existe<br>ticket abierto?}
    I -- Sí --> J[🔗 ACCIÓN: merge_tickets y notificar]
    
    I -- No es nuevo --> K[🧠 CAPA 2: DIAGNÓSTICO<br>Agente LLM con Prompt Estricto]
    K --> L[Input: Queja de usuario + Logs]
    L --> M{Lógica LLM:<br>Intención vs Verdad del Log}
    
    M -- "timeout, exception" --> N[🐛 BUG TÉCNICO]
    M -- "anomalías GPS" --> O[🚚 OPERACIÓN / EFECTIVIDAD]
    M -- "bloqueos, expirado" --> P[⚙️ CONFIGURACIÓN / CAPA 8]
    
    N --> Q[⚡ CAPA 3: DECISIÓN Y ACCIÓN<br>Motor de Reglas en Python]
    O --> Q
    P --> Q
    
    Q -- "Si es BUG" --> R[[🛠️ TOOL: crear_ticket_jira<br>Notificar al cliente]]
    Q -- "Si es OPERACIÓN" --> S[[📞 TOOL: enrutar_soporte_humano<br>Notificar]]
    Q -- "Si es CONFIGURACIÓN" --> T[[✉️ TOOL: auto_respuesta_resolutiva<br>Cerrar Ticket]]
    
    style A fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
    style B fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style K fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    style Q fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
Descripción de las Capas y Comunicación: 
El flujo de información se maneja mediante payloads en formato JSON, 
asegurando que la transición entre el sistema de tickets, el agente 
de IA y las herramientas externas sea estructurada.

## Capa 1: Comprensión (Filtro Determinista)
Antes de invocar al modelo de lenguaje, un script recibe el payload del ticket. Su objetivo es normalizar los datos, extraer entidades (como el order_id) y ejecutar validaciones básicas.

**Comunicación:** En esta capa, el sistema se comunica mediante API con la base de datos de soporte (usando la herramienta buscar_tickets_abiertos) para evitar el procesamiento de reclamos duplicados. Si la validación falla (falta información o es un ticket repetido), la ejecución termina aquí, ahorrando recursos.

## Capa 2: Diagnóstico (El Cerebro del Agente)
Si el ticket es válido y nuevo, se construye un prompt estructurado inyectando el texto del usuario y el registro exacto del system_logs.

**Comunicación:** Se realiza una llamada a la API del LLM. El agente no actúa de forma conversacional libre; está restringido por instrucciones de sistema para analizar las variables técnicas del log frente a la queja, y su única salida permitida es retornar un JSON con la clasificación exacta (Bug, Operación, Configuración) y una breve justificación de la causa raíz.

## Capa 3: Decisión y Acción (Orquestación)
El sistema lee el JSON estructurado devuelto por la Capa 2 y, basado en la categoría, acciona el árbol de decisiones.

**Comunicación:** En esta etapa se ejecutan las herramientas de escritura (write tools). El orquestador hace peticiones POST a las plataformas correspondientes: llama a la API de Jira para crear incidencias, a la API del CRM de soporte para cambiar el estado de un ticket y asignarlo a una cola humana, o al motor de correo/mensajería para enviar una resolución automática al cliente.