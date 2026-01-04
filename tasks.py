from invoke import task
import shutil
import os
os.chdir(os.path.join(os.path.dirname(__file__),  "accountant"))
import glob


@task
def copy_dependencies(c):
	dirs = ["wkhtmltopdf", "sounds"]
	dest = os.path.join("dist", "accountant")
	dlls = glob.glob("*.dll")
	if os.path.exists(dest):
		for d in dirs:
			print("copying", d)
			shutil.copytree(d, os.path.join(dest, d))
		for dll in dlls:
			print(f"copying: {dll}")
			shutil.copy(dll, dest)
		print("done")
	else:
		print("the destenation folder does not exist. please build the program first")
		

@task(post=[copy_dependencies])
def build(c):
	print("building exe file")
	if os.path.exists("accountant.spec"):
		print("running pyinstaller using accountant.spec")
		c.run("pyinstaller accountant.spec -y")
	else:
		print("accountant.spec does not exist.")
		print("trying to run pyinstaller using command line arguments")
		c.run("pyinstaller -w accountant.py --contents-dir='.'")
	print("done")