#!/usr/bin/env python3

import sys
import requests
from requests.auth import HTTPBasicAuth
from getpass import getuser, getpass
import json
import datetime
from openpyxl import Workbook

def authenticate(user, password):
	"""
		This function takes a user/password combo and attempts to authenticate those credentials and return an auth token

		Parameters
		==========
		user: str
			This is the username
		password: str
			This is the password
		
		Returns
		=======
		Auth token to be appended to future API requests
	"""

	auth_url = "http://a1vsecxrypl01.q2dc.local/api/v1/auth/token"
	headers = {'Content-type': 'application/json'}
	data = {
		"name": user,
		"password": password
	}
	json_data = json.dumps(data)

	res = requests.post(auth_url, headers=headers, data=json_data, verify=False)
	print(res.text)
	return res.json()


def get_violations(authE, watch):
	"""
		This function returns a json object with the violations matching a particular 'Watch'.  The JFrog API has paginated
		results so that has to be accounted for.  Also, a separate HTTP request has to be made for each viuolation in order
		to get all the details for each violation.  TODO, violation details could be pulled out into a separate method.

		Parameters
		==========
		authE: requests.auth.HTTPBasicAuth object
			For authentication
		watch: str
			String containing the name of the watch you want violations for
	"""

	violations_url = "http://a1vsecxrypl01.q2dc.local/api/v1/violations"
	headers = {'Content-type': 'application/json'}

	violations_list = []
	total_violations = 0
	block_size = 50
	page = 1
	get_next_page = True

	while get_next_page == True:

		data = {
			"filters": {
				"watch_name": watch
			},
			"pagination": {
				"limit": block_size,
				"offset": page
			}
		}

		json_data = json.dumps(data)

		res = requests.post(violations_url, auth=authE, headers=headers, data=json_data, verify=False)
		resj = res.json()

		total_violations = resj['total_violations']

		if block_size * page >= total_violations:
			get_next_page = False

		for violation in resj['violations']:
			# some nasty parsing incoming
			violation_details = requests.get(violation['violation_details_url'], auth=authE, headers=headers, verify=False).json()

			package_details = violation_details['infected_components'][0].split(':')

			package_manager = package_details[0]
			package_name = package_details[1][2:]
			package_version = package_details[2]
			
			infected_string = ""
			if 'infected_versions' in violation_details:
				for infection in violation_details['infected_versions']:
					infected_string += infection + " || "

			fixstring = ""
			if 'fix_versions' in violation_details:
				for fix in violation_details['fix_versions']:
					fixstring += fix + " || "

			# Not every violation is uniform
			v_type = str(violation_details['type']) if 'type' in violation_details else ""
			v_summary = str(violation_details['summary']) if 'summary' in violation_details else ""
			v_description = str(violation_details['description']) if 'description' in violation_details else ""
			v_severity = str(violation_details['severity']) if 'severity' in violation_details else ""

			violation_dict = {
				"manager": package_manager,
				"package": package_name,
				"version": package_version,
				"type": v_type,
				"summary": v_summary,
				"description": v_description,
				"severity": v_severity,
				"infected_versions": infected_string[:-4],
				"fixed_versions": fixstring[:-4]
			}

			violations_list.append(violation_dict)

		page += 1	

	ret_json = {
		"total_violations": total_violations,
		"violations": violations_list
	}

	return ret_json	


def write_report(violation_data, out_file):
	"""
		This function takes violation JSON data for a particular 'Watch' and writes an Excel report.

		Parameters
		==========
		violation_data: JSON dict
			Dict containing the JSON blob of violations for a particular JFrog X-ray Watch
		out_file: str
			String containing the filename for the resulting .xlsx file to be written
	"""
	book = Workbook()
	sheet = book.active
	sheet.title = "Violations"
	column_headers = [
		"Manager",
		"Package",
		"Version",
		"Type",
		"Summary",
		"Description",
		"Severity",
		"Infected Versions",
		"Fixed Versions"
	]
	sheet.append(column_headers)

	for violation in violation_data["violations"]:
		violation_row = list(violation.values())
		sheet.append(violation_row) 

	book.save(out_file)


def main():
	auth_info = HTTPBasicAuth(getuser(), getpass())
	watch_name = sys.argv[1]
	v = get_violations(auth_info, watch_name)
	#print(json.dumps(v,sort_keys=False,indent=4, separators=(',', ': ')))
	# TODO write a report file with the json results
	out_file = f"{watch_name}-{str(datetime.date.today())}-xray.xlsx"
	print(f"Writing {v['total_violations']} violations to excel report: {out_file}")
	write_report(v, out_file)


if __name__ == "__main__":
	main()