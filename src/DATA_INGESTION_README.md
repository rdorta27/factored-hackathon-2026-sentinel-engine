Guía de Ingesta y Descarga de Datos — Sentinel Engine

Este documento describe los pasos necesarios para configurar el entorno local y ejecutar el script de descarga automatizada de datos desde el bucket oficial de Amazon S3 del Factored AI & Data Hackathon 2026.

📌 Datos de Origen (AWS S3)

Bucket: TU_BUCKET_DEL_DOC

Región: us-east-2

Directorio de origen S3: data/

Directorio de destino local: data/raw/

📋 Requisitos Previos

Python 3.10+ instalado.

Entorno virtual activo (.venv).

Dependencias de Python instaladas: boto3, pydantic-settings, python-dotenv.

🚀 Paso a Paso para la Configuración y Ejecución Local

1. Activar el Entorno Virtual e Instalar Dependencias

Asegúrate de estar en la raíz del repositorio y tener el entorno virtual activo:

# Activar en Linux/macOS:
source .venv/bin/activate

# Activar en Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

# Instalar dependencias requeridas
pip install boto3 pydantic-settings python-dotenv


2. Configurar el Archivo de Variables de Entorno (.env)

⚠️ IMPORTANTE: Para listar y descargar los datos desde el bucket de S3 es obligatorio contar con las credenciales de autenticación. No se pueden dejar las variables vacías, ya que la operación ListObjectsV2 de S3 requiere autenticación válida.

Crea un archivo llamado .env ubicado en la raíz del repositorio (al mismo nivel que README.md y fuera de la carpeta src/) con las credenciales oficiales provistas en la documentación del Hackathon:

# Configuración AWS S3 (Credenciales requeridas del documento oficial del Hackathon)
AWS_ACCESS_KEY_ID=TU_AWS_ACCESS_KEY_DEL_DOC
AWS_SECRET_ACCESS_KEY=TU_AWS_SECRET_KEY_DEL_DOC
AWS_DEFAULT_REGION=us-east-2
S3_BUCKET_NAME=TU_BUCKET_DEL_DOC

# Rutas de Almacenamiento Local
DATA_RAW_PATH=data/raw
DATA_DELTA_PATH=data/delta


Nota: El archivo .env está ignorado por .gitignore, por lo que tus credenciales locales nunca se subirán al repositorio de Git.

3. Ejecutar la Ingesta en Local

Ejecuta el script de ingesta desde la raíz del proyecto usando el módulo de Python:

python -m src.scripts.ingest_s3_data


⚙️ ¿Qué hace el Script de Ingesta?

Verificación de Directorios: Crea automáticamente las carpetas data/raw/ y data/delta/ en local si aún no existen.

Autenticación con S3: Carga las credenciales del .env mediante pydantic-settings y se conecta de forma segura a AWS.

Descarga Inteligente de Archivos: Lista el contenido de data/ en S3 y descarga los archivos hacia data/raw/.

Control de Duplicados: Si un archivo ya existe localmente y su tamaño coincide exactamente con el objeto en S3, se omite para evitar descargas redundantes.

Manejo de Excepciones: Captura errores de red y credenciales con logs detallados.

🔍 Verificación de Descarga

Al finalizar, puedes verificar que los archivos estén presentes ejecutando:

# En Windows (PowerShell)
Get-ChildItem data/raw/

# En Linux / macOS
ls -lh data/raw/



