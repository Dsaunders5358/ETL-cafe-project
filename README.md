# ADS Group Project
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