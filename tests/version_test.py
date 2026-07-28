import asyncio

import asyncpg


async def main():
    conn = await asyncpg.connect(
        user="scraper_user",
        password="scraper_password",
        database="scraper_db",
        host="localhost",
        port=5432,
    )

    version = await conn.fetchval("SELECT version();")
    print(version)

    await conn.close()

asyncio.run(main())