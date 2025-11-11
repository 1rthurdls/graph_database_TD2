# Graph Database – TD2

A reproducible setup for a small graph/database assignment that uses:
- **PostgreSQL** for relational data (auto-seeded on first run),
- **Python** code in `app/` (scripts/API as you prefer),
- **Docker Compose** to orchestrate everything.

---

##  What’s inside

- `app/` — Python application code (scripts or API that interacts with the database).  
- `postgres/init/` — SQL files that initialize and seed Postgres automatically on first start.  
- `docker-compose.yml` — Orchestrates the stack (database and, if defined, the app).

---

##  Prerequisites

- Docker & Docker Compose v2+
- (Optional) `psql` CLI (for inspecting the DB)

---

##  Quick start

1) **Clone the repository**
```bash
git clone https://github.com/1rthurdls/graph_database_TD2.git
cd graph_database_TD2
