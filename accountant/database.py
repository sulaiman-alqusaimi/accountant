import shelve
import paths
import os
from datetime import datetime


path = os.path.join(paths.data_path, "accounts")

with shelve.open(path) as data:
	if not "accounts" in data:
		data["accounts"] = {}

def apply(func):
	def rapper(*args, **kwargs):
		with shelve.open(path) as data:
			return func(*args, file=data, **kwargs)
	return rapper




@apply
def add_account(name, phone_number, file=None):
	ids = list(file["accounts"].keys())
	if ids == []:
		account_id = 0
	else:
		account_id = ids[-1]+1
	accounts = dict(file["accounts"])

	accounts[account_id] = {
		"name": name,
		"phone": phone_number,
		"products": [],
		"payments": [],
		"active": True,
		"maximum": None,
		"total": 0,
		"notes": "",
		"notifications": [],
		"date": datetime.now(),
	}
	file["accounts"] = accounts
	return account_id

@apply
def get_accounts(file=None):
	accounts = []
	for key, data in file["accounts"].items():
		accounts.append((key, data["name"]))
	return accounts

@apply
def delete_account(ac_id, file=None):
	accounts = file["accounts"]
	accounts.pop(ac_id)
	file["accounts"] = accounts


class Account:
	def __init__(self, account_id):
		self.__account_id = account_id
		with shelve.open(path) as data:
			account = data["accounts"][self.__account_id]
		self.__name = account["name"]
		self.__phone = account["phone"]
		self.__products = account["products"]
		self.__payments = account['payments']
		self.__active = account.get("active", True)
		self.__maximum = account.get("maximum")
		self.__notes = account.get("notes", "")
		self.__notifications = account.get("notifications", [])
		self.update_total()
		self.__date = account['date']

	@property
	def date(self):
		return self.__date
	def edit(self, key, value):
		with shelve.open(path) as data:
			accounts = data["accounts"]
			accounts[self.__account_id][key] = value
			data["accounts"] = accounts

	@property
	def name(self):
		return self.__name
	@name.setter
	def name(self, value):
		self.edit("name", value)
		self.__name = value
	@property
	def phone(self):
		return self.__phone
	@phone.setter
	def phone(self, value):
		self.edit("phone", value)
		self.__phone = value
	@property
	def active(self):
		return self.__active
	@active.setter
	def active(self, value):
		self.edit("active", value)
		self.__active = value
	@property
	def notes(self):
		return self.__notes
	@notes.setter
	def notes(self, value):
		self.edit("notes", value)
		self.__notes = value

	@property
	def maximum(self):
		return self.__maximum
	@maximum.setter
	def maximum(self, value):
		self.edit("maximum", value)
		self.__maximum = value


	@property
	def total(self):
		return self.__total
	@total.setter
	def total(self, value):
		# self.edit("total", value)
		# self.__total = value
		raise NotImplementedError("cannot directly modify total")
	def update_total(self):
		total = 0
		for product in self.__products:
			total += product.price
		for payment in self.__payments:
			total -= payment.amount
		self.edit("total", total)
		self.__total = total

	@property
	def products(self):
		return self.__products

	@products.setter
	def products(self, value):
		self.edit("products", value)
		self.__products = value
		self.update_total()

	@property
	def payments(self):
		return self.__payments

	@payments.setter
	def payments(self, value):
		self.edit("payments", value)
		self.__payments = value
		self.update_total()
	@property
	def notifications(self):
		return self.__notifications
	@notifications.setter
	def notifications(self, value):
		self.edit("notifications", value)
		self.__notifications = value


class Product:

	def __init__(self, name, price, phone):
		self.name = name
		self.price = price
		self.phone = phone
		self.date = datetime.now()


class Payment:
	def __init__(self, amount, phone, notes=""):
		self.__date = datetime.now()
		self.amount = amount
		self.phone = phone
		self.notes = notes
	@property
	def date(self):
		return self.__date

class Notification:
	def __init__(self, title, body):
		self.title = title
		self.body = body

