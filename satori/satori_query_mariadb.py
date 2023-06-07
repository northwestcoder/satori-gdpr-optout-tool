#import mariadb
import mysql.connector


def search_for_email(host, port, database, location, user, password, email_to_find, colname):

	rows = []

	str_sql = "SELECT * from {} where {} = '{}';".format(location, colname, email_to_find)

	try:

		connector = mysql.connector.connect(
			user=user,
			password=password,
			host=host,
			database='devmariadb',
			port=int(port)		
			)

		cursor = connector.cursor()
		cursor.execute(str_sql)
		for row in cursor.fetchall():
			rows.append(row)
		print(str(rows))
		return(str(rows), str_sql)

	except Exception as err:
		print(err)
		return(str(err), str_sql)

