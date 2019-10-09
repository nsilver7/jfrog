#!/usr/bin/env python3

import sys
import json

def main():
	with open("report.csv", "w+") as outfile:
		outfile.write("manager,package,version,type,severity,summary,infected versions,fixed versions\n")
		with open(sys.argv[1]) as infile:
			j_data = json.load(infile)
			for violation in j_data["data"]:
				#print( f"package: { violation['comp_name'] }    version: " )
				infected_string = ""
				if 'infected_versions' in violation:
					for infection in violation['infected_versions']:
						infected_string += infection + " || "

				fixstring = ""
				if 'fix_versions' in violation:
					for fix in violation['fix_versions']:
						fixstring += fix + " || "

				# parse the package manager out
				pm = ""
				if "nuget://" in violation['comp_id']:
					pm = "Nuget"

				if "npm://" in violation['comp_id']:
					pm = "NPM"	 

				out_string = f"{pm},{violation['comp_name']},{violation['comp_version']},{violation['type']},{violation['severity']},{violation['summary']},{infected_string[:-4]},{fixstring[:-4]}\n"
				outfile.write(out_string)	
				

if __name__ == "__main__":
	main()