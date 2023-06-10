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
from satori import satori_query_mysql as mysql
from satori import satori_query_mariadb as mariadb
from satori import satori_query_mssql as mssql
from satori import satori_query_athena as athena
from satori import satori_query_cockroach as cockroachdb
from satori import satori_query_redshift as redshift
from satori import satori_query_snowflake as snowflake



PORT_POSTGRES = "5432"
PORT_REDSHIFT = "5439"
PORT_COCKROACH = "26257"
PORT_MYSQL = "12343"
PORT_MARIADB = "12349"

routes_gdprform = Blueprint('routes_gdprform', __name__)

@routes_gdprform.route('/satori/gdpr/', methods=('GET', 'POST'))
def create():

	result_items = {}
	query_items = defaultdict(list)
	delete_items = defaultdict(list)

	if request.method == 'POST':

		email_to_find = '' 
		search_results = ''

		# look in satori/satori.py for values first, else look at web form received

		email_to_find = request.form['email'] if request.form['email'] else satori.email_to_find

		satori_account_id = request.form['satori_account_id'] if request.form['satori_account_id'] else satori.satori_account_id 
		satori_serviceaccount_id = request.form['satori_serviceaccount_id'] if request.form['satori_serviceaccount_id'] else satori. satori_serviceaccount_id 
		satori_serviceaccount_key = request.form['satori_serviceaccount_key'] if request.form['satori_serviceaccount_key'] else satori.satori_serviceaccount_key
		apihost = request.form['apihost'] if request.form['apihost'] else satori.apihost
		print("using api server: " + apihost)

		satori_username = request.form['satori_username'] if request.form['satori_username'] else satori.satori_username
		satori_password = request.form['satori_password'] if request.form['satori_password'] else satori.satori_password

		snowflake_username = request.form['snowflake_username'] if request.form['snowflake_username'] else satori.snowflake_username
		snowflake_password = request.form['snowflake_password'] if request.form['snowflake_password'] else satori.snowflake_password
		snowflake_account = request.form['snowflake_account'] if request.form['snowflake_account'] else satori.snowflake_account

		cockroachdb_username = request.form['cockroachdb_username'] if request.form['cockroachdb_username'] else satori.cockroachdb_username
		cockroachdb_password = request.form['cockroachdb_password'] if request.form['cockroachdb_password'] else satori.cockroachdb_password
		cockroachdb_cluster = request.form['cockroachdb_cluster'] if request.form['cockroachdb_cluster'] else satori.cockroachdb_cluster

		mariadb_username = request.form['mariadb_username'] if request.form['mariadb_username'] else satori.mariadb_username
		mariadb_password = request.form['mariadb_password'] if request.form['mariadb_password'] else satori.mariadb_password

		athena_results = request.form['athena_results'] if request.form['athena_results'] else satori.athena_results
		athena_region = request.form['athena_region'] if request.form['athena_region'] else satori.athena_region

		# get auth token
		satori_token = satori_common.satori_auth(satori_serviceaccount_id, satori_serviceaccount_key, apihost)
		
		# minimalist error check on form input and auth token
		if '' in (
				satori_token, 
				email_to_find):
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

				satori_hostname = str(ds_entry['satoriHostname'])
				satori_displayname = str(ds_entry['name'])
				db_type = str(ds_entry['type'])

				print("\nSearching " + str(found_locations[0]) + " locations for datastore " + satori_hostname + " (" + db_type + ")")

				# For this example we are only interested in emails and email tags
				
				for location_entry in found_locations[1]:

					#reset the search results after each location
					search_results = ['','']
					remediation_response = ''

					tags = location_entry['tags']
					if tags is not None:
						for tag_item in tags:
							if tag_item['name'] == 'EMAIL':


								# for each location of type EMAIL, we build the following vars:
								# dbname, table, column_name, schema, query-able location, full_location

								# NEED TO FINISH databricks, for now omitting
								if db_type == 'DATABRICKS':
									dbname = 		''
									table = 		''
									column_name = 	''
								else:
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

								if db_type == 'POSTGRESQL' and satori_username != '':
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

								if db_type == 'MARIA_DB' and mariadb_username != '':
									search_results = mariadb.search_for_email(
										satori_hostname, 
										PORT_MARIADB, 
										dbname, 
										query_location, 
										mariadb_username, 
										mariadb_password, 
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

								if db_type == 'MYSQL' and satori_username != '':
									search_results = mysql.search_for_email(
										satori_hostname, 
										PORT_MYSQL, 
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
								
								elif db_type == 'REDSHIFT' and satori_username != '':
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
								
								elif db_type == 'MSSQL' and satori_username != '':
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

								elif db_type == 'ATHENA' and athena_results != '':
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

								elif db_type == 'COCKROACH_DB' and cockroachdb_username != '':
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

								elif db_type == 'SNOWFLAKE' and snowflake_username != '':
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
									print("\n\nSkipping unsupported database type or database type is not needed (no user/pass provided): " + db_type + "\n\n")

									#THIS IS A STUB FOR FUTURE WORK

									#search_results = query.search_for_email(
									#	satori_hostname, 
									#	"5432", 
									#	dbname, 
									#	query_location, 
									#	satori_username, 
									#	satori_password, 
									#	email_to_find, 
									#	column_name)

									#print(constants.print_noqueryresults)

									#remediation_response = remediation.build_remediation(
									#	search_results[0], 
									#	query_location, 
									#	column_name, 
									#	email_to_find
									#	)

									#result_items.update(
									#	{full_location : [search_results[0], remediation_response]}
									#	)

									#query_items[satori_hostname + "::" + dbname].append(search_results[1])


			render_items = [result_items, query_items, delete_items]
			return render_template('gdpr.html', result = render_items)

	else:
		render_items = [result_items, query_items, delete_items]
		return render_template('gdpr.html', result = render_items)

