from library.composites.infra.db.engine import engine
from library.infra.db.repos.readers_repo import DbReadersRepo

readers_repo = DbReadersRepo(engine=engine)
