import os, re, shutil, subprocess

cfg_dict = {}

file_path = os.path.dirname(os.path.abspath(__file__))
cfg_path = file_path + "/dbtest80.cfg"
sysdump_path = file_path + "/files/dbtest80.sysdump"
editda_path = file_path + "/files/dbtest80.editda"

#Read and parse the config file
f = open(cfg_path, "r")

for line in f:
	match = re.search(r'^([\w]+)\s*=\s*([\w\\\-\@]+)', line)
	if match:
		key = match.group(1)
		value  = match.group(2) 
		#Put the entries in the dictionary
		if key not in cfg_dict:
			cfg_dict[key] = value
f.close()

#Run sysload of dbtest80.sysdump
print("Running sysload for " + cfg_dict["PRODLINE"] + "...\n")
subprocess.call(["sysload", "-efp", sysdump_path, cfg_dict["PRODLINE"]])

#Create the cap file based on the entries from the config file
capfile_path = os.environ["LAWDIR"] + "/" + cfg_dict["PRODLINE"] + "/" + cfg_dict["DBTYPE"].upper()
try:
	print("Creating capfile...")
	f = open(capfile_path, "w")

	f.write("DBSERVER=" + cfg_dict["DBSERVER"] + "\n")
	f.write("DBNAME=" + cfg_dict["DBNAME"] + "\n")
	f.write("SCHEMA=" + cfg_dict["SCHEMA"] + "\n")

	if "SERVICENAME" in cfg_dict:
		f.write("SERVICENAME=" + cfg_dict["SERVICENAME"] + "\n")
	else:
		f.write("LOGINNAME=" + cfg_dict["LOGINNAME"] + "\n")
		f.write("PASSWORD=" + cfg_dict["PASSWORD"] + "\n")

	if cfg_dict["DBTYPE"].upper() == "MICROSOFT":
		f.write("FILEGROUPS=" + cfg_dict["FILEGROUPS"] + "\n")

	print(cfg_dict["DBTYPE"].upper() + " capfile created in LAWDIR/" + cfg_dict["PRODLINE"] + " SUCCESSFULLY\n")
	f.close()
except OSError as e:
	print ("Error: %s - %s." % (e.filename,e.strerror))

#Create the editda config file based on the entries from the config file
try:
	print("Creating config file for editda command...")
	f = open(editda_path, "w")

	f.write("B " + cfg_dict["DBSPACE"] + " " + cfg_dict["DBTYPE"] + " " + cfg_dict["DATATABLESPACE"] + " " + cfg_dict["INDEXTABLESPACE"] + "\n")
	f.write("D " + cfg_dict["PRODLINE"] + " " + cfg_dict["DBSPACE"])

	print("Config file created SUCCESSFULLY\n")
	f.close()
except OSError as e:
	print ("Error: %s - %s." % (e.filename,e.strerror))

#Run editda command
print("Creating and assigning database space to " + cfg_dict["PRODLINE"] + "...")
subprocess.call(["editda", "-c", cfg_dict["PRODLINE"], editda_path])

#Run blddbdict
print("\nRunning blddbdict...")
subprocess.call(["blddbdict", cfg_dict["PRODLINE"]])

#Run dbcreate
print("Running dbcreate...")
subprocess.call(["dbcreate", cfg_dict["PRODLINE"]])