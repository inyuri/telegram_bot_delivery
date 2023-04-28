import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'users'

    telegramId = sqlalchemy.Column(sqlalchemy.Integer, nullable=True, primary_key=True)
    money = sqlalchemy.Column(sqlalchemy.Integer, nullable=True, default=1000)
    amountOrders = sqlalchemy.Column(sqlalchemy.Integer, nullable=True, default=0)
