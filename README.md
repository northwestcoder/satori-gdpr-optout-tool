# Satori GDPR Opt Out Tool
#### A python tool that searches all known table locations in all known Satori Datastores for a specific email address and then generates a report for GDPR out-out purposes.

### How and Why Does It Work?

If you combine the following concepts, the result is a tool for querying multiple locations across multiple datastores, searching for a specific email address.

1. Satori has all of your [Datastores](https://satoricyber.com/docs/datastores/data-stores-overview/) defined.
2. Satori provides a temp [username and password](https://satoricyber.com/docs/data%20portal/#data-store-temporary-credentials) for most datastores (except Snowflake and CockroachDB for which we provide input fields if needed).
3. Satori has all of your sensitive email columns tagged using [Satori Data Inventory](https://satoricyber.com/docs/inventory/) features.
4. Satori includes a [Rest API](https://app.satoricyber.com/docs/api) for finding and operating upon datastores and locations. You need a service account and service key to use the Rest API.

Therefore, this tool can iterate through the entire corpus of your Satori account and query each and every email location for a desired email, e.g. ```select * from HOST.DB.SCHEMA.LOCATION where COL = 'janedoe@somedomain.com'```

#### Flow

The flow and order of steps is as follows:

- User fills out the web form
- The tool will gather all Satori Datastores from the Satori account
- For each datastore
	- The tool will gather all inventory locations, and remove any location that is not tagged EMAIL by Satori
	- For each email found
		- If the datastore type is supported (currently MSSQL, MySQL, POSTGRES, SNOWFLAKE, ATHENA and REDSHIFT)
			- The tool will query the table containing the email and return results, or return an error
			- The tool will generate a delete statement for remediation purposes
		- If the datastore type is not supported
			- The tool will still generate a select statement for the table
			- The tool will still generate a remediation statement for the table
- The first section will contain a line item for each EMAIL found as well as records returned and remediation statements
- The second section will summarize for each datastore all select statements required to research further. This section is meant as an exploratory tool for a data engineer.

### Installation

##### Local deployment

- This is a Python Flask app. We have tried to keep the syntax as simple as possible for learning and template purposes.
- This is _not_ considered production code. It is meant as an exploratory tool.
- We have tested on local environments using ```python 3.11.0``` as well as with Docker.
- Basic steps:
	- Download this repository.
	- At a command prompt run ```pip install -r requirements.txt```
		- This attempts to install a few different python database clients, including Postgres, MySQL, MSSQL, Redshift, Athena, CockroachDB and Snowflake. If there are any issues, these client libraries will likely be the culprit. See next section 'Docker Deployment' for a much more convenient method of deployment.
	- Run the app: ```python main.py```
	- The app should now be running. Leave the console open and running - useful debugging output will appear when you use the web app
	- OPTIONAL: create a brand new file "satori/satori.py" and prepopulate the following values, these will override the web form at all times. Useful for testing or for permanently assigning your various credentials.

```
email_to_find = ""

satori_account_id = ""
satori_serviceaccount_id = ""
satori_serviceaccount_key = ""
apihost = ""

satori_username = ""
satori_password = ""

snowflake_username = ""
snowflake_password = ""
snowflake_account = ""

cockroachdb_username = ""
cockroachdb_password = ""
cockroachdb_cluster = ""

mariadb_username = ""
mariadb_password = ""

athena_results = ""
athena_region = ""
```

##### Docker Deployment

- Have Docker Desktop installed (tested on MacOS)
- Download this repo
- Install
	- ```docker build -t satori-gdpr-optout-tool .```
	- ```docker run -dp 8080:8080 satori-gdpr-optout-tool```

##### GCP Cloud Run Deployment

- Install gcloud command line tools (we have tested on macOS)
- Log into google cloud from the command line: ```cloud auth login```
- Set your project: ```gcloud config set project YOUR_PROJECT_ID```
- Make sure Google Cloud Run API's are enabled for this project
- ```gcloud run deploy```


### Usage

- Navigate to http://127.0.0.1:8080/satori/gdpr - ssl is not implemented.
- This app is a simple, single web page with no background tasking or threading.
- Fill out the form. 
	- The Snowflake fields are optional unless you want to query Snowflake sources. The rest of the fields are required. 
	- The API Host field can be left default ("app.satoricyber.com")
- Click "FIND ALL RESULTS". The button status will change to "PLEASE WAIT".
- Be patient. Depending on the number of Satori datasources and locations you have, this step may take a few minutes.
- When the button returns to "FIND ALL RESULTS" you can scroll below it to see the results.

The results are divided into two sections:

1. We show query results that were run against supported datastores, and we also suggest remediation (deletion sql).
2. For each datastore, a full list of select statements are generated for each table that contains an email column. This is meant for further exploration on your part.

**At no point in time will this tool attempt to actually delete information from your datastores!**

- If you are planning to run this multiple times, you should edit gdpr.html and hardwire the form values for Satori Rest API, usernames and passwords, so that you don't have to paste or type these values in over and over again. :)

### Further Info

- All of the logic is initiated in routes_gdpr.py which in turn uses several files in ./satori
- Database ports are hardwired at the top of routes_gdpr.py
- See python comments scattered throughout for more info
- Results are generated using ./templates/base.html and ./templates/gdpr.html

### DB Client Notes

- This tool - painfully - attempts to use several python database clients. In our opinion this is an area fraught with version compatibility issues.
- ```pip requirements.txt``` includes psycopg2, pyodbc, snowflake-connector, and boto3 (for Athena).
- you may wish to consider this repo an example only, and strip out all of the unneeded database client code as appropriate.

