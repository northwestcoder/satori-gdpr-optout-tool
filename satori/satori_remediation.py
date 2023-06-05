def build_remediation(search_results, query_location, column_name, email_to_find):
	if str(search_results) == "None":
		remediation = "None"

	elif str(search_results) == "":
		remediation = "None"

	elif search_results[0:34] == 'Access to unauthorized data denied':
		remediation = "Not allowed to access this data, consider changing Satori permissions for the current user"

	else:
		remediation = "delete from " + query_location + " where " + column_name + " = '" + email_to_find + "';"

	return remediation
									