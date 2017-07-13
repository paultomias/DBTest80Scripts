import os, re, shutil, subprocess

cfg_dict = {}

file_path = os.path.dirname(os.path.abspath(__file__))
cfg_path = file_path + "/dbtest80.cfg"
sysdump_path = file_path + "/files/dbtest80.sysdump"
editda_path = file_path + "/files/dbtest80.editda"

#Read and parse the config file
cfg_file = open(cfg_path, "r")

for line in cfg_file:
	match = re.search(r'^([\w]+)\s*=\s*([\w\\\-\@\.]+)', line)
	if match:
		if match.group(1) not in cfg_dict:
			cfg_dict[match.group(1)] = match.group(2)

cfg_file.close()

#Run sysload of dbtest80.sysdump
print("Running sysload for " + cfg_dict["PRODLINE"] + "...\n")
subprocess.call(["sysload", "-efp", sysdump_path, cfg_dict["PRODLINE"]])

#Create the cap file based on the entries from the config file
capfile_path = os.environ["LAWDIR"] + "/" + cfg_dict["PRODLINE"] + "/" + cfg_dict["DBTYPE"].upper()
try:
	print("Creating capfile...")

	cap_file = open(capfile_path, "w")
	cfg_file = open(cfg_path, "r")

	for line in cfg_file:
		if 'PRODLINE' in line:
			break

		match = re.search(r'^([\w]+)\s*=\s*([\w\\\-\@\.]+)', line)
		
		if match:
			cap_file.write(match.group()+"\n")

	cap_file.close()
	cfg_file.close()

	print(cfg_dict["DBTYPE"].upper() + " capfile created in LAWDIR/" + cfg_dict["PRODLINE"] + " SUCCESSFULLY\n")

except OSError as e:
	print ("Error: %s - %s." % (e.filename,e.strerror))

#Create the editda config file based on the entries from the config file
try:
	print("Creating config file for editda command...")
	editda_file = open(editda_path, "w")

	editda_file.write("B " + cfg_dict["DBSPACE"] + " " + cfg_dict["DBTYPE"] + " " + cfg_dict["DATATABLESPACE"] + " " + cfg_dict["INDEXTABLESPACE"] + "\n")
	editda_file.write("D " + cfg_dict["PRODLINE"] + " " + cfg_dict["DBSPACE"])

	print("Config file created SUCCESSFULLY\n")
	editda_file.close()

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