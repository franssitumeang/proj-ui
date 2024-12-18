import polars as pl
import pandas as pd

from sqlalchemy import create_engine
from urllib.parse import quote
from dotenv import load_dotenv
import os
import sqlite3

load_dotenv()

# Define a mapping between Polars data types and PostgreSQL data types
polars_to_postgres = {
    pl.Int64: "INTEGER",
    pl.Int32: "INTEGER",
    pl.Int16: "SMALLINT",
    pl.Float64: "DOUBLE PRECISION",
    pl.Float32: "REAL",
    pl.Utf8: "TEXT",
    pl.Boolean: "BOOLEAN",
    pl.Date: "DATE",
    pl.Datetime: "TIMESTAMP",
    pl.Time: "TIME",
    pl.String: "VARCHAR(500)"
}

# Function to generate the CREATE TABLE DDL statement
def generate_postgres_ddl(df: pl.DataFrame, table_name: str) -> str:
    columns = []
    for name, dtype in zip(df.columns, df.dtypes):
        postgres_type = polars_to_postgres.get(dtype, "TEXT")  # Default to TEXT if type not found
        columns.append(f'"{name}" {postgres_type}')
    
    ddl = f"CREATE TABLE {table_name} (\n  " + ",\n  ".join(columns) + "\n);"
    return ddl

# MASTER_DB POSTGRES
MASTER_DB_HOST=os.getenv("MASTER_DB_HOST")
MASTER_DB_USER=os.getenv("MASTER_DB_USER")
MASTER_DB_PASS=os.getenv("MASTER_DB_PASS")
MASTER_DB_NAME=os.getenv("MASTER_DB_NAME")

engine = create_engine(f"postgresql://{MASTER_DB_USER}:{quote(MASTER_DB_PASS)}@{MASTER_DB_HOST}/{MASTER_DB_NAME}")

def df_to_db(df: pl.DataFrame, table_name: str):
    pd_df = df.to_pandas()
    pd_df.to_sql(table_name, con=engine, if_exists='append', index=False)
    
def read_database(engine, query):
    df = pd.read_sql(query, con=engine)
    return df
