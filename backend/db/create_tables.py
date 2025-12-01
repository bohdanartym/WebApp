from backend.db.database import engine
from backend.db.models import Base
import asyncio

async def run():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ All tables created successfully!")
    print("Tables:")
    print("  - users")
    print("  - tasks_history")
    print("  - task_progress (NEW)")

if __name__ == "__main__":
    asyncio.run(run())