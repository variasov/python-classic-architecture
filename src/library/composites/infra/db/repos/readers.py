from library.composites.infra.db.engine import engine
from library.infra.db.repos.readers import ReadersRepository

readers_repo = ReadersRepository(db=engine)
