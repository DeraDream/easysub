"""数据库初始化编排：自动建库、建表、迁移、种子数据与定时任务。"""

from app import bootstrap, database, migrate
from app.seed import seed_all
from app.services import scheduler


def initialize_database(cfg: dict, *, create_database: bool = True, persist_config: bool = False) -> None:
    if create_database:
        bootstrap.ensure_database(cfg)
    database.init_engine(bootstrap.build_url(cfg))
    database.Base.metadata.create_all(bind=database.engine)
    migrate.run_migrations(database.engine)
    db = database.SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()
    if persist_config:
        bootstrap.save_config(cfg)
    scheduler.start_scheduler()
