from alembic import context

from spencer.database import Base, data_directory, database_engine

with database_engine(data_directory()).connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata, render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()
