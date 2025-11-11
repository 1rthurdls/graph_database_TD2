Graph Database – TD2

Short, reproducible setup for a graph-database assignment with a Python app, a PostgreSQL database (with seed SQL), and helper scripts.
Tested with Docker Compose.

✨ What’s inside

app/ — Python application code (API endpoints and Cypher queries for interacting with the graph database).

postgres/init/ — SQL files that initialize and seed the Postgres database on first run.

docker-compose.yml — Orchestrates the stack (database + seeder + app).

Repo structure visible on GitHub: app/, postgres/init/, README, docker-compose.yml.
Language breakdown (approx.): Python ~91%, Cypher ~7%, Shell ~2%.

🧰 Prerequisites

Docker
 and Docker Compose v2+

(Optional) psql CLI for local DB inspection

🚀 Quick start

Clone the repo

git clone https://github.com/1rthurdls/graph_database_TD2.git
cd graph_database_TD2


(Optional) Configure environment
Create a .env file if needed:

POSTGRES_DB=shop
POSTGRES_USER=app
POSTGRES_PASSWORD=appsecret
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Optional if you use Neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password


Start the stack

docker compose up -d --build


This command launches the Postgres database and seeds it automatically with the SQL files located in postgres/init/.

Verify services

Containers

docker compose ps


Database health

docker compose exec postgres pg_isready -U app -d shop -h localhost


Inspect the database

docker compose exec -it postgres psql -U app -d shop
\dt               -- list tables
SELECT NOW();     -- test query

📦 Database seeding

All .sql files inside postgres/init/ are executed automatically on first database initialization.
To reset and reseed the database from scratch:

docker compose down -v
docker compose up -d


Seed file summary:

01_schema.sql — creates all necessary tables and schema structure.

02_data.sql — populates the tables with example data for testing.

🐍 Running the app

The Python application is located in the app/ directory.

Option A — Run with Docker

If your docker-compose.yml includes an app service, it will start automatically with:

docker compose up


Default API endpoint:

http://localhost:8000


Example:

GET /health → checks service status

GET /products → lists items from the database

Option B — Run locally

Create a virtual environment and install dependencies:

cd app
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py

🔷 Working with the graph database (Neo4j)

This repository also contains Cypher queries used to test graph relationships.

If you use Neo4j:

Make sure Neo4j is running (either locally or in Docker).

Connect using the Python Neo4j driver:

from neo4j import GraphDatabase
import os

driver = GraphDatabase.driver(os.getenv("NEO4J_URI"), auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD")))
with driver.session() as s:
    result = s.run("MATCH (n) RETURN count(n) AS nodes")
    print(result.single()["nodes"])


Example Cypher query:

MATCH (a:Person)-[:FRIEND_WITH]->(b:Person)
RETURN a.name, b.name;

🧪 Tests

If you have a tests/ folder:

pytest -q

🧱 Troubleshooting
Problem	Solution
Port already in use (5432 or 8000)	Stop conflicting local services or change ports in docker-compose.yml.
Seed files didn’t execute	They only run on first initialization. Use docker compose down -v to reset.
App cannot connect to Postgres	Ensure both services share the same Docker network and environment variables are correct.
Graph DB connection fails	Verify NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD values and confirm Neo4j is running.
📁 Project structure
graph_database_TD2/
├─ app/                 # Python code (API, scripts, Cypher integration)
├─ postgres/
│  └─ init/             # SQL schema + data seeding
├─ docker-compose.yml   # Service orchestration
└─ README.md
