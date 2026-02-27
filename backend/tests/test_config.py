"""
Tests for configuration module.
"""

import pytest

from app.config import Settings


class TestSettings:
    def test_default_settings(self):
        s = Settings(
            POSTGRES_HOST="localhost",
            POSTGRES_PORT=5433,
            POSTGRES_DB="test_db",
            POSTGRES_USER="user",
            POSTGRES_PASSWORD="pass",
        )
        assert s.APP_ENV == "development"
        assert s.APP_DEBUG is True
        assert s.APP_NAME == "predictive-maintenance"

    def test_database_url_async(self):
        s = Settings(
            POSTGRES_HOST="localhost",
            POSTGRES_PORT=5433,
            POSTGRES_DB="mydb",
            POSTGRES_USER="myuser",
            POSTGRES_PASSWORD="mypass",
        )
        url = s.DATABASE_URL
        assert "asyncpg" in url
        assert "mydb" in url
        assert "myuser" in url

    def test_database_url_sync(self):
        s = Settings(
            POSTGRES_HOST="localhost",
            POSTGRES_PORT=5433,
            POSTGRES_DB="mydb",
            POSTGRES_USER="myuser",
            POSTGRES_PASSWORD="mypass",
        )
        url = s.DATABASE_URL_SYNC
        assert "psycopg2" in url
        assert "mydb" in url

    def test_redis_url(self):
        s = Settings(
            POSTGRES_HOST="localhost",
            POSTGRES_PORT=5433,
            POSTGRES_DB="test_db",
            POSTGRES_USER="user",
            POSTGRES_PASSWORD="pass",
            REDIS_HOST="redis-server",
            REDIS_PORT=6380,
        )
        url = s.REDIS_URL
        assert "redis-server" in url
        assert "6380" in url

    def test_cors_origins_list(self):
        s = Settings(
            POSTGRES_HOST="localhost",
            POSTGRES_PORT=5433,
            POSTGRES_DB="test_db",
            POSTGRES_USER="user",
            POSTGRES_PASSWORD="pass",
        )
        assert isinstance(s.CORS_ORIGINS, list)
        assert len(s.CORS_ORIGINS) > 0

    def test_jwt_settings(self):
        s = Settings(
            POSTGRES_HOST="localhost",
            POSTGRES_PORT=5433,
            POSTGRES_DB="test_db",
            POSTGRES_USER="user",
            POSTGRES_PASSWORD="pass",
            JWT_SECRET_KEY="my-super-secret",
            JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60,
        )
        assert s.JWT_SECRET_KEY == "my-super-secret"
        assert s.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 60
