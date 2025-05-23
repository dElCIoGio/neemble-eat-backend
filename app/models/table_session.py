from app.db.crud import MongoCrud
from app.schema import table_session as table_session_schema


class TableSessionModel(MongoCrud[table_session_schema.TableSessionDocument]):

    model = table_session_schema.TableSessionDocument