import os
import time
from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd
import psycopg2
from neo4j import GraphDatabase

# --------------------
# Config from env vars
# --------------------
# etl.py
PG_HOST = os.environ.get("POSTGRES_HOST", "postgres")
PG_PORT = int(os.environ.get("POSTGRES_PORT", "5432"))
PG_DB = os.environ.get("POSTGRES_DB", "shop")
PG_USER = os.environ.get("POSTGRES_USER", "app")
PG_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "appsecret")


NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")

_driver = None  # global Neo4j driver


# ------------- Postgres helpers -------------


def get_pg_conn():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
    )


def wait_for_postgres(timeout: int = 60):
    """
    Waits until Postgres is ready to accept connections.
    """
    print("Waiting for Postgres...")
    start = time.time()
    while True:
        try:
            with get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
            print("Postgres is ready ✅")
            return
        except Exception as exc:  # noqa: BLE001
            if time.time() - start > timeout:
                print("Postgres did not become ready in time ❌")
                raise
            print(f"  Postgres not ready yet: {exc}")
            time.sleep(2)


# ------------- Neo4j helpers -------------


def get_neo4j_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
        )
    return _driver


def wait_for_neo4j(timeout: int = 60):
    """
    Waits until Neo4j is ready to accept Bolt connections.
    """
    print("Waiting for Neo4j...")
    start = time.time()
    driver = get_neo4j_driver()
    while True:
        try:
            with driver.session() as session:
                session.run("RETURN 1").single()
            print("Neo4j is ready ✅")
            return
        except Exception as exc:  # noqa: BLE001
            if time.time() - start > timeout:
                print("Neo4j did not become ready in time ")
                raise
            print(f"  Neo4j not ready yet: {exc}")
            time.sleep(2)


def run_cypher(query: str, params: Dict | None = None):
    """
    Executes a single Cypher query.
    """
    driver = get_neo4j_driver()
    with driver.session() as session:
        return session.run(query, params or {})


def run_cypher_file(path: Path):
    """
    Executes multiple Cypher statements from a file.
    Very simple splitter on ';' which is enough for this project.
    """
    text = path.read_text(encoding="utf-8")
    statements = [s.strip() for s in text.split(";") if s.strip()]
    for stmt in statements:
        # Useful log to debug
        print(f"Running Cypher statement:\n{stmt[:80]}...")
        run_cypher(stmt)


# ------------- Utilities -------------


def chunk(df: pd.DataFrame, size: int = 1000) -> Iterable[List[Dict]]:
    """
    Splits a DataFrame into batches of dict rows for batch processing.
    """
    if df.empty:
        return
    for start in range(0, len(df), size):
        yield df.iloc[start : start + size].to_dict(orient="records")


# ------------- Main ETL -------------


def etl():
    """
    Main ETL function that migrates data from PostgreSQL to Neo4j.

    This function performs the complete Extract, Transform, Load process:
    1. Waits for both databases to be ready
    2. Sets up Neo4j schema using queries.cypher file
    3. Extracts data from PostgreSQL tables
    4. Transforms relational data into graph format
    5. Loads data into Neo4j with appropriate relationships

    The process creates the following graph structure:
    - Category nodes with name properties
    - Product nodes linked to categories via IN_CATEGORY relationships
    - Customer nodes with name and join_date properties
    - Order nodes linked to customers via PLACED relationships
    - Order-Product relationships via CONTAINS with quantity properties
    - Dynamic event relationships between customers and products
    """
    # 1. Ensure dependencies are ready (useful when running in docker-compose)
    wait_for_postgres()
    wait_for_neo4j()

    # 2. Apply Neo4j schema (constraints, cleanup, etc.)
    queries_path = Path(__file__).with_name("queries.cypher")
    if queries_path.exists():
        print(f"Applying Neo4j schema from {queries_path}...")
        run_cypher_file(queries_path)
    else:
        print("WARNING: queries.cypher not found, continuing without schema.")

    # 3. Extract data from PostgreSQL
    print("Extracting data from Postgres...")
    with get_pg_conn() as conn:
        customers = pd.read_sql("SELECT * FROM customers", conn)
        categories = pd.read_sql("SELECT * FROM categories", conn)
        products = pd.read_sql("SELECT * FROM products", conn)
        orders = pd.read_sql("SELECT * FROM orders", conn)
        order_items = pd.read_sql("SELECT * FROM order_items", conn)
        events = pd.read_sql("SELECT * FROM events", conn)

    print(
        f"Rows: customers={len(customers)}, categories={len(categories)}, "
        f"products={len(products)}, orders={len(orders)}, "
        f"order_items={len(order_items)}, events={len(events)}"
    )

    # 4. Load into Neo4j

    # 4.1 Categories
    print("Loading categories into Neo4j...")
    for rows in chunk(categories):
        run_cypher(
            """
            UNWIND $rows AS row
            MERGE (c:Category {id: row.id})
            SET c.name = row.name
            """,
            {"rows": rows},
        )

    # 4.2 Products + IN_CATEGORY
    print("Loading products into Neo4j...")
    for rows in chunk(products):
        run_cypher(
            """
            UNWIND $rows AS row
            MERGE (p:Product {id: row.id})
            SET p.name = row.name,
                p.price = row.price
            WITH p, row
            MATCH (c:Category {id: row.category_id})
            MERGE (p)-[:IN_CATEGORY]->(c)
            """,
            {"rows": rows},
        )

    # 4.3 Customers
    print("Loading customers into Neo4j...")
    for rows in chunk(customers):
        run_cypher(
            """
            UNWIND $rows AS row
            MERGE (c:Customer {id: row.id})
            SET c.name = row.name,
                c.join_date = row.join_date
            """,
            {"rows": rows},
        )

    # 4.4 Orders + PLACED
    print("Loading orders into Neo4j...")
    for rows in chunk(orders):
        run_cypher(
            """
            UNWIND $rows AS row
            MERGE (o:Order {id: row.id})
            SET o.ts = row.ts
            WITH o, row
            MATCH (c:Customer {id: row.customer_id})
            MERGE (c)-[:PLACED]->(o)
            """,
            {"rows": rows},
        )

    # 4.5 Order items: CONTAINS
    print("Loading order items into Neo4j...")
    for rows in chunk(order_items):
        run_cypher(
            """
            UNWIND $rows AS row
            MATCH (o:Order {id: row.order_id})
            MATCH (p:Product {id: row.product_id})
            MERGE (o)-[r:CONTAINS]->(p)
            SET r.quantity = row.quantity
            """,
            {"rows": rows},
        )

    # 4.6 Events: VIEWED / CLICKED / ADDED_TO_CART
    print("Loading events into Neo4j...")

    def load_events_for_type(ev_type: str, rel_type: str):
        sub = events[events["event_type"] == ev_type]
        if sub.empty:
            return
        for rows in chunk(sub):
            run_cypher(
                f"""
                UNWIND $rows AS row
                MATCH (c:Customer {{id: row.customer_id}})
                MATCH (p:Product {{id: row.product_id}})
                MERGE (c)-[r:{rel_type}]->(p)
                // optional: keep last timestamp
                SET r.last_ts = row.ts
                """,
                {"rows": rows},
            )

    load_events_for_type("view", "VIEWED")
    load_events_for_type("click", "CLICKED")
    load_events_for_type("add_to_cart", "ADDED_TO_CART")

    print("ETL done.")


if __name__ == "__main__":
    etl()
