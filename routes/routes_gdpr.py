import requests
import json
from collections import defaultdict
from flask import Flask, Blueprint, request, render_template

from satori import satori_common
from satori import satori_locations as locations
from satori import satori_datastores as datastores
from satori import satori_constants as constants
from satori import satori_remediation as remediation

#db clients
from satori import satori
from satori import satori_query as query
from satori import satori_query_postgres as postgres
from satori import satori_query_mssql as mssql
from satori import satori_query_athena as athena
from satori import satori_query_cockroach as cockroachdb
from satori import satori_query_redshift as redshift
from satori import satori_query_snowflake as snowflake

PORT_POSTGRES = "5432"
PORT_REDSHIFT = "5439"
PORT_COCKROACH = "26257"

routes_gdprform = Blueprint('routes_gdprform', __name__)

@routes_gdprform.route('/satori/gdpr/', methods=('GET', 'POST'))
def create():

	result_items = {}
	query_items = defaultdict(list)
	delete_items = defaultdict(list)
	render_items = [result_items, query_items, delete_items]

	if request.method == 'POST':

		email_to_find = '' 
		search_results = ''

		# look in satori/satori.py for values first, else look at web form received

		email_to_find = satori.email_to_find if satori.email_to_find else request.form['email']

		satori_account_id = satori.satori_account_id if satori.satori_account_id else request.form['satori_account_id']
		satori_serviceaccount_id = satori.satori_serviceaccount_id if satori. satori_serviceaccount_id else request.form['satori_serviceaccount_id']
		satori_serviceaccount_key = satori.satori_serviceaccount_key if satori.satori_serviceaccount_key else request.form['satori_serviceaccount_key']
		apihost = satori.apihost if satori.apihost else request.form['apihost']

		satori_username = satori.satori_username if satori.satori_username else request.form['satori_username']
		satori_password = satori.satori_password if satori.satori_password else request.form['satori_password']

		snowflake_username = satori.snowflake_username if satori.snowflake_username else request.form['snowflake_username']
		snowflake_password = satori.snowflake_password if satori.snowflake_password else request.form['snowflake_password']
		snowflake_account = satori.snowflake_account if satori.snowflake_account else request.form['snowflake_account']

		cockroachdb_username = satori.cockroachdb_username if satori.cockroachdb_username else request.form['cockroachdb_username']
		cockroachdb_password = satori.cockroachdb_password if satori.cockroachdb_password else request.form['cockroachdb_password']
		cockroachdb_cluster = satori.cockroachdb_cluster if satori.cockroachdb_cluster else request.form['cockroachdb_cluster']

		athena_results = satori.athena_results if satori.athena_results else request.form['athena_results']
		athena_region = satori.athena_region if satori.athena_region else request.form['athena_region']


		# get auth token
		satori_token = satori_common.satori_auth(satori_serviceaccount_id, satori_serviceaccount_key, apihost)
		
		# minimalist error check on form input and auth token
		if '' in (
				satori_token, 
				email_to_find, 
				satori_username, 
				satori_password):
			return constants.USER_PARAMS_MISSING

		# else let's assume the database-specific constants are not needed and
		# go ahead and authenticate against Satori Rest API and perform main work
		else:

			auth_headers = {
			'Authorization': 'Bearer {}'.format(satori_token), 
			'Content-Type': 'application/json', 'Accept': 'application/json'
			}

			found_datastores = datastores.get_all_datastores(
				auth_headers, 
				apihost, 
				satori_account_id)

			print("Found datastore count: " + str(found_datastores[0]) + "\n")

			for ds_entry in found_datastores[1]:
				datastore_id = ds_entry['id']
				found_locations = locations.get_locations_by_datastore(auth_headers, 
																	   apihost, 
																	   satori_account_id, 
																	   datastore_id)

				satori_hostname = ds_entry['satoriHostname']
				satori_displayname = ds_entry['name']
				db_type = ds_entry['type']

				print("\nSearching " + str(found_locations[0]) + " locations for datastore " + satori_hostname + " (" + db_type + ")")

				# For this example we are only interested in emails and email tags
				
				for location_entry in found_locations[1]:
					tags = location_entry['tags']
					if tags is not None:
						for tag_item in tags:
							if tag_item['name'] == 'EMAIL':
								
								# for each location of type EMAIL, we build the following vars:
								# dbname, table, column_name, schema, query-able location, full_location

								dbname = 		location_entry['location']['db']
								table = 		location_entry['location']['table']
								column_name = 	location_entry['location']['column']

								#some DB's don't have a concept of schema
								if db_type in ('MARIA_DB', 'ATHENA', 'MYSQL'):
									schema = ''
									query_location = table
									full_location = satori_hostname + '::' + dbname + '.' + table + '.' + column_name
									print(constants.print_foundemail + full_location)
								else:
									schema = location_entry['location']['schema']
									query_location = schema + '.' + table
									full_location = satori_hostname + '::' + dbname + '.' + schema + '.' + table + '.' + column_name
									print(constants.print_foundemail + full_location)

								# BEGIN MAIN DB CLIENT WORK

								if db_type == 'POSTGRESQL':
									search_results = postgres.search_for_email(
										satori_hostname, 
										PORT_POSTGRES, 
										dbname, 
										query_location, 
										satori_username, 
										satori_password, 
										email_to_find, 
										column_name)

									print(constants.print_querytext + search_results[0])

									remediation_response = remediation.build_remediation(
										search_results[0], 
										query_location, 
										column_name, 
										email_to_find
										)

									result_items.update(
										{full_location : [search_results[0], remediation_response]}
										)

									query_items[satori_hostname + "::" + dbname].append(search_results[1])
								
								elif db_type == 'REDSHIFT':
									search_results = redshift.search_for_email(
										satori_hostname, 
										PORT_REDSHIFT, 
										dbname, 
										query_location, 
										satori_username, 
										satori_password, 
										email_to_find,
										column_name)
									print(constants.print_querytext + search_results[0])

									remediation_response = remediation.build_remediation(
										search_results[0], 
										query_location, 
										column_name, 
										email_to_find
										)

									result_items.update(
										{full_location : [search_results[0], remediation_response]}
										)

									query_items[satori_hostname + "::" + dbname].append(search_results[1])
								
								elif db_type == 'MSSQL':
									search_results = mssql.search_for_email(
										satori_hostname,
										dbname,
										query_location,
										satori_username,
										satori_password,
										email_to_find,
										column_name)
									
									print(constants.print_querytext + search_results[0])
									
									remediation_response = remediation.build_remediation(
										search_results[0], 
										query_location, 
										column_name, 
										email_to_find
										)
								
									result_items.update(
										{full_location : [search_results[0], remediation_response]}
										)

									query_items[satori_hostname + "::" + dbname].append(search_results[1])

								elif db_type == 'ATHENA':
									search_results = athena.search_for_email(
										athena_results,
										athena_region,
										satori_hostname,
										dbname,
										query_location,
										satori_username,
										satori_password,
										email_to_find,
										column_name)
									
									print(constants.print_querytext + search_results[0])
									
									remediation_response = remediation.build_remediation(
										search_results[0], 
										query_location, 
										column_name, 
										email_to_find
										)
								
									result_items.update(
										{full_location : [search_results[0], remediation_response]}
										)

									query_items[satori_hostname + "::" + dbname].append(search_results[1])

								elif db_type == 'COCKROACH_DB':
									search_results = cockroachdb.search_for_email(
										cockroachdb_username, 
										cockroachdb_password, 
										cockroachdb_cluster,
										satori_hostname,
										PORT_COCKROACH,
										dbname,
										query_location,
										satori_username,
										satori_password,
										email_to_find,
										column_name)
									
									print(constants.print_querytext + search_results[0])
									
									remediation_response = remediation.build_remediation(
										search_results[0], 
										query_location, 
										column_name, 
										email_to_find
										)
								
									result_items.update(
										{full_location : [search_results[0], remediation_response]}
										)

									query_items[satori_hostname + "::" + dbname].append(search_results[1])

								elif db_type == 'SNOWFLAKE':
									search_results = snowflake.search_for_email(
										satori_hostname,
										dbname,
										schema,
										query_location,
										email_to_find,
										column_name,
										snowflake_account,
										snowflake_username,
										snowflake_password
										)

									print(constants.print_querytext + search_results[0])

									remediation_response = remediation.build_remediation(
										search_results[0], 
										query_location, 
										column_name, 
										email_to_find
										)

									result_items.update(
										{full_location : [search_results[0], remediation_response]}
										)

									query_items[satori_hostname + "::" + dbname].append(search_results[1])

								else:

									#THIS IS A STUB FOR FUTURE WORK

									search_results = query.search_for_email(
										satori_hostname, 
										"5432", 
										dbname, 
										query_location, 
										satori_username, 
										satori_password, 
										email_to_find, 
										column_name)

									print(constants.print_noqueryresults)

									remediation_response = remediation.build_remediation(
										search_results[0], 
										query_location, 
										column_name, 
										email_to_find
										)

									result_items.update(
										{full_location : [search_results[0], remediation_response]}
										)

									query_items[satori_hostname + "::" + dbname].append(search_results[1])

								#reset the search results after each location
								search_results = ['','']

			return render_template('gdpr.html', result = render_items)

	else:

		return render_template('gdpr.html', result = render_items)
