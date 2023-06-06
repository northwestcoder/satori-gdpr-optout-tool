import psycopg2

def search_for_email(cockroachdb_username, cockroachdb_password, cockroachdb_cluster, host, port, database, location, user, password, email_to_find, colname):

	str_sql = "SELECT * from {} where {} = '{}';".format(location, colname, email_to_find)

	try:

		DATABASE_URL="postgresql://{}:{}@{}:26257/{}.{}?sslmode=require".format(
			cockroachdb_username,
			cockroachdb_password,
			host,
			cockroachdb_cluster,
			database)

		conn = psycopg2.connect(DATABASE_URL)

		conn = psycopg2.connect(DATABASE_URL)		
		cur = conn.cursor()
		cur.execute(str_sql)
		rows = cur.fetchall()
		return (str(rows), str_sql)
	except Exception as err:
		print(str(err))
		return (str(err), str_sql)


