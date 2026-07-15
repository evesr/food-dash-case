
En este proyecto, utilicé la Inteligencia Artificial estrictamente como un copiloto de desarrollo y redactor técnico, manteniendo en todo momento el control arquitectónico y la toma de decisiones de negocio.

### Herramientas Utilizadas

1. **Gemini:** Lo utilicé como *sparring* analítico. Le planteé mis ideas de arquitectura y criterios de negocio para recibir retroalimentación técnica y refinar la redacción de los documentos formales (Entregables 1, 2, 3, 4, 5 y 6).
2. **Asistente de Código (Copilot / IA Generativa):** Lo utilicé como motor de generación de código para escribir el script de Python (Entregable 7) bajo instrucciones muy restrictivas.

### Prompts Clave Utilizados (Estrategia Secuencial)

Para evitar que la IA alucinara o inventara flujos, utilicé la técnica de "Prompting de Contexto Base":

1. **Contexto Obligatorio:** *"Actúa como un AI Solutions Expert... Tu única tarea en este paso es leer, estudiar y comprender a profundidad la arquitectura, las reglas de negocio, el árbol de decisiones y los criterios de clasificación que definí. NO generes ningún archivo, script o código. Responde únicamente: Contexto asimilado."*
2. **Generación Restringida:** *"Ahora que comprendes mi criterio, escribe el script de Python. Implementa estrictamente esta arquitectura de 3 capas... La Capa 1 debe ser un filtro en Python puro sin IA... Obliga al modelo a responder ESTRICTAMENTE con un objeto JSON... Parsea el JSON y mapea la decisión."*
3. **Refinamiento de Estabilidad:** *"El código base funciona, pero necesito que implementes mejoras críticas: 1) Limpieza estricta del JSON usando Regex `re.search(r'\{.*\}', texto, re.DOTALL)` para evitar fallos de parseo. 2) Modo de Test interactivo para procesar un solo ticket."*

### En qué se equivocó la IA y qué corregí yo

* **Problema de Parseo (Formato Basura):** El LLM inicialmente devolvía el JSON envuelto en bloques de Markdown (`json ... `) o incluía texto extra, lo que rompía la función `json.loads()` nativa de Python.
* **Mi corrección:** Intervine el código para forzar una limpieza del string con Expresiones Regulares (`Regex`) antes del parseo, creando un mecanismo tolerante a fallos que extrajera únicamente el contenido entre las llaves.


* **Falta de previsión de cuotas (Error HTTP 429):** Inicialmente, el prototipo utilizaba la API de Gemini. Sin embargo, la herramienta no previó que procesar el lote completo agotaría rápidamente la cuota diaria del nivel gratuito, provocando errores en cadena. La IA sugirió parches ineficientes como pausar la ejecución por minutos enteros.
* **Mi corrección:** Descarté las sugerencias de la IA y tomé la decisión arquitectónica de migrar el sistema a la API de Groq usando el modelo Llama 3.1 8B. Esto eliminó el bloqueo de cuota, redujo el tiempo de ejecución de minutos a segundos y mantuvo el costo del MVP en cero.


### Decisiones 100% Mías (Diseño, Negocio y Arquitectura)

* **El diseño del Árbol de Decisiones y Enrutamiento:** Toda la lógica de hacia dónde viaja cada problema fue mi creación. Yo definí que los Bugs Técnicos deben escalar directo a Jira (Ingeniería), puenteando al Nivel 1 para ahorrar tiempo, y que los problemas operativos (Logística) requieren atención humana en una cola específica.
* **La creación de los Criterios de Clasificación (El "Cerebro" del agente):** La IA no inventó las categorías. Fui yo quien analizó los logs del caso para estructurar los tres pilares de diagnóstico: Bug Técnico (excepciones de código), Error de Configuración/Capa 8 (bloqueos válidos por reglas de negocio) y Problemas de Operación (anomalías físicas o de GPS).
* **Identificación y Manejo de Casos Borde (Resiliencia):** Anticipé que el flujo fallaría en escenarios del mundo real y diseñé la lógica para contenerlos. Fui yo quien decidió cómo manejar *inputs* impredecibles de los usuarios (creando las ramas para spam, duplicados y falta de información) y cómo mitigar los *outputs* inestables del LLM (forzando la limpieza estricta del JSON mediante Regex).
* **Jerarquía de la información:** Definí la regla fundamental del *System Prompt*: el log siempre invalida la percepción del cliente. La IA tiene estrictamente prohibido creerle al usuario si el log demuestra que el sistema actuó según lo esperado.
* **Arquitectura de Deflexión Temprana (Capa 1):** Diseñé el filtro determinista en Python explícitamente para proteger el presupuesto operativo. Al atrapar y resolver los casos borde antes de llamar a la API, evito que peticiones basura consuman tokens y tiempo de inferencia del LLM.
* **Simulación de Acciones (Mocking):** Decidí que el agente no ejecutara acciones reales (como mandar correos o alterar Jira). Darle permisos de escritura a un LLM en un MVP de prueba es un riesgo innecesario. Preferí simular las respuestas por consola para mostrar que la lógica de decisión funciona de forma segura.
* **Uso de JSON en lugar de CSV:** Decidí que el script consumiera los tickets desde un archivo .json en vez del .csv original, dado que visualmente es mucho más limpio y ordenado, pero además facilita el manejo de campos vacíos dentro del código.
* **Selección de Infraestructura Desacoplada:** La elección final de usar Groq con Llama 3.1 e inyectar una API Key temporal fue una decisión estratégica para garantizar que ustedes pudieran ejecutar el código de inmediato a costo cero, sin fricciones ni vulnerabilidad de credenciales permanentes.

