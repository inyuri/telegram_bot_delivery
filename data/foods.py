import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase


class Food(SqlAlchemyBase):
    __tablename__ = 'foods'

    food_title = sqlalchemy.Column(sqlalchemy.String, nullable=True, primary_key=True)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    price = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    path_img = sqlalchemy.Column(sqlalchemy.String, nullable=True)
