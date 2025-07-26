from collections.abc import Generator
from contextlib import contextmanager
from sqlalchemy.orm import Session


class TransactionRollback(Exception):
    pass


@contextmanager
def atomic_transaction(db: Session) -> Generator[None, None, None]:
    """
    Context manager for database transactions.
    Automatically commits the transaction if no exception occurs,
    or rolls it back if an exception is raised.
    
    Example:
        with transaction(db):
            db.add(item)
            # No need to call db.commit() here
    """
    try:
        yield
    except Exception as e:
        db.rollback()
        raise TransactionRollback(str(e))
    else:
        db.commit()
