from invoke import task
import shutil
import os
os.chdir(os.path.join(os.path.dirname(__file__),  "accountant"))


@task
def copy_dependencies(c):
	dirs = ["wkhtmltopdf", "sounds"]
	dest = os.path.join("dist", "accountant")
	for d in dirs:
		if os.path.exists(dest):
			print("copying", d)
			shutil.copytree(d, os.path.join(dest, d))
		else:
			print("the destenation folder does not exist. please build the program first")

@task(post=[copy_dependencies])
def build(c):
	print("building")
	if os.path.exists("accountant.spec"):
		c.run("pyinstaller accountant.spec -y")
		