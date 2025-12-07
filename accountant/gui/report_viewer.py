import subprocess
import wx
from database import Product, Payment
from utiles import get_events, play
import pdfkit
import os
from config import config_get
from datetime import datetime


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
		export_pdf = wx.Button(p, -1, "استخراج بصيغة pdf...")
		export_pdf.Bind(wx.EVT_BUTTON, self.onPdf)
		close = wx.Button(p, wx.ID_OK, "إغلاق")
		self.report.Value = self.display_report()
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(close, 1)
		sizer.Add(self.report, 1, wx.EXPAND)
		sizer1 = wx.BoxSizer(wx.HORIZONTAL)

		sizer1.Add(export, 1)
		sizer1.Add(exportWeb, 1)
		sizer1.Add(export_pdf, 1)

		sizer.Add(sizer1)
		p.SetSizer(sizer)
		play("report")
		self.ShowModal()
	def display_report(self):
		report = f"""اسم العميل: {self.account.name}
رقم الهاتف: {self.account.phone}
تاريخ التسجيل: {self.account.date.strftime("%d/%m/%Y") if self.account.date else 'غير موثق'}
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
التاريخ: {event.date.strftime("%d/%m/%Y %I:%M %p")}

"""
			elif type(event) == Payment:
				report += "الحدث: دفع مبلغ\n"
				report += f"""المبلغ المدفوع: {event.amount if event.amount - int(event.amount) != 0.0 else int(event.amount)} ريال
التاريخ: {event.date.strftime("%d/%m/%Y %I:%M %p")}
رقم الهاتف: {event.phone}"""
				if event.notes:
					report += f"ملاحظات الدفع: \n{event.notes}"
				report += "\n\n"
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
		path = config_get("default_path")
		path = os.path.join(path, self.account.name, "التقارير الشاملة")
		try:
			os.makedirs(path, exist_ok=True)
		except FileExistsError:
			pass
		path = os.path.join(path, f"التقرير الشامل_{self.account.name}_{datetime.now().strftime('%d-%m-%Y %I-%M %p')}.txt")
		with open(path, "w", encoding="utf-8") as file:
			file.write(self.report.Value)

		self.report.SetFocus()
		if wx.MessageBox(f"تم استخراج التقرير إلى المسار المحدد. هل تريد عرض الملف في الموقع المحفوظ؟", "نجاح", wx.YES_NO, parent=self) == wx.YES:
			subprocess.run(f"""explorer /select,"{path}" """)
	def html_report(self):
		events = get_events(self.account)
		report = \
f"""<html lang='ar' dir='rtl'>
<head>
<meta charset='utf-8' />
<title>كشف الحساب - {self.account.name}</title>
<style>
	body {{
		font-family: Arial, sans-serif;
		background-color: #f9f9f9;
		color: #333;
		line-height: 1.6;
	}}
	.container {{
		max-width: 800px;
		margin: auto;
		padding: 20px;
		background-color: #fff;
		box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
		border-radius: 8px;
	}}
	h2 {{
		background-color: #004e92;
		color: #fff;
		padding: 10px;
		border-radius: 5px;
		text-align: center;
	}}
	table {{
		width: 100%;
		border-collapse: collapse;
		margin-bottom: 20px;
	}}
	table, th, td {{
		border: 1px solid #ddd;
	}}
	th, td {{
		padding: 10px;
		text-align: right;
	}}
	th {{
		background-color: #f2f2f2;
		font-weight: bold;
	}}
	.event-title {{
		color: #004e92;
		font-size: 18px;
		margin-top: 20px;
	}}
	.summary-table th {{
		background-color: #004e92;
		color: white;
	}}
	hr {{
		border: 1px solid #ddd;
		margin: 20px 0;
	}}
</style>
</head>
<body>
<div class='container'>
	<h2>المعلومات الأساسية</h2>
	<table>
		<tr><th>اسم العميل</th><td>{self.account.name}</td></tr>
		<tr><th>رقم الهاتف</th><td>{self.account.phone}</td></tr>
		<tr><th>تاريخ التسجيل</th><td>{self.account.date.strftime("%d/%m/%Y") if self.account.date else 'غير موثق'}</td></tr>
		<tr><th>الحالة</th><td>{"نشط" if self.account.active else "غير نشط"}</td></tr>
		<tr><th>سقف الحساب</th><td>{"لا يوجد" if not self.account.maximum else "{} ريال".format(round(self.account.maximum, 3) if self.account.maximum - int(self.account.maximum) != 0.0 else int(self.account.maximum))}</td></tr>
	</table>
	
	<h2>المنتجات والمدفوعات</h2>
"""

		for event in events:
			if isinstance(event, Product):
				report += f"""
		<div class='event-title'>الحدث: منتج جديد</div>
		<table>
			<tr><th>اسم المنتج</th><td>{event.name}</td></tr>
			<tr><th>السعر</th><td>{event.price if event.price - int(event.price) != 0.0 else int(event.price)} ريال</td></tr>
			<tr><th>رقم الهاتف</th><td>{event.phone}</td></tr>
			<tr><th>التاريخ</th><td>{event.date.strftime("%d/%m/%Y %I:%M %p")}</td></tr>
		</table>
		"""
			elif isinstance(event, Payment):
				report += f"""
		<div class='event-title'>الحدث: دفع مبلغ</div>
		<table>
			<tr><th>المبلغ المدفوع</th><td>{event.amount if event.amount - int(event.amount) != 0.0 else int(event.amount)} ريال</td></tr>
			<tr><th>التاريخ</th><td>{event.date.strftime("%d/%m/%Y %I:%M %p")}</td></tr>
			<tr><th>رقم الهاتف</th><td>{event.phone}</td></tr>
			<tr><th>ملاحظات الدفع</th><td>{event.notes}</td></tr>
		</table>
		"""

		product_total = sum(product.price for product in self.account.products)
		pay_total = sum(payment.amount for payment in self.account.payments)

		report += f"""
	<h2>ملخص الحساب</h2>
	<table class='summary-table'>
		<tr><th>تكلفة جميع المنتجات</th><td>{round(product_total, 1) if product_total - int(product_total) != 0.0 else int(product_total)} ريال</td></tr>
		<tr><th>اجمالي ما تم دفعه</th><td>{round(pay_total, 1) if pay_total - int(pay_total) != 0.0 else int(pay_total)} ريال</td></tr>
		<tr><th>المتبقي من الحساب</th><td>{round(self.account.total, 1) if self.account.total - int(self.account.total) != 0.0 else int(self.account.total)} ريال</td></tr>
	</table>
</div>
</body>
</html>
"""
		return report

	def onHtml(self, event):
		path = config_get("default_path")
		path = os.path.join(path, self.account.name, "التقارير الشاملة")
		try:
			os.makedirs(path, exist_ok=True)
		except FileExistsError:
			pass
		path = os.path.join(path, f"التقرير الشامل_{self.account.name}_{datetime.now().strftime('%d-%m-%Y %I-%M %p')}.html")

		report = self.html_report()
		with open(path, "w", encoding="utf-8") as file:
			file.write(report)
		self.report.SetFocus()
		if wx.MessageBox(f"تم استخراج التقرير إلى المسار المحدد. هل تريد عرض الملف في الموقع المحفوظ؟", "نجاح", wx.YES_NO, parent=self) == wx.YES:
			subprocess.run(f"""explorer /select,"{path}" """)
	def onPdf(self, event):
		path = config_get("default_path")
		path = os.path.join(path, self.account.name, "التقارير الشاملة")
		try:
			os.makedirs(path, exist_ok=True)
		except FileExistsError:
			pass
		path = os.path.join(path, f"التقرير الشامل_{self.account.name}_{datetime.now().strftime('%d-%m-%Y %I-%M %p')}.pdf")
		exe = os.path.join(os.getcwd(), "wkhtmltopdf", "bin", "wkhtmltopdf.exe")
		config = pdfkit.configuration(wkhtmltopdf=exe)
		report = self.html_report()
		pdfkit.from_string(report, path, configuration=config)
		self.report.SetFocus()
		if wx.MessageBox(f"تم استخراج التقرير إلى المسار المحدد. هل تريد عرض الملف في الموقع المحفوظ؟", "نجاح", wx.YES_NO, parent=self) == wx.YES:
			subprocess.run(f"""explorer /select,"{path}" """)
