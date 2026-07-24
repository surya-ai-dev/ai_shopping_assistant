"""Test database connection health."""

import asyncio
import sys
from src.infrastructure.db.session import check_db_health, close_db_engine


async def main() -> None:
    print("Checking database health...")
    health = await check_db_health()
    print("Database Health Result:", health)
    if health.get("status") == "healthy":
        print("✅ Connected successfully")
        sys.exit(0)
    else:
        print("Error: Database connection failed.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        asyncio.run(close_db_engine())
