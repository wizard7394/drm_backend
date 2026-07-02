import asyncio
from sqlalchemy import text
from app.api.dependencies import get_vault_db

async def run_patch():
    async_gen = get_vault_db()
    session = await anext(async_gen)
    
    queries = [
        "ALTER TABLE courses ADD COLUMN base_stream_url VARCHAR(500);",
        "ALTER TABLE vault_items ADD COLUMN batch_name VARCHAR;",
        "ALTER TABLE vault_items ADD COLUMN original_filename VARCHAR;",
        "ALTER TABLE vault_items ADD COLUMN duration INTEGER;"
    ]
    
    for q in queries:
        try:
            await session.execute(text(q))
            await session.commit()
            print(f"Executed: {q}")
        except Exception as e:
            await session.rollback()
            print(f"Skipped: {q}")
            
    await session.close()

if __name__ == "__main__":
    asyncio.run(run_patch())