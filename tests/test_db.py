import asyncio
import asyncpg

async def main():
    try:
        conn = await asyncpg.connect(
            "postgresql://scraper_user:scraper_password@localhost:5432/scraper_db"
        )
        print("✅ Connected successfully!")
        await conn.close()
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")

asyncio.run(main())