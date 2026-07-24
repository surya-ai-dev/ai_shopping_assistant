# Project Debugging History: Phases 1 to 5
## AI Shopping Assistant Backend

This document logs all system issues, configuration clashes, and resolutions encountered during the implementation and verification of Phases 1 to 5.

---

## 1. Issue: PostgreSQL Authentication Outage (`InvalidPasswordError`)

### Symptoms
During local database verification runs using `uv run python test_db.py` or Alembic migrations, the application threw the following exception:
```
asyncpg.exceptions.InvalidPasswordError: password authentication failed for user "scraper_user"
```
However, running the database client *inside* the Docker container connected successfully:
```bash
docker exec -it scraper_postgres psql -h localhost -U scraper_user -d scraper_db
```

### Investigation Steps
1. **Credential Check**: Verified `.env` and `settings.py` were using matching credentials:
   * `POSTGRES_USER=scraper_user`
   * `POSTGRES_PASSWORD=scraper_password`
2. **Docker Port Mapping**: Confirmed port `5432` was mapped to the host loopback interface in `docker-compose.yml`.
3. **Internal vs. External Connection Behavior**:
   * Internal connection inside Docker bypassed password verification using the `trust` authentication rule in `pg_hba.conf`.
   * External connection from the host machine routed through the Docker bridge gateway required `md5` or `scram-sha-256` password authentication.

---

## 2. Root Cause: Port Collision with Native Host Services

A native instance of PostgreSQL was running as a background service on the Windows host machine, listening on port `5432`.

### Why it happens:
* **Loopback Routing**: When Python connected to `localhost:5432` on the host machine, the connection routed to the native Windows PostgreSQL service instead of the Docker container.
* **Mismatched Credentials**: The native Windows service did not have the `scraper_user` role configured, resulting in `InvalidPasswordError` errors.
* **Why Docker exec worked**: Running `psql` inside the container bypassed the host's port clash, connecting directly to the container's PostgreSQL service.

---

## 3. Resolution

We resolved this conflict by stopping the native Windows PostgreSQL service:

```powershell
# Stop the native Windows PostgreSQL service (Run as Administrator)
Stop-Service -Name postgresql*
```

Alternatively, you can change the default host port mapping in `docker-compose.yml` to `5433` (or any other non-standard port) to avoid port clashes:
```yaml
ports:
  - "5433:5432"
```

---

## 4. Lessons Learned

* **Isolate Developer Ports**: Avoid mapping development databases to standard ports (like `5432`) to prevent port clashes with local host services.
* **IPv6 vs. IPv4 Resolution**: Explicitly define hosts as `127.0.0.1` rather than `localhost` to bypass IPv6 (`::1`) loopback routing issues on Windows.
* **Persistent Volume Lifecycles**: PostgreSQL containers only initialize credentials on the *very first run*. Remember to clear volumes (`docker compose down -v`) when changing credentials to force a database re-initialization.

---

## 5. Troubleshooting Checklist

Future developers experiencing database connection issues should run the following checks:

* [ ] **Verify port bindings**: Ensure port `5432` or `5433` is not bound by a native host service.
* [ ] **Inspect local environment overrides**: Check if your shell has a global `DATABASE_URL` environment variable that is overriding your `.env` file settings.
* [ ] **Force container re-initialization**: If you changed credentials, drop existing container volumes and rebuild:
  ```bash
  docker compose down -v
  docker compose up -d
  ```
* [ ] **Check IPv6 routing**: Try replacing `localhost` with `127.0.0.1` in your connection strings to bypass IPv6 loopback routing issues.
