
import paths
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

path = os.path.join(paths.data_path, "accountant.db")
# Create a SQLite database
engine = create_engine(f'sqlite:///{path}')

# Create a session factory
Session = sessionmaker(bind=engine)
session = Session()

# Create a base class for declarative models
Base = declarative_base()

def add_account(name, phone):
	account = Account(name=name, phone=phone, date=datetime.now())
	session.add(account)
	session.commit()
	return account.id

def delete_account(account_id):
	account = session.query(Account).get(account_id)
	session.delete(account)
	session.commit()

def get_accounts():
	accounts = list(session.query(Account))
	return accounts


def get_account_by_id(account_id):
	data = session.query(Account).filter_by(id=account_id)
	return list(data)[0]


# Define the "accounts" model class
class Account(Base):
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    maximum = Column(Float, default=None)
    notes = Column(Text, default="")
    date = Column(DateTime)
    payments = relationship("Payment", back_populates="account", cascade="all, delete")
    products = relationship("Product", back_populates="account", cascade="all, delete")
    notifications = relationship("Notification", back_populates="account", cascade="all, delete")
    @property
    def total(self):
        total_products = sum(product.price for product in self.products)
        total_payments = sum(payment.amount for payment in self.payments)
        return total_products - total_payments

# Define the "payments" model class
class Payment(Base):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.now())
    amount = Column(Float)
    phone = Column(String)
    notes = Column(Text)
    account_id = Column(Integer, ForeignKey('accounts.id'))

    account = relationship("Account", back_populates="payments")
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.date = datetime.now()

# Define the "products" model class
class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(Float)
    phone = Column(String)
    date = Column(DateTime, default=datetime.now())
    account_id = Column(Integer, ForeignKey('accounts.id'))

    account = relationship("Account", back_populates="products")
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.date = datetime.now()


# Define the "notifications" model class
class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    body = Column(Text)
    account_id = Column(Integer, ForeignKey('accounts.id'))

    account = relationship("Account", back_populates="notifications")


Base.metadata.create_all(engine, checkfirst=True)
