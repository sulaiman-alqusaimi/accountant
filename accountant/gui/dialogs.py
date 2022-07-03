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
		if self.account.maximum is not None and p.price + self.account.total > self.account.maximum:
			wx.MessageBox(f"لقد تجاوزت سقف الحساب البالغ مقداره {self.account.maximum} ريالًا", "خطأ", wx.ICON_ERROR, self)
			self.Destroy()
			return
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
		self.price.Value = str(product.price if product.price - int(product.price) != 0.0 else int(product.price))
		self.phone.Value = product.phone
		self.ShowModal()
	def onAdd(self, event):
		if not self.validate():
			return
		if self.account.maximum is not None and (self.account.total + float(self.price.Value)) - self.product.price > self.account.maximum:
			wx.MessageBox(f"لقد تجاوزت سقف الحساب البالغ مقداره {self.account.maximum} ريالًا", "خطأ", wx.ICON_ERROR, self)
			self.Destroy()
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
		self.amount.Value = str(payment.amount if payment.amount - int(payment.amount) != 0.0 else int(payment.amount))
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
				self.eventsBox.Append(f"المنتج: {event.name}. بتاريخ {event.date.strftime('%d/%m/%Y %#I:%#M %p')}. السعر {event.price if event.price - int(event.price) != 0.0 else int(event.price)} ريال", event)
			elif type(event) == Payment:
				self.eventsBox.Append(f"دفع مبلغ. القيمة {event.amount if event.amount - int(event.amount) != 0.0 else int(event.amount)} ريال. بتاريخ {event.date.strftime('%d/%m/%Y %#I:%#M %p')}", event)
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
			self.eventsBox.SetString(selection, f"المنتج: {data.name}. بتاريخ {data.date.strftime('%d/%m/%Y %#I:%#M %p')}. السعر {data.price if data.price - int(data.price) != 0.0 else int(data.price)} ريال")
		elif type(data) == Payment:
			EditPaymentDialog(self, self.account, data)
			self.eventsBox.SetString(selection, f"دفع مبلغ. القيمة {data.amount if data.amount - int(data.amount) != 0.0 else int(data.amount)} ريال. بتاريخ {data.date.strftime('%d/%m/%Y %#I:%#M %p')}")

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

class AccountSettingsDialog(wx.Dialog):
	def __init__(self, parent, account):
		self.account = account
		super().__init__(parent, title="إعدادات الحساب")
		self.CenterOnParent()
		p = wx.Panel(self)
		self.activeCheck = wx.CheckBox(p, -1, "تنشيط الحساب")
		self.activeCheck.Value = self.account.active
		stateLabel = wx.StaticText(p, -1, "سقف الحساب: ")
		self.maximumState = wx.Choice(p, -1, choices=["بلا سقف", "تعيين سقف"])
		self.maximumState.Selection = 1 if self.account.maximum else 0
		self.amountLabel = wx.StaticText(p, -1, "قيمة السقف: ")
		self.maximumAmount = wx.TextCtrl(p, -1)
		self.togleAmount()
		saveButton = wx.Button(p, -1, "حفظ")
		saveButton.SetDefault()
		cancelButton = wx.Button(p, wx.ID_CANCEL, "إلغاء")
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.activeCheck)
		grid = wx.GridSizer(3, 2, 5)
		grid.AddMany([
			(stateLabel, 1),
			(self.maximumState, 1, wx.EXPAND),
			(self.amountLabel, 1),
			(self.maximumAmount, 1, wx.EXPAND),
			(saveButton, 1),
			(cancelButton, 1)
])
		sizer.Add(grid)
		p.SetSizer(sizer)
		self.maximumState.Bind(wx.EVT_CHOICE, self.onChoice)
		saveButton.Bind(wx.EVT_BUTTON, self.onSave)
		self.ShowModal()

	def togleAmount(self):
		if self.account.maximum is not None:
			self.maximumAmount.Value = str(self.account.maximum)
		else:
			self.maximumAmount.Value = "100000"
			self.amountLabel.Hide()
			self.maximumAmount.Hide()
	def onChoice(self, event):
		selection = self.maximumState.Selection

		if selection == 1:
			self.amountLabel.Show()
			self.maximumAmount.Show()
			self.maximumAmount.SetFocus()
		else:
			self.amountLabel.Hide()
			self.maximumAmount.Hide()

	def onSave(self, event):
		self.account.active = self.activeCheck.Value
		if self.maximumState.Selection == 0:
			maximum = None
		else:
			value = float(self.maximumAmount.Value)
			maximum = value if value - int(value) != 0.0 else int(value)
		self.account.maximum = maximum
		self.Destroy()