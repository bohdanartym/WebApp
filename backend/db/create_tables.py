from backend.db.database import engine
from backend.db.models import Base

async def run():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    import asyncio
    asyncio.run(run())

print("Done!")
