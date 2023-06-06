import boto3
import time

#Some Athena Hardwiring

MAX_RESULTS = 100

def search_for_email(athena_results, athena_region, host, database, location, user, password, email_to_find, colname):

	query = "SELECT * FROM {} where {} = '{}' LIMIT {}".format(location, colname, email_to_find, MAX_RESULTS)

	try:

		max_execution = 5
		session = boto3.Session()
		
		client = session.client(
			'athena', 
			region_name=athena_region,
			aws_access_key_id=user, 
			aws_secret_access_key=password,
			endpoint_url='https://' + host
		)

		response = client.start_query_execution(
		QueryString=query,
		QueryExecutionContext={
			'Database': database
		},
		ResultConfiguration={
			'OutputLocation': athena_results
		}
		)

		execution_id = response['QueryExecutionId']
		state = 'RUNNING'

		while (max_execution > 0 and state in ['RUNNING', 'QUEUED']):
			max_execution = max_execution - 1
			response = client.get_query_execution(QueryExecutionId = execution_id)

			if 'QueryExecution' in response and \
					'Status' in response['QueryExecution'] and \
					'State' in response['QueryExecution']['Status']:
				state = response['QueryExecution']['Status']['State']
				if state == 'FAILED':
					return False
				elif state == 'SUCCEEDED':
					
					query_results = client.get_query_results(QueryExecutionId=execution_id, MaxResults=MAX_RESULTS)
					results = []
					rows = []
		
					for row in query_results['ResultSet']['Rows']:
						rows.append(row['Data'])        
			time.sleep(1)
		
		return (str(rows), query)
	except Exception as err:
		print(str(err))
		return (str(err),query)

