from library.composites.infra.db.engine import engine
from library.infra.db.repos.readers import DbReadersRepo

readers_repo = DbReadersRepo(engine)
