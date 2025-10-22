#!/usr/bin/env python3
import os
from typing import Optional, Tuple
from datetime import date

import psycopg
from psycopg.rows import dict_row


def _dsn_from_env() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    host = os.environ.get("PGHOST", "127.0.0.1")
    port = os.environ.get("PGPORT", "5432")
    user = os.environ.get("PGUSER", "postgres")
    password = os.environ.get("PGPASSWORD", "postgres")
    dbname = os.environ.get("PGDATABASE", "clientes")
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"


def get_db():
    return psycopg.connect(_dsn_from_env(), autocommit=True, row_factory=dict_row)


def init_db():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS clients (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(150) NOT NULL,
                    cpf VARCHAR(10) NOT NULL UNIQUE,
                    data_nascimento DATE NOT NULL,
                    data_cadastro DATE NOT NULL DEFAULT CURRENT_DATE,
                    renda_familiar NUMERIC(14,2)
                );
                """
            )


def fetch_clients(q: str):
    with get_db() as conn, conn.cursor() as cur:
        if q:
            cur.execute(
                "SELECT id, nome, cpf, TO_CHAR(data_nascimento, 'YYYY-MM-DD') AS data_nascimento, TO_CHAR(data_cadastro, 'YYYY-MM-DD') AS data_cadastro, renda_familiar FROM clients WHERE nome ILIKE %s ORDER BY nome ASC",
                (f"%{q}%",),
            )
        else:
            cur.execute(
                "SELECT id, nome, cpf, TO_CHAR(data_nascimento, 'YYYY-MM-DD') AS data_nascimento, TO_CHAR(data_cadastro, 'YYYY-MM-DD') AS data_cadastro, renda_familiar FROM clients ORDER BY nome ASC"
            )
        return [dict(row) for row in cur.fetchall()]


def fetch_client_by_id(cid: int):
    with get_db() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, nome, cpf, TO_CHAR(data_nascimento, 'YYYY-MM-DD') AS data_nascimento, TO_CHAR(data_cadastro, 'YYYY-MM-DD') AS data_cadastro, renda_familiar FROM clients WHERE id = %s",
            (cid,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def insert_client(nome: str, cpf: str, data_nascimento: str, data_cadastro: str, renda_familiar: Optional[float]) -> Tuple[bool, Optional[str]]:
    try:
        with get_db() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO clients (nome, cpf, data_nascimento, data_cadastro, renda_familiar)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (nome, cpf, data_nascimento, data_cadastro, renda_familiar),
            )
        return True, None
    except psycopg.errors.UniqueViolation:
        return False, 'CPF já cadastrado.'


def update_client(cid: int, nome: str, cpf: str, data_nascimento: str, data_cadastro: str, renda_familiar: Optional[float]) -> Tuple[bool, Optional[str]]:
    try:
        with get_db() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE clients
                   SET nome = %s,
                       cpf = %s,
                       data_nascimento = %s,
                       data_cadastro = %s,
                       renda_familiar = %s
                 WHERE id = %s
                """,
                (nome, cpf, data_nascimento, data_cadastro, renda_familiar, cid),
            )
        return True, None
    except psycopg.errors.UniqueViolation:
        return False, 'CPF já cadastrado.'


def delete_client(cid: int):
    with get_db() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM clients WHERE id = %s", (cid,))


def fetch_income_stats(start_date_iso: str):
    with get_db() as conn, conn.cursor() as cur:
        # Average income across all with renda not null
        cur.execute("SELECT AVG(renda_familiar) AS avg_income FROM clients WHERE renda_familiar IS NOT NULL")
        avg_row = cur.fetchone()
        avg_income = avg_row['avg_income'] if avg_row and avg_row['avg_income'] is not None else 0.0

        # Over 18 and income > average, within period (using AGE to compute years)
        cur.execute(
            """
            SELECT COUNT(*) AS qty
              FROM clients
             WHERE data_cadastro >= %s
               AND renda_familiar IS NOT NULL
               AND renda_familiar > %s
               AND EXTRACT(YEAR FROM AGE(CURRENT_DATE, data_nascimento)) >= 18
            """,
            (start_date_iso, avg_income),
        )
        over_18_above_avg = cur.fetchone()['qty']

        # Counts per class within period
        cur.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN renda_familiar <= 980.0 THEN 1 ELSE 0 END), 0) AS class_a,
                COALESCE(SUM(CASE WHEN renda_familiar > 980.0 AND renda_familiar <= 2500.0 THEN 1 ELSE 0 END), 0) AS class_b,
                COALESCE(SUM(CASE WHEN renda_familiar > 2500.0 THEN 1 ELSE 0 END), 0) AS class_c
              FROM clients
             WHERE data_cadastro >= %s AND renda_familiar IS NOT NULL
            """,
            (start_date_iso,),
        )
        row = cur.fetchone()
        return {
            'avg_income': float(avg_income or 0.0),
            'over_18_above_avg': int(over_18_above_avg or 0),
            'class_a': int(row['class_a'] or 0),
            'class_b': int(row['class_b'] or 0),
            'class_c': int(row['class_c'] or 0),
        }
