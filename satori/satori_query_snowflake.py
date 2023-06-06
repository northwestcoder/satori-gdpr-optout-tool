import snowflake.connector

def search_for_email(host, database, schema, location, email_to_find, colname, snowflake_account, snowflake_username, snowflake_password):
	
	str_sql = "SELECT * from " + location + " where " + colname + " = '" + email_to_find + "'"

	try:
		ctx = snowflake.connector.connect(
			account=snowflake_account,
			password= snowflake_password,
			user=snowflake_username,
			host=host,
			database=database,
			schema=schema
			)

		result = ''
		
		cs = ctx.cursor()
			
		cs.execute(str_sql)
		for row in cs:
			result += str(row) + "\n"
		return (result, str_sql)

	except Exception as err:
		print(str(err))
		return (str(err), str_sql)
