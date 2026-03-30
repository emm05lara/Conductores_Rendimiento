# Dashboard: Rendimiento de Conductores 📊🚗

Un dashboard interactivo y robusto desarrollado en Python usando Dash y Plotly para la visualización del rendimiento de los conductores a lo largo del tiempo, con capacidades de lectura desde un archivo de Excel (`.xlsx`).

## Descripción
Este proyecto procesa datos históricos de ganancias y metas por cada conductor, proporcionando resúmenes matemáticos, barras interactivas con el cumplimiento de objetivos y un cajón de comentarios por evento/período.

## Tecnologías Principales
- **Python 3.10+**
- **Dash / Dash Bootstrap Components**: Para la creación de la interfaz de usuario.
- **Plotly**: Para las gráficas dinámicas y dinámicamente acotadas.
- **Pandas & OpenPyXL**: Para la lectura y manipulación de `.xlsx`.
- **Gunicorn**: Como servidor WSGI en producción (Render).

---

## 📂 Estructura del Proyecto

```text
mi-proyecto/
│
├── app.py               # Orquestación de app, callbacks e inicio del servidor.
├── data_loader.py       # Lectura de la carpeta data/ y preparación de las variables globales.
├── logic.py             # Funciones matemáticas para cálculos y KPIs.
├── visualization.py     # Creación de tablas, gráficas de barra invertidas y UI.
├── requirements.txt     # Dependencias necesarias para este dashboard en Python.
├── render.yaml          # Blueprint de automatización de deploys en render.com.
├── .gitignore           # Archivos omitidos de control de de versiones.
├── README.md            # Documentación.
│
└── data/
    └── CONDUCTORES 1-11.xlsx  # TUS DATOS: El archivo Excel que el sistema escanea.
```

---

## 🛠️ Cómo Ejecutar Localmente

1. **Clona o descarga este repositorio** a tu computadora.
2. **Crea un entorno virtual (opcional pero recomendado):**
   ```bash
   python -m venv venv
   # En Windows: .\venv\Scripts\activate
   # En Mac/Linux: source venv/bin/activate
   ```
3. **Instala las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Ejecuta la app:**
   ```bash
   python app.py
   ```
5. Accede en el navegador a: `http://localhost:8050`

---

## 📝 Subir / Actualizar Datos en el Excel

La aplicación extrae **únicamente** la data del archivo Excel que vive en el directorio `data/`.
Para actualizar la información a mostrar sin tocar código, simplemente reemplázalo:

1. Modifica o sobrescribe el archivo: `data/CONDUCTORES 1-11.xlsx` 
2. Haz `git add data/`, `git commit`, y `git push...` hacia tu GitHub ligado a Render.
3. Asegúrate de que el archivo base se llame siempre `CONDUCTORES 1-11.xlsx`.

> **NOTAS IMPORTANTES DEL ARCHIVO**:
> - La hoja a leer obligatoriamente debe llamarse: `BASE DATOS`
> - Se esperan de manera estricta las columnas `CONDUCTOR`, `GANANCIAS TOTALES`, `META` y `COMENTARIO`.

---

## 🚀 Cómo Desplegar en Render (Automático)

Como el repositorio ya incluye el archivo `render.yaml` y la inyección por `gunicorn`, el deploy es muy sencillo:

1. Sube este repositorio completo a GitHub.
2. En [Render.com](https://render.com/), crea un **Blueprint** y pégale el repositorio, o bien, crea un **Web Service**.
3. El `render.yaml` orquestará lo demás:
   - **Build Command**: `pip install --upgrade pip setuptools wheel && pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:server`
   - Instalará dependencias y tomará el entorno Python correctos automáticamente.
4. Cada vez que modifiques el Excel, Render redesplegará tu sitio para lucir la data nueva.
