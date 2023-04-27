import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase


class History(SqlAlchemyBase):
    __tablename__ = 'History'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    tg_id = sqlalchemy.Column(sqlalchemy.String,
                              nullable=True)
    time = sqlalchemy.Column(sqlalchemy.DateTime,
                             default=datetime.datetime.now)
    request = sqlalchemy.Column(sqlalchemy.String,
                                nullable=True)
