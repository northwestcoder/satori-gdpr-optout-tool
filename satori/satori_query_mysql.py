import mysql.connector

def search_for_email(host, port, database, location, user, password, email_to_find, colname):

	str_sql = "SELECT * from {} where {} = '{}';".format(location, colname, email_to_find)

	try:

		mysql_con = mysql.connector.connect(
			user=user,
			password=password,
			host=host,
			database=database,
			port=port)

		mycursor = mysql_con.cursor()

		mycursor.execute(str_sql)

		myresult = mycursor.fetchall()
		return (str(myresult), str_sql)

	except Exception as err:
		print(err)
		return (str(err), str_sql)