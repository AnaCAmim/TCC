"""Acesso ao PostgreSQL/PostGIS do WebSIG (container Docker), só com a biblioteca padrão do Python.
Configuração por variáveis de ambiente: WEBSIG_CONTAINER (padrão: pgtcc) e WEBSIG_BANCO (padrão: websig)."""
import csv
import io
import os
import pathlib
import subprocess

RAIZ = pathlib.Path(__file__).resolve().parents[1]
CONTAINER = os.environ.get("WEBSIG_CONTAINER", "pgtcc")
BANCO = os.environ.get("WEBSIG_BANCO", "websig")

# Totais validados contra o TABNET e o Censo 2022: qualquer divergência para o processo
TOTAL_CASOS = 10344
TOTAL_MUNICIPIOS = 223
TOTAL_MULHERES = 2055832
ANOS = [2019, 2020, 2021, 2022, 2023, 2024]
TIPOS = ["total", "fisica", "psicologica", "sexual"]


class Falha(Exception):
    """Conferência que não bateu."""


def consulta(sql):
    """Executa um SELECT no banco e devolve uma lista de dicionários (via COPY ... TO STDOUT CSV)."""
    cmd = ["docker", "exec", CONTAINER, "psql", "-h", "127.0.0.1", "-U", "postgres", "-d", BANCO,
           "-v", "ON_ERROR_STOP=1", "-q", "-c", f"COPY ({sql}) TO STDOUT WITH CSV HEADER"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise Falha("consulta ao banco falhou: " + r.stderr.decode("utf-8", "replace").strip())
    return list(csv.DictReader(io.StringIO(r.stdout.decode("utf-8"))))


def confere(cond, msg):
    if not cond:
        raise Falha(msg)
