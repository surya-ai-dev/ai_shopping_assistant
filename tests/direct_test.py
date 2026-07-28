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
    print("Connected!")
    await conn.close()

asyncio.run(main())