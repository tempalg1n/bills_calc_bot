import datetime

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from .models import Base, User, Report

from settings import database_config


def engine():
    engine = create_engine(database_config.url, echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


def add_user(tg_id):
    session = engine()
    user = session.query(User).filter(User.tg_id == tg_id).first()
    if user is None:
        new_user = User(tg_id=tg_id)
        session.add(new_user)
        session.commit()


def set_user_address(tg_id, address):
    session = engine()
    user = session.query(User).filter(User.tg_id == tg_id).first()
    user.address = address
    session.commit()


def get_user_address(tg_id):
    session = engine()
    address = session.query(User).filter(User.tg_id == tg_id).first().address
    return address


class Tariff:
    def __init__(self):
        self.hot = 223.04
        self.cold = 45.88
        self.drainage = 35.53
        self.electricity = 6.17

    @property
    def tariff(self):
        tariff = [self.hot, self.cold, self.drainage, self.electricity]
        return tariff

    @tariff.setter
    def tariff(self, hot, cold, drainage, electricity):
        self.hot = hot
        self.cold = cold
        self.drainage = drainage
        self.electricity = electricity


def do_report(tg_id, cold, hot, electricity):
    session = engine()
    address = session.query(User).filter(User.tg_id == tg_id).first().address
    last_report = session.query(Report).filter(User.tg_id == tg_id).order_by(desc('date')).first()
    tariff = Tariff()
    drainage = hot - last_report.hot + cold - last_report.cold
    hot_bill = (hot - last_report.hot) * tariff.hot
    cold_bill = (cold - last_report.cold) * tariff.cold
    electricity_bill = (electricity - last_report.electricity) * tariff.electricity
    drainage_bill = drainage * tariff.drainage
    total = hot_bill + cold_bill + electricity_bill + drainage_bill
    bills_dict = {
        'hot': hot_bill,
        'cold': cold_bill,
        'electricity': electricity_bill,
        'drainage': drainage_bill,
        'total': total
    }
    user = session.query(User).filter(User.tg_id == tg_id).first()
    report = Report(owner=user.id, cold=cold, hot=hot, electricity=electricity,
                    address=address)
    session.add(report)
    session.commit()
    return bills_dict


def get_reports(tg_id):
    session = engine()
    user = session.query(User).filter(User.tg_id == tg_id).first()
    reports = user.reports
    return reports


def delete_user_report(report_id):
    session = engine()
    report = session.get(Report, report_id)
    session.delete(report)
    session.commit()


def do_reports_for_me(tg_id):
    session = engine()
    user = session.query(User).filter(User.tg_id == tg_id).first()
    if not get_reports(tg_id):
        july = Report(owner=user.id, date='2022-07-20', cold=90, hot=66, electricity=9369,
                      address='Пролетарский проспект 43к2')
        august = Report(owner=user.id, date='2022-08-15', cold=95, hot=68, electricity=9507,
                        address='Пролетарский проспект 43к2')
        september = Report(owner=user.id, date='2022-09-15', cold=99, hot=70, electricity=9641,
                           address='Пролетарский проспект 43к2')
        october = Report(owner=user.id, date='2022-10-15', cold=104, hot=75, electricity=9815,
                         address='Пролетарский проспект 43к2')
        session.add(july)
        session.add(august)
        session.add(september)
        session.add(october)
        session.commit()
