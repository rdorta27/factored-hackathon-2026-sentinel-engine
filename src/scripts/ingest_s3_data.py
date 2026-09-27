"""
scripts/ingest_s3_data.py

Script de ingesta para el proyecto Sentinel Engine.
Descarga los archivos del LATAM Bank Dataset desde el bucket S3 oficial
hacia el directorio local `data/raw/` sin duplicar descargas existentes.
"""

import sys
import logging
from pathlib import Path
import boto3
from botocore import UNSIGNED
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

# Añadir directorio raíz al PATH de Python para importar módulos internos
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.config import settings

# Configuración de Logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def setup_local_directories():
    """Crea los directorios locales de almacenamiento si no existen."""
    settings.data_raw_path.mkdir(parents=True, exist_ok=True)
    settings.data_delta_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Directorio RAW verificado: {settings.data_raw_path.resolve()}")
    logger.info(f"Directorio DELTA verificado: {settings.data_delta_path.resolve()}")


def get_s3_client():
    """
    Inicializa el cliente S3 de Boto3.
    Permite autenticación mediante credenciales explícitas del documento de la Hackathon
    o en modo anónimo (UNSIGNED) si las variables de entorno están vacías.
    """
    try:
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            logger.info("Credenciales detectadas: Conectando a S3 con llaves de AWS configuradas.")
            return boto3.client(
                "s3",
                region_name=settings.aws_default_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key
            )
        else:
            logger.info("Variables de AWS vacías: Conectando a S3 en modo público/anónimo (UNSIGNED).")
            return boto3.client(
                "s3",
                region_name=settings.aws_default_region,
                config=Config(signature_version=UNSIGNED)
            )
    except Exception as e:
        logger.error(f"Error al inicializar el cliente de S3: {e}")
        raise

def download_dataset_from_s3():
    """
    Lista y descarga todos los archivos de datos presentes en la carpeta 'data/' del S3.
    Evita descargas duplicadas si el archivo local ya existe y tiene el mismo tamaño.
    """
    setup_local_directories()
    s3_client = get_s3_client()
    bucket_name = settings.s3_bucket_name
    s3_prefix = "data/"

    logger.info(f"Conectando a S3 Bucket: '{bucket_name}' (Región: {settings.aws_default_region})")

    try:
        paginator = s3_client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=s3_prefix)

        downloaded_count = 0
        skipped_count = 0

        for page in page_iterator:
            if "Contents" not in page:
                logger.warning(f"No se encontraron objetos bajo el prefijo '{s3_prefix}' en el bucket.")
                continue

            for obj in page["Contents"]:
                key = obj["Key"]
                size_bytes = obj["Size"]

                # Omitir la propia carpeta 'data/'
                if key == s3_prefix or key.endswith("/"):
                    continue

                filename = Path(key).name
                local_file_path = settings.data_raw_path / filename

                # Control de duplicados por existencia y tamaño de archivo
                if local_file_path.exists() and local_file_path.stat().st_size == size_bytes:
                    logger.debug(f"Saltando '{filename}' (ya existe localmente y coincide en tamaño).")
                    skipped_count += 1
                    continue

                logger.info(f"Descargando: '{key}' ({size_bytes / (1024 * 1024):.2f} MB) -> {local_file_path}")
                
                s3_client.download_file(
                    Bucket=bucket_name,
                    Key=key,
                    Filename=str(local_file_path)
                )
                downloaded_count += 1

        logger.info("=" * 60)
        logger.info(f"Resumen de Ingesta: {downloaded_count} descargados, {skipped_count} omitidos.")
        logger.info(f"Todos los archivos RAW disponibles en: {settings.data_raw_path.resolve()}")
        logger.info("=" * 60)

    except ClientError as ce:
        error_code = ce.response.get("Error", {}).get("Code")
        logger.error(f"Error de cliente S3 ({error_code}): {ce}")
        sys.exit(1)
    except BotoCoreError as bce:
        logger.error(f"Error de red/conexión con AWS Botocore: {bce}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error inesperado durante la descarga: {e}")
        sys.exit(1)


if __name__ == "__main__":
    download_dataset_from_s3()