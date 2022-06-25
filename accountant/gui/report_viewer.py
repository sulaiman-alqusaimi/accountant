import wx
from database import Product, Payment

class Report(wx.Dialog):
	def __init__(self, parent, account):
		super().__init__(parent, title="تقرير العمليات")
		self.account = account
		self.CenterOnParent()
		self.SetSize(wx.GetDisplaySize())
		p = wx.Panel(self)
		self.report = wx.TextCtrl(p, style=wx.TE_MULTILINE + wx.TE_READONLY + wx.HSCROLL)
		export = wx.Button(p, -1, "تصدير...")
		export.Bind(wx.EVT_BUTTON, self.onExport)
		close = wx.Button(p, wx.ID_OK, "إغلاق")
		self.report.Value = self.display_report()
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(close, 1)
		sizer.Add(self.report, 1, wx.EXPAND)
		sizer.Add(export, 1)
		p.SetSizer(sizer)
		self.ShowModal()
	def display_report(self):
		report = f"""اسم العميل: {self.account.name}
رقم الهاتف: {self.account.phone}
تاريخ التسجيل: {self.account.date.strftime("%d/%m/%Y")}

"""
		events = list(self.account.products)
		events.extend(self.account.payments)
		events = sorted(events, key=lambda e: e.date)
		for event in events:
			if type(event) == Product:
				report += "الحدث: منتج جديد\n"
				report += f"""اسم المنتج: {event.name}
السعر: {event.price}
رقم الهاتف: {event.phone}
التاريخ: {event.date.strftime("%d/%m/%Y %I:%M %p")}

"""
			elif type(event) == Payment:
				report += "الحدث: دفع مبلغ\n"
				report += f"""المبلغ المدفوع: {event.amount}
التاريخ: {event.date.strftime("%d/%m/%Y %I:%M %p")}
رقم الهاتف: {event.phone}

"""
				if event.notes:
					report += f"ملاحظات الدفع: \n{event.notes}"
				report += "\n\n"
		product_total = 0
		for product in self.account.products:
			product_total += product.price
		report += f"تكلفة جميع المنتجات: {product_total}\n"
		pay_total = 0
		for payment in self.account.payments:
			pay_total += payment.amount

		report += f"إجمالي ما تم دفعه: {pay_total}\n"
		report += f"المتبقي من الحساب: {round(self.account.total, 3)}"
		return report

	def onExport(self, event):
		path = wx.SaveFileSelector(" ", ".txt", f"تقرير المحاسب الشخصي_{self.account.name}", self)
		if not path:
			return
		with open(path, "w", encoding="utf-8") as file:
			file.write(self.report.Value)
		wx.MessageBox(f"تم استخراج التقرير إلى المسار {path}", "نجاح", parent=self)
		self.report.SetFocus()
