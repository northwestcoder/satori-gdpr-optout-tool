import pyodbc

def search_for_email(host, database, location, user, password, email_to_find, colname):


	str_sql = "SELECT * from {} where {} = '{}';".format(location, colname, email_to_find)

	try:
		cnxn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';ENCRYPT=yes;UID='+user+';PWD='+ password)
		cursor = cnxn.cursor()
		cursor.execute(str_sql) 
		rows = cursor.fetchall() 
		return (str(rows), str_sql)
	except Exception as err:
		print(err)
		return (str(err),str_sql)
