# Cafe ETL project
The goal of this project to create an ETL pipeline based off CSV data from multiple different stores based on their sales. We will be using AWS cloud services, Python, SQL and docker containers to acheive this. This git repo is purely used for. Our team name for this was ADS (Alternate Data Solutions)

**Please note This repo is an archived version only and will not work if run, all data is here and is available for PoC only.**
I have included an example CSV of the data we have received as well as examples of some of the deployment packages that are created when IAC is triggered. Also, because Psycopg2 Python package doesn't work on AWS Lambda currently I had to create my own version of the package which I have kept in this repo so if you see anything related to Psycopg2 then look at the folder in the repo. 

## Tech & Services Used
1. Python
2. Docker
3. AWS S3 Buckets
4. AWS Redshift
5. AWS Cloudformation
6. AWS Lambda
7. AWS SNS
8. AWS SQS
9. AWS CloudWatch
10. AWS Grafana

## How Does this Work?

When a CSV is added to an S3 bucket (ads-raw-data) then a trigger activates which causes a Lambda to read the CSV file, create a staging table in the redshift data warehouse and add all that data to that staging table and copy all of the data except products into it. For products, it seperates all of the products into indivdual items and creates a new CSV which then gets copied over to another staging table within redshift. Then, both staging tables go through a transformation process and any unique fields get added to their respective fields in the database (products, flavours, hashed customer names etc) and get their own entry in the transaction table. Once all the data has been added to the final database the staging tables are deleted and the process is completed.

We have IAC set up here so when an update gets pushed or merged to the main branch, a deployment package is created by installing Python and the requirements.txt file on a docker container and extracting the python package folders that are created and copying them as well as the YAML file in this repo over to another S3 bucket (ADS-resources) and then runs the update command for our cloudformation stack which will create all of our resources (if they don't exist already) and will update anything that has changed.

## AWS Resource Names
### Cloudformation Stack Name:
ads-resources-stack-cf
Contains the infrastructure of the project that sets up the S3 buckets lambda and IAM roles regarding all the functions
### S3Buckets:
1. ads-raw-data: Data bucket that contains all the raw data we receive
2. ads-processed: Data bucket where all of the processed files go to
3. ads-resources: Data bucket that contains all of the files we need to set up our infrastructure aka templates, deployment packages etc
### Lambda Functions:
1. ads-resources-stack-cf-LambdaFunction-69om6pvOXHhN (LambdaFunction) Lambda function that extracts data from CSVs and adds to redshift
2. ads-resources-stack-cf-LambdaCreateDatabase-mRFWTvL9b7Kx(LambdaCreateDatabase) Lambda Function that create the database schema in redshift
### IAM Rolse:
1. ads-resources-stack-cf-LambdaFunctionRole-WE4UIP4FLDCU (LambdaFunctionRole) Role for the lambda functions to access s3 buckets and redshift
