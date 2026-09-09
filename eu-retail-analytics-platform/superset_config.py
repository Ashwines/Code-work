import os

ROW_LIMIT = 5000
SECRET_KEY = os.getenv("SUPERSET_SECRET_KEY", "super_secret_retail_key_change_in_prod")

# Point to PostgreSQL
SQLALCHEMY_DATABASE_URI = os.getenv(
    "SQLALCHEMY_DATABASE_URI",
    "postgresql+psycopg2://retail:retail@postgres:5432/superset_metadata"
)

# Redis Cache
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")

CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_KEY_PREFIX": "superset_",
    "CACHE_REDIS_HOST": REDIS_HOST,
    "CACHE_REDIS_PORT": REDIS_PORT,
}
DATA_CACHE_CONFIG = CACHE_CONFIG

# Local dev settings
WTF_CSRF_ENABLED = True
TALISMAN_ENABLED = False