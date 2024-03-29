import logging

from sqlalchemy.orm import registry

_LOGGER = logging.getLogger(__name__)


def make_declarative_base():
    mapper_registry = registry()
    Base = mapper_registry.generate_base()

    Base.metadata.naming_convention = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s__%(column_0_name)s",
        "ck": "ck_%(table_name)s__%(constraint_name)s",
        "fk": "fk_%(table_name)s__%(column_0_name)s__%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }

    # overwrite the SQLAlchemy __repr__ method for ORM instances
    def base_repr(self):
        values = [
            f"{col.key}={repr(getattr(self, col.key))}" for col in self.__table__.c
        ]
        return f'<Row of {self.__tablename__}: {", ".join(values)}>'

    Base.__repr__ = base_repr
    return Base


Base = make_declarative_base()
# Aliased type annotation useful for type hints
AnyModel = Base
