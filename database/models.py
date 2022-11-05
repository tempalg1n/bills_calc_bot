from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True)
    tg_id = Column(Integer, nullable=False)
    address = Column(String)
    connection_date = Column(DateTime, default=datetime.datetime.now, nullable=False)
    reports = relationship('Report', backref='report', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return self.tg_id


class Report(Base):
    __tablename__ = 'Reports'
    id = Column(Integer, primary_key=True)
    owner = Column(Integer, ForeignKey('Users.id'), nullable=False)
    date = Column(DateTime, default=datetime.datetime.now, nullable=False)
    cold = Column(Float, nullable=False)
    hot = Column(Float, nullable=False)
    electricity = Column(Float, nullable=False)
    address = Column(String, nullable=False)

    def __repr__(self):
        return self.address
