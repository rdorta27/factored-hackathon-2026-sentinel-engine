"""
src/config.py

Módulo central de configuración del sistema Sentinel Engine usando Pydantic Settings.
"""

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Ruta raíz del proyecto (2 niveles arriba de src/config.py)
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Entorno y Logging
    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    
    # AWS S3 Data Bucket (Dataset Oficial LATAM Bank)
    # Se dejan vacíos por defecto para NO exponer credenciales en el repositorio de Git
    aws_access_key_id: str = Field(default="", alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="", alias="AWS_SECRET_ACCESS_KEY")
    aws_default_region: str = Field(default="us-east-2", alias="AWS_DEFAULT_REGION")
    s3_bucket_name: str = Field(
        default="",
        alias="S3_BUCKET_NAME"
    )

    # Rutas de Almacenamiento Local (RAW y Delta Lake)
    data_raw_path: Path = Field(default=BASE_DIR / "data" / "raw", alias="DATA_RAW_PATH")
    data_delta_path: Path = Field(default=BASE_DIR / "data" / "delta", alias="DATA_DELTA_PATH")

    # Azure OpenAI Endpoints (Inferencia y Razonamiento)
    azure_openai_endpoint: str = Field(default="", alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str = Field(default="", alias="AZURE_OPENAI_API_KEY")
    azure_openai_deployment_name: str = Field(default="gpt-4o", alias="AZURE_OPENAI_DEPLOYMENT_NAME")
    azure_openai_api_version: str = Field(default="2024-02-15-preview", alias="AZURE_OPENAI_API_VERSION")

    # Databricks Mosaic AI (Model Serving - Llama 3)
    databricks_host: str = Field(default="", alias="DATABRICKS_HOST")
    databricks_token: str = Field(default="", alias="DATABRICKS_TOKEN")
    databricks_llama_endpoint: str = Field(default="sentinel-llama-3-8b-instruct", alias="DATABRICKS_LLAMA_ENDPOINT")

    # Reglas Financieras Deterministas
    max_auto_reimbursement_usd: float = 150.0  # Umbral máximo para aprobación directa


settings = Settings()