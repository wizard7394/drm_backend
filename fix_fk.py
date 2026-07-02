import asyncio
from sqlalchemy import text
from app.api.dependencies import get_vault_db


async def run_patch():
    async_gen = get_vault_db()
    session = await anext(async_gen)

    queries = [
        "ALTER TABLE course_nodes DROP CONSTRAINT IF EXISTS course_nodes_parent_id_fkey;",
        "ALTER TABLE course_nodes ADD CONSTRAINT course_nodes_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES course_nodes(id) ON DELETE CASCADE;",
    ]

    for q in queries:
        try:
            await session.execute(text(q))
            await session.commit()
            print(f"Executed: {q}")
        except Exception as e:
            await session.rollback()
            print(f"Error: {e}")

    await session.close()


if __name__ == "__main__":
    asyncio.run(run_patch())
