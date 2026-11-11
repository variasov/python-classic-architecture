from library.composites.infra.db.engine import engine
from library.infra.db.repos.copies import DbCopiesRepo

copies_repo = DbCopiesRepo(engine)
