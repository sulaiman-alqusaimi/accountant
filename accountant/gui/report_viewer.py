import subprocess
import wx
from database import Product, Payment
from utiles import get_events, play

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
		exportWeb = wx.Button(p, -1, "تصدير كملف html")
		exportWeb.Bind(wx.EVT_BUTTON, self.onHtml)
		close = wx.Button(p, wx.ID_OK, "إغلاق")
		self.report.Value = self.display_report()
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(close, 1)
		sizer.Add(self.report, 1, wx.EXPAND)
		sizer1 = wx.BoxSizer(wx.HORIZONTAL)

		sizer1.Add(export, 1)
		sizer1.Add(exportWeb, 1)
		sizer.Add(sizer1)
		p.SetSizer(sizer)
		play("report")
		self.ShowModal()
	def display_report(self):
		report = f"""اسم العميل: {self.account.name}
رقم الهاتف: {self.account.phone}
تاريخ التسجيل: {self.account.date.strftime("%d/%m/%Y")}
حالة الحساب: {"نشط" if self.account.active else "غير نشط"}
سقف الحساب: {"لا يوجد" if not self.account.maximum else "{} ريال".format(round(self.account.maximum, 3) if self.account.maximum - int(self.account.maximum) != 0.0 else int(self.account.maximum))}


"""
		events = get_events(self.account)
		for event in events:
			if type(event) == Product:
				report += "الحدث: منتج جديد\n"
				report += f"""اسم المنتج: {event.name}
السعر: {event.price if event.price - int(event.price) != 0.0 else int(event.price)} ريال
رقم الهاتف: {event.phone}
التاريخ: {event.date.strftime("%d/%m/%Y %#I:%#M %p")}

"""
			elif type(event) == Payment:
				report += "الحدث: دفع مبلغ\n"
				report += f"""المبلغ المدفوع: {event.amount if event.amount - int(event.amount) != 0.0 else int(event.amount)} ريال
التاريخ: {event.date.strftime("%d/%m/%Y %#I:%#M %p")}
رقم الهاتف: {event.phone}

"""
				if event.notes:
					report += f"ملاحظات الدفع: \n{event.notes}"
				report += "\n\n"
		product_total = 0
		for product in self.account.products:
			product_total += product.price
		report += f"تكلفة جميع المنتجات: {product_total if product_total - int(product_total) != 0.0 else int(product_total)} ريال\n"
		pay_total = 0
		for payment in self.account.payments:
			pay_total += payment.amount

		report += f"إجمالي ما تم دفعه: {pay_total if pay_total - int(pay_total) != 0.0 else int(pay_total)} ريال\n"
		report += f"المتبقي من الحساب: {round(self.account.total, 3) if self.account.total - int(self.account.total) != 0.0 else int(self.account.total)} ريال\n"

		return report

	def onExport(self, event):
		path = wx.SaveFileSelector(" ", ".txt", f"تقرير المحاسب الشخصي_{self.account.name}", self)
		if not path:
			return
		with open(path, "w", encoding="utf-8") as file:
			file.write(self.report.Value)

		self.report.SetFocus()
		if wx.MessageBox(f"تم استخراج التقرير إلى المسار المحدد. هل تريد عرض الملف في الموقع المحفوظ؟", "نجاح", wx.YES_NO, parent=self) == wx.YES:
			subprocess.run(f"""explorer /select,"{path}" """)


	def onHtml(self, event):
		path = wx.SaveFileSelector(" ", ".html", f"تقرير المحاسب الشخصي_{self.account.name}", self)
		if not path:
			return

		events = get_events(self.account)
		report = \
f"""<html lang='ar' dir='rtl'>
<head>
<meta charset='utf-8' />
<title>كشف الحساب - {self.account.name}</title>
</head>
<body>
<div style='font-size:18px;text-align:center;'>
<h2><b>المعلومات الأساسية</b></h2>
<table border="1">
<tr>
<th>اسم العميل</th>
<td>{self.account.name}</td>
</tr>
<tr>
<th>رقم الهاتف</th>
<td>{self.account.phone}</td>
</tr>
<tr>
<th>تاريخ التسجيل</th>
<td>{self.account.date.strftime("%d/%m/%Y")}</td>
</tr>
<tr>
<th>الحالة</th>
<td>{"نشط" if self.account.active else "غير نشط"}</td>
</tr>
<tr>
<th>سقف الحساب</th>
<td>{"لا يوجد" if not self.account.maximum else "{} ريال".format(round(self.account.maximum, 3) if self.account.maximum - int(self.account.maximum) != 0.0 else int(self.account.maximum))}
</tr>
</table>
<hr />

<h2><b>المنتجات والمدفوعات</b></h2>

"""


		for event in events:
			if type(event) == Product:
				report += \
f"""<h3>الحدث: منتج جديد</h3>
<table border="1">
<tr>
<th>اسم المنتج</th>
<td>{event.name}</td>
</tr>
<tr>
<th>السعر</th>
<td>{event.price if event.price - int(event.price) != 0.0 else int(event.price)} ريال</td>
</tr>

<tr>
<th>رقم الهاتف</th>
<td>{event.phone}</td>
</tr>

<tr>
<th>التاريخ</th>
<td>{event.date.strftime("%d/%m/%Y %#I:%#M %p")}</td>
</tr>
</table>
<hr />
"""
			elif type(event) == Payment:
				report += \
f"""
<h3>الحدث: دفع مبلغ</h3>
<table border="1">
<tr>

<th>المبلغ المدفوع</th>
<td>{event.amount if event.amount - int(event.amount) != 0.0 else int(event.amount)} ريال</td>
</tr>

<tr>
<th>التاريخ</th>
<td>{event.date.strftime("%d/%m/%Y %#I:%#M %p")}</td>
</tr>

<tr>
<th>رقم الهاتف</th>

<td>{event.phone}</td>
</tr>

<tr>
<th>ملاحظات الدفع</th>
<td>{event.notes}</td>
</tr>
</table>
<hr />
"""

		product_total = 0
		for product in self.account.products:
			product_total += product.price
		pay_total = 0
		for payment in self.account.payments:
			pay_total += payment.amount



		report += \
f"""
<h2><b>ملخص الحساب</b></h2>
<br />
<table border="1">
<tr>
<th>تكلفة جميع المنتجات</th>
<td>{product_total if product_total - int(product_total) != 0.0 else int(product_total)} ريال</td>
</tr>

<tr>
<th>اجمالي ما تم دفعه</th>
<td>{pay_total if pay_total - int(pay_total) != 0.0 else int(pay_total)} ريال</td>
</tr>
<tr>
<th>المتبقي من الحساب</th>
<td>{self.account.total if self.account.total - int(self.account.total) != 0.0 else int(self.account.total)} ريال</td>
</tr>

</table></div>
</body>
</html>
"""
		with open(path, "w", encoding="utf-8") as file:
			file.write(report)
		self.report.SetFocus()
		if wx.MessageBox(f"تم استخراج التقرير إلى المسار المحدد. هل تريد عرض الملف في الموقع المحفوظ؟", "نجاح", wx.YES_NO, parent=self) == wx.YES:
			subprocess.run(f"""explorer /select,"{path}" """)

