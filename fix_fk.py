import asyncio
from sqlalchemy import text
from app.api.dependencies import get_vault_db


async def run_patch():
    async_gen = get_vault_db()
    session = await anext(async_gen)

    queries = [
        "ALTER TABLE course_nodes DROP COLUMN IF EXISTS attachment_url;",
        "ALTER TABLE course_nodes ADD COLUMN attachments JSONB;",
        """
        CREATE TABLE IF NOT EXISTS watched_videos (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            vault_uuid VARCHAR,
            watched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_watched_videos_user_id ON watched_videos (user_id);",
        "CREATE INDEX IF NOT EXISTS ix_watched_videos_vault_uuid ON watched_videos (vault_uuid);",
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
