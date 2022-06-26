import wx
from utiles import get_events
from database import add_account, Account, Product, Payment


class AccountInfo(wx.Dialog):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.CentreOnParent()
		p = wx.Panel(self)
		wx.StaticText(p, -1, "اسم العميل: ")
		self.accountName = wx.TextCtrl(p, -1)
		wx.StaticText(p, -1, "رقم الهاتف:")
		self.phoneNumber = wx.TextCtrl(p, -1)
		saveButton = wx.Button(p, wx.ID_SAVE, "حفظ")
		saveButton.SetDefault()
		cancelButton = wx.Button(p, wx.ID_CANCEL, "إلغاء")
		self.Bind(wx.EVT_BUTTON, self.onSave, id=wx.ID_SAVE)
	def onSave(self, event):
		raise NotImplementedError()
	def validate(self):
		if self.accountName.Value == "" or self.phoneNumber.Value == "":
			return
		return True


class BaseProductDialog(wx.Dialog):
	def __init__(self, parent, account):
		self.account = account
		super().__init__(parent, title="إضافة منتج")
		self.CenterOnParent()
		p = wx.Panel(self)
		wx.StaticText(p, -1, "اسم المنتج: ")
		self.name = wx.TextCtrl(p, -1)
		wx.StaticText(p, -1, "التكلفة: ")
		self.price = wx.TextCtrl(p, -1)
		wx.StaticText(p, -1, "رقم الهاتف: ")
		self.phone = wx.TextCtrl(p, -1, value=self.account.phone)
		addButton = wx.Button(p, wx.ID_ADD, "حفظ")
		addButton.SetDefault()
		cancel = wx.Button(p, wx.ID_CANCEL, "إلغاء")
		addButton.Bind(wx.EVT_BUTTON, self.onAdd)
	def onAdd(self, event):
		raise NotImplementedError()
	def validate(self):
		if not self.name.Value:
			return
		try:
			float(self.price.Value)
		except ValueError:
			wx.MessageBox("يجب أن يحتوي حقل كتابة التكلفة على أرقام فقط", "خطأ", wx.ICON_ERROR, self)
			return
		return True

class BasePaymentDialog(wx.Dialog):
	def __init__(self, parent, account):
		self.account = account
		super().__init__(parent, title="ادفع")
		self.CenterOnParent()
		p = wx.Panel(self)
		wx.StaticText(p, -1, "المبلغ: ")
		self.amount = wx.TextCtrl(p, -1)
		wx.StaticText(p, -1, "رقم الهاتف: ")
		self.phone = wx.TextCtrl(p, -1, value=self.account.phone)
		wx.StaticText(p, -1, "ملاحظات الدفع: ")
		self.notes = wx.TextCtrl(p, -1, style=wx.TE_MULTILINE + wx.HSCROLL)
		pay = wx.Button(p, -1, "احفظ")
		pay.SetDefault()
		cancel = wx.Button(p, wx.ID_CANCEL, "إلغاء")
		pay.Bind(wx.EVT_BUTTON, self.onPay)
	def validate(self):
		try:
			float(self.amount.Value)
		except ValueError:
			wx.MessageBox("يتم قبول الأرقام الصحيحة والعشرية فقط في حقل كتابة المبلغ", "خطأ", wx.ICON_ERROR, self)
			return
		return True


	def onPay(self, event):
		raise NotImplementedError()


class NewAccountDialog(AccountInfo):
	def __init__(self, parent):
		super().__init__(parent, title="عميل جديد")
	def onSave(self, event):
		if not self.validate():
			return
		account_id = add_account(self.accountName.Value, self.phoneNumber.Value)
		self.saved = True
		self.EndModal(account_id)


class EditAccountDialog(AccountInfo):
	def __init__(self, parent, name, phone, account_id):
		super().__init__(parent, title="تعديل معلومات الحساب")
		self.name = self.accountName.Value = name
		self.phone = self.phoneNumber.Value = phone
		self.__id = account_id
	def onSave(self, event):
		if not self.validate():
			return
		account = Account(self.__id)
		if self.accountName.Value != self.name:
			self.new_name = account.name = self.accountName.Value
		if self.phoneNumber.Value != self.phone:
			account.phone = self.phoneNumber.Value
		self.EndModal(self.__id)



class AddProduct(BaseProductDialog):
	def __init__(self, parent, account):
		super().__init__(parent, account)
		self.ShowModal()

	def onAdd(self, event):
		if not self.validate():
			return
		p = Product(self.name.Value, float(self.price.Value), self.phone.Value)
		products = self.account.products
		products.append(p)
		self.account.products = products
		self.Destroy()


class EditProduct(BaseProductDialog):
	def __init__(self, parent, account, product):
		self.product = product
		super().__init__(parent, account)
		self.Title = "تحرير المنتج"
		self.name.Value = product.name
		self.price.Value = str(product.price)
		self.phone.Value = product.phone
		self.ShowModal()
	def onAdd(self, event):
		if not self.validate():
			return
		self.product.name = self.name.Value
		self.product.price = float(self.price.Value)
		self.product.phone = self.phone.Value
		self.account.products = self.account.products
		self.Destroy()


class PayDialog(BasePaymentDialog):
	def __init__(self, parent, account):
		super().__init__(parent, account)
		self.ShowModal()
	def onPay(self, event):
		if not self.validate():
			return
		payment = Payment(float(self.amount.Value), self.phone.Value, self.notes.Value)
		payments = list(self.account.payments)
		payments.append(payment)
		self.account.payments = payments
		self.account.update_total()
		self.Destroy()


class EditPaymentDialog(BasePaymentDialog):
	def __init__(self, parent, account, payment):
		self.payment = payment
		super().__init__(parent, account)
		self.Title = "تحرير معلومات الدفع"
		self.amount.Value = str(payment.amount)
		self.phone.Value = payment.phone
		self.notes.Value = payment.notes
		self.ShowModal()
	def onPay(self, event):
		self.payment.amount = float(self.amount.Value)
		self.payment.phone = self.phone.Value
		self.payment.notes = self.notes.Value
		self.account.payments = self.account.payments
		self.Destroy()



class EventsHistory(wx.Dialog):
	def __init__(self,parent, account):
		super().__init__(parent, title="تحرير العمليات")
		self.account = account
		self.CenterOnParent()
		p = wx.Panel(self)
		wx.StaticText(p, -1, "قائمة العمليات: ")
		self.eventsBox = wx.ListBox(p, -1)
		events = get_events(self.account, True)
		for event in events:
			if type(event) == Product:
				self.eventsBox.Append(f"المنتج: {event.name}. بتاريخ {event.date.strftime('%d/%m/%Y %#I:%#M %p')}. السعر {event.price}", event)
			elif type(event) == Payment:
				self.eventsBox.Append(f"دفع مبلغ. القيمة {event.amount}. بتاريخ {event.date.strftime('%d/%m/%Y %#I:%#M %p')}", event)
		self.editButton = wx.Button(p, -1, "تحرير...")
		cancelButton = wx.Button(p, wx.ID_CANCEL, "إغلاق")
		self.editButton.SetDefault()
		self.editButton.Bind(wx.EVT_BUTTON, self.onEdit)
		if self.eventsBox.Count > 0:
			self.eventsBox.Selection = 0
		else:
			self.editButton.Enabled = False
		self.contextSetup()
		self.eventsBox.Bind(wx.EVT_CHAR_HOOK, self.onHook)
		self.Show()
	def onEdit(self, event):
		selection = self.eventsBox.Selection
		data = self.eventsBox.GetClientData(selection)
		if type(data) == Product:
			EditProduct(self, self.account, data)
			self.eventsBox.SetString(selection, f"المنتج: {data.name}. بتاريخ {data.date.strftime('%d/%m/%Y %#I:%#M %p')}. السعر {data.price}")
		elif type(data) == Payment:
			EditPaymentDialog(self, self.account, data)
			self.eventsBox.SetString(selection, f"دفع مبلغ. القيمة {data.amount}. بتاريخ {data.date.strftime('%d/%m/%Y %#I:%#M %p')}")

	def contextSetup(self):
		context = wx.Menu()
		deleteItem = context.Append(-1, "حذف العملية")
		self.Bind(wx.EVT_MENU, self.onDelete, deleteItem)
		self.eventsBox.Bind(wx.EVT_CONTEXT_MENU, lambda e: self.eventsBox.PopupMenu(context) if self.eventsBox.Selection != -1 else None)

	def onDelete(self, event):
		if wx.MessageBox("أمتأكد من رغبتك في حذف العملية المحددة؟", "حذف", style=wx.YES_NO, parent=self) == wx.YES:
			selection = self.eventsBox.Selection
			data = self.eventsBox.GetClientData(selection)
			self.eventsBox.Delete(selection)
			if type(data) == Product:
				self.account.products.remove(data)
				self.account.products = self.account.products
			else:
				self.account.payments.remove(data)
				self.account.payments = self.account.payments
			self.editButton.Enabled = self.eventsBox.Count > 0

	def onHook(self, event):
		if event.KeyCode in (wx.WXK_DELETE, wx.WXK_NUMPAD_DELETE) and self.eventsBox.Selection != -1:
			self.onDelete(None)
		else:
			event.Skip()

class SearchDialog(wx.Dialog):
	def __init__(self, parent):
		super().__init__(parent, title="بحث")
		self.result = None
		p = wx.Panel(self)
		wx.StaticText(p, -1, "اسم العميل: ")
		self.name = wx.TextCtrl(p, -1)
		self.searchButton = wx.Button(p, -1, "بحث")
		self.searchButton.SetDefault()
		self.searchButton.Enabled = False
		cancelButton = wx.Button(p, wx.ID_CANCEL, "إغلاق")
		self.searchButton.Bind(wx.EVT_BUTTON, self.onSearch)
		self.name.Bind(wx.EVT_TEXT, self.onChange)
		self.ShowModal()
	def onSearch(self, event):
		self.result = self.name.Value
		self.Destroy()
	def onChange(self, event):
		self.searchButton.Enabled = self.name != ""



class ResultsDialog(wx.Dialog):
	def __init__(self, parent, accounts):
		super().__init__(parent, title="نتائج البحث")
		self.CenterOnParent()
		self.account = None
		p = wx.Panel(self)
		wx.StaticText(p, -1, "قائمة العملاء: ")
		self.results = wx.ListBox(p, -1)
		for account in accounts:
			self.results.Append(account[1], account)
		self.results.Selection = 0
		openButton = wx.Button(p, -1, "اذهب")
		openButton.SetDefault()
		cancelButton = wx.Button(p, wx.ID_CANCEL, "العودة إلى النافذة الرئيسية")
		ه=i=openButton.Bind(wx.EVT_BUTTON, self.onOpen)
		self.ShowModal()

	def onOpen(self, event):
		self.account = self.results.GetClientData(self.results.Selection)
		self.Destroy()