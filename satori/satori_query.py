
# THIS IS A STUB FOR FUTURE WORK
# We use this method for consistency of experience. No actual DB call occurs

def search_for_email(host, port, database, location, user, password, email_to_find, colname):

	str_sql = "SELECT * from {} where {} = '{}';".format(location, colname, email_to_find)	
	return ('', str_sql)