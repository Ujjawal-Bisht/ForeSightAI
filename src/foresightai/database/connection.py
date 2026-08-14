import environ
import psycopg2

from foresightai.config.configuration import env


def get_postgres_connection():
    """
    Create and return a PostgreSQL database connection.
    """

    return psycopg2.connect(
        host=env("DB_HOST"),
        port=env.int("DB_PORT"),
        dbname=env("DB_NAME"),
        user=env("DB_USER"),
        password=env("DB_PASSWORD"),
    )