import wx
from utiles import get_events, play, save_html_receet, save_pdf_receet, format_number
from database import add_account, get_account_by_id as Account, Product, Payment, Notification, session
import pyperclip
import subprocess
import os 
from .settings import TextSettingsDialog, AccountMaximumSettingsDialog

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
	def onAdd(self, event=None):
		play("save")

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


	def onPay(self, event=None):
		play("save")


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
		session.commit()
		self.EndModal(self.__id)



class AddProduct(BaseProductDialog):
	def __init__(self, parent, account):
		super().__init__(parent, account)
		self.ShowModal()

	def onAdd(self, event):
		if not self.validate():
			return
		p = Product(name=self.name.Value, price=float(self.price.Value), phone=self.phone.Value)
		if self.account.maximum is not None and p.price + self.account.total > self.account.maximum:
			play("limit")
			wx.MessageBox(f"لقد تجاوزت سقف الحساب البالغ مقداره {self.account.maximum} ريالًا", "خطأ", wx.ICON_ERROR, self)
			self.Destroy()
			return
		p.account = self.account
		session.add(p)
		session.commit()
		self.Destroy()
		super().onAdd(None)
		report = \
f"""اسم المنتج: {p.name}
التاريخ: {p.date.strftime("%d/%m/%Y %I:%M %p")}
رقم الهاتف: {p.phone}
القيمة: {p.price if p.price - int(p.price) != 0.0 else int(p.price)} ريال
إجمالي الحساب: {round(self.account.total, 3) if self.account.total - int(self.account.total) != 0.0 else int(self.account.total)} ريال
"""
		if self.account.maximum:
			used = round(self.account.total/self.account.maximum, 2)
			used = int(used*100)
			if used >= 80:
				report += f"""تنبيه:
استهلكتم {used}% من سقف الحساب

"""
		n = Notification(title="إضافة منتج", body=report, account=self.account)
		session.add(n)
		session.commit()
		SummaryDialog(wx.GetApp().GetTopWindow(), report, p)

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
			play("limit")
			wx.MessageBox(f"لقد تجاوزت سقف الحساب البالغ مقداره {self.account.maximum} ريالًا", "خطأ", wx.ICON_ERROR, self)
			self.Destroy()
			return

		self.product.name = self.name.Value
		self.product.price = float(self.price.Value)
		self.product.phone = self.phone.Value
		session.commit()
		parent = self.Parent
		self.Destroy()
		super().onAdd()
		report = \
f"""اسم المنتج: {self.product.name}
التاريخ: {self.product.date.strftime("%d/%m/%Y %I:%M %p")}
رقم الهاتف: {self.product.phone}
القيمة: {self.product.price if self.product.price - int(self.product.price) != 0.0 else int(self.product.price)} ريال
إجمالي الحساب: {round(self.account.total, 3) if self.account.total - int(self.account.total) != 0.0 else int(self.account.total)} ريال

"""
		n = Notification(title="تحرير منتج", body=report, account=self.account)
		session.add(n)
		session.commit()


		SummaryDialog(parent, report, self.product)

class PayDialog(BasePaymentDialog):
	def __init__(self, parent, account):
		super().__init__(parent, account)
		self.ShowModal()
	def onPay(self, event):
		if not self.validate():
			return
		payment = Payment(amount=float(self.amount.Value), phone=self.phone.Value, notes=self.notes.Value)
		payment.account = self.account
		session.add(payment)
		session.commit()
		self.Destroy()
		super().onPay()
		previous = self.account.total + payment.amount

		report = \
f"""المبلغ المضاف: {payment.amount if payment.amount - int(payment.amount) != 0.0 else int(payment.amount)} ريال
التاريخ: {payment.date.strftime("%d/%m/%Y %I:%M %p")}
الحساب السابق: {round(previous, 3) if previous - int(previous) != 0.0 else int(previous)} ريال
إجمالي الحساب: {round(self.account.total, 3) if self.account.total - int(self.account.total) != 0.0 else int(self.account.total)} ريال
"""
		if self.account.maximum:
			used = round(self.account.total/self.account.maximum, 2)
			used = int(used*100)
			if used >= 80:
				report += f"""تنبيه:
استهلكتم {used}% من سقف الحساب

"""
		n = Notification(title="دفع مبلغ", body=report, account=self.account)
		session.add(n)
		session.commit()
		SummaryDialog(wx.GetApp().GetTopWindow(), report, payment)

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
		session.commit()
		parent = self.Parent
		self.Destroy()
		super().onPay()
		previous = self.account.total + self.payment.amount

		report = \
f"""المبلغ المضاف: {self.payment.amount if self.payment.amount - int(self.payment.amount) != 0.0 else int(self.payment.amount)} ريال
التاريخ: {self.payment.date.strftime("%d/%m/%Y %I:%M %p")}
الحساب السابق: {round(previous, 3) if previous - int(previous) != 0.0 else int(previous)} ريال
إجمالي الحساب: {round(self.account.total, 3) if self.account.total - int(self.account.total) != 0.0 else int(self.account.total)} ريال

"""
		n = Notification(title="تحرير مبلغ", body=report, account=self.account)
		session.add(n)
		session.commit()
		SummaryDialog(parent, report, self.payment)




class EventsHistory(wx.Dialog):
	def __init__(self,parent, account=None, events=None):
		super().__init__(parent, title="تحرير العمليات")
		self.account = account
		self.CenterOnParent()
		p = wx.Panel(self)
		wx.StaticText(p, -1, "قائمة العمليات: ")
		self.eventsBox = wx.ListBox(p, -1)
		if account:
			events = get_events(self.account, True)
		else:
			self.Title = "العمليات"
			
		for event in events:
			if type(event) == Product:
				self.eventsBox.Append(f"المنتج: {event.name}. بتاريخ {event.date.strftime('%d/%m/%Y %I:%M %p')}. القيمة {event.price if event.price - int(event.price) != 0.0 else int(event.price)} ريال", event)
					
			elif type(event) == Payment:
				self.eventsBox.Append(f"دفع مبلغ. القيمة {event.amount if event.amount - int(event.amount) != 0.0 else int(event.amount)} ريال. بتاريخ {event.date.strftime('%d/%m/%Y %I:%M %p')}", event)
		self.editButton = wx.Button(p, -1, "تحرير...")
		if not account:
			open_account_button = wx.Button(p, -1, "فتح الحساب")
			open_account_button.Bind(wx.EVT_BUTTON, self.onOpen)
			open_account_button.SetDefault()
		else:
			
			self.editButton.SetDefault()

		cancelButton = wx.Button(p, wx.ID_CANCEL, "إغلاق")
		self.editButton.Bind(wx.EVT_BUTTON, self.onEdit)
		if self.eventsBox.Count > 0:
			self.eventsBox.Selection = 0
		else:

			self.editButton.Enabled = False
		self.contextSetup()
		self.eventsBox.Bind(wx.EVT_CHAR_HOOK, self.onHook)
		self.Show()
	def onOpen(self, event):
		from .account import AccountViewer
		selection = self.eventsBox.Selection
		account = self.eventsBox.GetClientData(selection).account
		self.Parent.Hide()
		viewer = AccountViewer(wx.GetApp().GetTopWindow(), account)
		play("open")
		self.EndModal(wx.ID_CANCEL)
	def onEdit(self, event):
		selection = self.eventsBox.Selection
		data = self.eventsBox.GetClientData(selection)
		account = data.account
		if type(data) == Product:
			EditProduct(self, account, data)
			self.eventsBox.SetString(selection, f"المنتج: {data.name}. بتاريخ {data.date.strftime('%d/%m/%Y %I:%M %p')}. القيمة {data.price if data.price - int(data.price) != 0.0 else int(data.price)} ريال")
		elif type(data) == Payment:

			EditPaymentDialog(self, account, data)
			self.eventsBox.SetString(selection, f"دفع مبلغ. القيمة {data.amount if data.amount - int(data.amount) != 0.0 else int(data.amount)} ريال. بتاريخ {data.date.strftime('%d/%m/%Y %I:%M %p')}")

	def contextSetup(self):
		context = wx.Menu()
		deleteItem = context.Append(-1, "حذف العملية")
		html = context.Append(-1, "استخراج الإيصال بصيغة HTML")
		pdf = context.Append(-1, "استخراج الإيصال بصيغة PDF")
		self.Bind(wx.EVT_MENU, self.onDelete, deleteItem)
		self.Bind(wx.EVT_MENU, self.onHtml, html)
		self.Bind(wx.EVT_MENU, self.onPdf, pdf)
		self.eventsBox.Bind(wx.EVT_CONTEXT_MENU, lambda e: self.eventsBox.PopupMenu(context) if self.eventsBox.Selection != -1 else None)
	def onPdf(self, event):
		selection = self.eventsBox.GetClientData(self.eventsBox.Selection)
		res = save_pdf_receet(selection)
		if wx.MessageBox(f"تم استخراج الإيصال إلى المسار المحدد. هل تريد عرض الملف في الموقع المحفوظ؟", "نجاح", wx.YES_NO, parent=self) == wx.YES:
			subprocess.run(f"""explorer /select,"{res}" """)
		
	def onDelete(self, event):
		if wx.MessageBox("أمتأكد من رغبتك في حذف العملية المحددة؟", "حذف", style=wx.YES_NO, parent=self) == wx.YES:
			selection = self.eventsBox.Selection
			data = self.eventsBox.GetClientData(selection)
			self.eventsBox.Delete(selection)
			session.delete(data)
			session.commit()
			self.editButton.Enabled = self.eventsBox.Count > 0
	def onHtml(self, event):
		selection = self.eventsBox.GetClientData(self.eventsBox.Selection)
		
		res = save_html_receet(selection)
		if wx.MessageBox(f"تم استخراج الإيصال إلى المسار المحدد. هل تريد عرض الملف في الموقع المحفوظ؟", "نجاح", wx.YES_NO, parent=self) == wx.YES:
			subprocess.run(f"""explorer /select,"{res}" """)

		
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
		wx.StaticText(p, -1, "اسم أو رقم العميل: ")
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
			total = account.total
			total = round(total, 3) if total - int(total) != 0.0 else int(total)

			self.results.Append(f"{account.name}, المجموع {total} ريال", account)
		self.results.Selection = 0
		openButton = wx.Button(p, -1, "اذهب")
		openButton.SetDefault()
		cancelButton = wx.Button(p, wx.ID_CANCEL, "العودة إلى النافذة الرئيسية")
		openButton.Bind(wx.EVT_BUTTON, self.onOpen)
		play("results")
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
		notesLabel = wx.StaticText(p, -1, "ملاحظات: ")
		self.notes = wx.TextCtrl(p, -1, value=self.account.notes, style=wx.TE_MULTILINE + wx.HSCROLL)

		saveButton = wx.Button(p, -1, "حفظ")
		saveButton.SetDefault()
		cancelButton = wx.Button(p, wx.ID_CANCEL, "إلغاء")
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.activeCheck)
		grid = wx.GridSizer(4, 2, 5)
		grid.AddMany([
			(stateLabel, 1),
			(self.maximumState, 1, wx.EXPAND),
			(self.amountLabel, 1),
			(self.maximumAmount, 1, wx.EXPAND),
		(notesLabel, 1),
			(self.notes, 1, wx.EXPAND),
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
		if self.account.notes != self.notes.Value:
			self.account.notes = self.notes.Value
		session.commit()
		self.Destroy()


class SummaryDialog(wx.Dialog):
	def __init__(self, parent, summary, data=None):
		super().__init__(parent, title="ملخص العملية")
		self.data = data
		self.CenterOnParent()
		p = wx.Panel(self)
		lbl = wx.StaticText(p, -1, "محتوى الملخص")
		self.summaryBox = wx.TextCtrl(p, -1, value=summary, style=wx.TE_MULTILINE + wx.TE_READONLY + wx.HSCROLL)
		copyButton = wx.Button(p, -1, "نسخ")
		copyButton.Bind(wx.EVT_BUTTON, self.onCopy)
		if self.data:
			export_pdf = wx.Button(p, -1, "التصدير بصيغة pdf...")
			export_pdf.Bind(wx.EVT_BUTTON, self.onPdf)
			export_html = wx.Button(p, -1, "التصدير بصيغة HTML...")
			export_html.Bind(wx.EVT_BUTTON, self.onHtml)

		closeButton = wx.Button(p, wx.ID_CANCEL, "إغلاق")

		self.ShowModal()

	def onCopy(self, event):
		pyperclip.copy(self.summaryBox.Value)
		self.summaryBox.SetFocus()
	def onHtml(self, event):
		res = save_html_receet(self.data)
		if wx.MessageBox(f"تم استخراج الإيصال إلى المسار المحدد. هل تريد عرض الملف في الموقع المحفوظ؟", "نجاح", wx.YES_NO, parent=self) == wx.YES:
			subprocess.run(f"""explorer /select,"{res}" """)

	def onPdf(self, event):
		res = save_pdf_receet(self.data)
		if wx.MessageBox(f"تم استخراج الإيصال إلى المسار المحدد. هل تريد عرض الملف في الموقع المحفوظ؟", "نجاح", wx.YES_NO, parent=self) == wx.YES:
			subprocess.run(f"""explorer /select,"{res}" """)

			
def has_items(function):
	def rapper(self, event=None):
		if self.notifications.Count > 0 and self.notifications.Selection != -1:
			return function(self, event)
	return rapper

class NotificationDialog(wx.Dialog):
	def __init__(self, parent, account):
		super().__init__(parent, title="الإشعارات")
		self.account = account
		self.CenterOnParent()
		p = wx.Panel(self)
		self.notifications = wx.ListBox(p, -1)
		self.copyButton = wx.Button(p, -1, "نسخ")
		self.deleteButton = wx.Button(p, -1, "حذف...")
		self.clearButton = wx.Button(p, -1, "إفراغ")
		closeButton = wx.Button(p, wx.ID_CANCEL, "إغلاق")
		for notification in self.account.notifications[::-1]:
			self.notifications.Append(f"""الإشعار: {notification.title}. نص الإشعار: {notification.body}""", notification)
		self.toggleControls()
		self.notifications.Selection = 0 if self.notifications.Count > 0 else -1
		self.copyButton.Bind(wx.EVT_BUTTON, self.onCopy)
		self.deleteButton.Bind(wx.EVT_BUTTON, self.onDelete)
		self.clearButton.Bind(wx.EVT_BUTTON, self.onClear)
		self.notifications.Bind(wx.EVT_CHAR_HOOK, self.onHook)
		self.ShowModal()
	def toggleControls(self):
		for control in [self.copyButton, self.deleteButton, self.clearButton]:
			control.Enabled = self.notifications.Count > 0

	@has_items
	def onCopy(self, event):
		selection = self.notifications.Selection
		notification = self.notifications.GetClientData(selection)
		pyperclip.copy(notification.body)
		self.notifications.SetFocus()
	@has_items
	def onDelete(self, event):
		selection = self.notifications.Selection
		notification = self.notifications.GetClientData(selection)
		self.notifications.Delete(selection)
		session.delete(notification)
		session.commit()
		self.notifications.Selection = selection -1
		self.notifications.SetFocus()
		self.toggleControls()
	@has_items
	def onClear(self, event):
		if wx.MessageBox("هل أنت متأكد من رغبتك في إفراغ جميع الإشعارات لهذا الحساب؟", "إفراغ", wx.YES_NO, self) == wx.YES:
			self.notifications.Clear()
			notifications = session.query(Notification).filter_by(account=self.account)
			for n in notifications:
				session.delete(n)
			session.commit()
			self.toggleControls()
		self.notifications.SetFocus()

	def onHook(self, event):
		if event.KeyCode in (wx.WXK_DELETE, wx.WXK_NUMPAD_DELETE):
			self.onDelete(None)
		else:
			event.Skip()


class EventSearchDialog(wx.Dialog):
	def __init__(self, parent):
		super().__init__(parent, title="بحث")
		self.result = None
		p = wx.Panel(self)
		wx.StaticText(p, -1, "رقم الهاتف: ")
		self.phone = wx.TextCtrl(p, -1)
		self.products_check = wx.CheckBox(p, -1, "تضمين المنتجات")
		self.payments_check = wx.CheckBox(p, -1, "تضمين المدفوعات")
		self.products_check.Value = self.payments_check.Value = True
		self.searchButton = wx.Button(p, -1, "بحث")
		self.searchButton.SetDefault()
		self.searchButton.Enabled = False
		cancelButton = wx.Button(p, wx.ID_CANCEL, "إغلاق")
		self.searchButton.Bind(wx.EVT_BUTTON, self.onSearch)
		self.phone.Bind(wx.EVT_TEXT, self.onChange)
	def onSearch(self, event):
		self.events = []
		products = session.query(Product).filter(Product.phone == self.phone.Value) if self.products_check.Value else None
		if products:
			self.events.extend(list(products))
		payments = session.query(Payment).filter(Payment.phone == self.phone.Value) if self.payments_check.Value else None
		if payments:
			self.events.extend(list(payments))
		if self.events:
			self.events = sorted(self.events, key=lambda e: e.date, reverse=True)
			self.EndModal(wx.ID_OK)
		else:
			wx.MessageBox("لم يتم العثور على أية عمليات مرتبطة بالرقم المحدد", "خطأ", wx.ICON_ERROR)
	def onChange(self, event):
		self.searchButton.Enabled = self.phone != ""


class AccountInfo(wx.Dialog):
	def __init__(self, parent, account):
		super().__init__(parent, title="معلومات الحساب", size=(600, 600))
		self.account = account
		main_sizer = wx.BoxSizer(wx.VERTICAL)

		grid = wx.FlexGridSizer(rows=5, cols=3, hgap=10, vgap=10)
		grid.AddGrowableCol(1, 1)

		# ===== اسم العميل =====
		lbl_name = wx.StaticText(self, label="اسم العميل")
		self.txt_name = wx.TextCtrl(
			self,
			value=account.name,
			style=wx.TE_READONLY | wx.TE_MULTILINE
		)
		btn_edit_name = wx.Button(self, label="تعديل")

		grid.Add(lbl_name)
		grid.Add(self.txt_name, 1, wx.EXPAND)
		grid.Add(btn_edit_name)

		lbl_phone = wx.StaticText(self, label="رقم الهاتف")
		self.txt_phone = wx.TextCtrl(
			self,
			value=account.phone,
			style=wx.TE_READONLY | wx.TE_MULTILINE
		)
		btn_edit_phone = wx.Button(self, label="تعديل")

		grid.Add(lbl_phone)
		grid.Add(self.txt_phone, 1, wx.EXPAND)
		grid.Add(btn_edit_phone)

		lbl_status = wx.StaticText(self, label="حالة الحساب")

		status_box = wx.StaticBox(self, label="حالة الحساب")
		status_sizer = wx.StaticBoxSizer(status_box, wx.VERTICAL)

		self.chk_active = wx.CheckBox(status_box, label="نشط")
		self.chk_active.SetValue(account.active)
		status_sizer.Add(self.chk_active, 0, wx.ALL, 5)

		grid.Add(lbl_status)
		grid.Add(status_sizer, 1, wx.EXPAND)
		grid.Add((0, 0))  # عنصر فارغ بدل زر التعديل

		lbl_limit = wx.StaticText(self, label="سقف الحساب")
		self.txt_limit = wx.TextCtrl(
			self,
			style=wx.TE_READONLY | wx.TE_MULTILINE
		)
		btn_edit_limit = wx.Button(self, label="تعديل")
		self.process_limit()
		grid.Add(lbl_limit)
		grid.Add(self.txt_limit, 1, wx.EXPAND)
		grid.Add(btn_edit_limit)

		lbl_notes = wx.StaticText(self, label="ملاحظات")
		self.txt_notes = wx.TextCtrl(
			self,
			value=account.notes,
			style=wx.TE_READONLY | wx.TE_MULTILINE
		)
		btn_edit_notes = wx.Button(self, label="تعديل")

		grid.Add(lbl_notes)
		grid.Add(self.txt_notes, 1, wx.EXPAND)
		grid.Add(btn_edit_notes)

		main_sizer.Add(grid, 1, wx.ALL | wx.EXPAND, 15)

		btn_close = wx.Button(self, wx.ID_OK, label="إغلاق")
		btn_close.SetDefault()
		main_sizer.Add(btn_close, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)
		btn_edit_name.Bind(wx.EVT_BUTTON, self.on_edit_name)
		btn_edit_phone.Bind(wx.EVT_BUTTON, self.on_edit_phone)
		self.chk_active.Bind(wx.EVT_CHECKBOX, self.on_active)
		btn_edit_limit.Bind(wx.EVT_BUTTON, self.on_edit_limit)
		btn_edit_notes.Bind(wx.EVT_BUTTON, self.on_edit_notes)
		self.SetSizer(main_sizer)
		self.Layout()
		self.CentreOnParent()
	def on_edit_name(self, event):
		with TextSettingsDialog(self, "تعديل اسم العميل", "اسم العميل", self.account, "name") as dlg:
			c = dlg.ShowModal()
			if c:
				self.account.name = dlg.res
				session.commit()
				self.txt_name.Value = self.account.name
			self.txt_name.SetFocus()
	def on_edit_phone(self, event):
		with TextSettingsDialog(self, "تعديل رقم الهاتف", "رقم الهاتف", self.account, "phone") as dlg:
			c = dlg.ShowModal()
			if c:
				self.account.phone = dlg.res
				session.commit()
				self.txt_phone.Value = self.account.phone
			self.txt_phone.SetFocus()
	def on_edit_notes(self, event):
		with TextSettingsDialog(self, "تعديل ملاحظات الحساب", "ملاحظات الحساب", self.account, "notes", True) as dlg:
			c = dlg.ShowModal()
			if c:
				self.account.notes = dlg.res
				session.commit()
				self.txt_notes.Value = self.account.notes
			self.txt_notes.SetFocus()
	def on_edit_limit(self, event):
		with AccountMaximumSettingsDialog(self, self.account) as dlg:
			if dlg.ShowModal() == wx.ID_SAVE:
				self.account.maximum = dlg.maximum
				session.commit()
				self.process_limit()
		self.txt_limit.SetFocus()
	def process_limit(self):
		if self.account.maximum is None:
			self.txt_limit.Value = "بلا سقف"
		else:
			self.txt_limit.Value = str(format_number(self.account.maximum))
	def on_active(self, event):
		self.account.active = self.chk_active.Value
		session.commit()