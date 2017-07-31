import os, re, sys, shutil, subprocess

#Check if GENDIR is set
if "GENDIR" not in os.environ:
	print("ERROR: GENDIR is not set. Please set GENDIR before running this script.")
	sys.exit(1)

file_path = os.path.dirname(os.path.abspath(__file__))
cfg_path = file_path + "/dbtest80.cfg"
rundbtests_path = file_path + "/files/rundbtests.pl"
jar_path = file_path + "/files/DBTests.jar"
class_path = file_path + "/files/classes"
gen_java = os.environ['GENDIR'] + "/java/classes"

#Read dbtest80.cfg to get the value of the prodline to perform rubdbtests
try:
	f = open(cfg_path, "r")
	for line in f:
		match = re.search(r'^PRODLINE\s*=\s*([^\#\t\n\r\s]+)', line)
		if match:
			prodline = match.group(1)
			continue

		match = re.search(r'^OS\s*=\s*([^\#\t\n\r\s]+)', line)
		if match:
			platform = match.group(1)

	if 'prodline' not in locals() or 'platform' not in locals():
		print("ERROR: OS or PRODLINE not set in dbtest80.cfg")
		f.close()
		sys.exit(1)
	
	f.close()

except OSError as e:
	print ("Error: %s - %s." % (e.filename,e.strerror))

#Add DBTests.jar to CLASSPATH if not yet added
print("Checking CLASSPATH...")
if "CLASSPATH" in os.environ:
	if jar_path not in os.environ['CLASSPATH']:
		print("Adding DBTest.jar to CLASSPATH")

		if os == "WINDOWS":
			os.environ['CLASSPATH'] = jar_path + ";" + os.environ['CLASSPATH']
		else:
			os.environ['CLASSPATH'] = jar_path + ":" + os.environ['CLASSPATH']

		print("CLASSPATH=" + os.environ['CLASSPATH'] + "\n")
	else:
		print("DBTest.jar already in CLASSPATH")
else:
	print("CLASSPATH is not set. Setting environment variable CLASSPATH")
	os.environ['CLASSPATH'] = jar_path
	print("CLASSPATH=" + os.environ['CLASSPATH'] + "\n")

#Copy all Java regression test classes to GENDIR/java/classes/test/lawson/rdtech/db/api
if not os.path.isdir(gen_java + "/test/lawson/rdtech/db/api"):
	try:
		print("Copying test classes to GENDIR/java/classes/test/lawson/rdtech/db/api...")
		shutil.copytree(class_path, gen_java)
		print("Test classes copied SUCCESSFULLY\n")

		#added command to alter directory classes permission
		subprocess.call("chmod -R 777 " + os.environ['GENDIR'] +  "/java/classes", shell=True)

	except OSError as e:
		print ("Error: %s - %s." % (e.filename,e.strerror))
else:
	print("Copying test classes SKIPPED.\nDirectory: GENDIR/java/classes/test/lawson/rdtech/db/api already exists\n")

#Perform rundbtests script on prodline
print("Running Java Regression Tests on " + prodline + "...\n")
subprocess.call(["perl", rundbtests_path, "-4", prodline])