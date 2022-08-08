# Setup
1. Upload the following files to the S3 bucket and directory of your choice:
- validation-queries.json
- validation-answers.json
- queries.json
- lambda_package.zip
- poppler.zip
- lf/lambda_validate_form/lambda_validate_form.zip
- lf/lambda_execute_queries/lambda_execute_queries.zip
- lf/lambda_handle_validation_failure/lambda_handle_validation_failure.zip
- lf/lambda_handle_query_answers/lambda_handle_query_answers.zip

The zip files are lambda functions and libraries, and the json files are used for Textract.

2. Create CloudFormation Stack using the mercator-application-textract.yaml template.
- e.g., using AWS CLI: aws cloudformation create-stack --stack-name mercator-application-textract --template-body file://mercator-application-textract.yaml --capabilities CAPABILITY_NAMED_IAM

Add parameter arguments or change the default parameter values in the yaml template as needed. 

# Usage
1. Upload an application form to the S3 Forms Bucket/Directory (Template Parameters)
2. Download and examine the csv form in the S3 Output Bucket/Directory (Template Parameters)

# Expected Workflow/Behavior
1. Form is uploaded to the S3 Forms Bucket/Directory
2. State machine is triggered via EventBridge
3. LambdaValidateForm validates the uploaded form via Textract Query, using the validation-queries and validation-answers json files. It also validates the json files used for querying. If validation passes, LambdaExecuteQueries is triggered. The form name is passed on as an event variable.
4. LambdaExecuteQueries 
    - gets the queries for the form from the queries.json file
    - breaks up the pdf into images (Textract performs better this way)
    - finds the page via the "page-identifying phrases" that are configured in the queries.json file. 
    - queries the image/page and returns the answers
5. LambdaHandleQueryAnswers saves the answers
    - If the queries change, the csv file will be saved in a new directory with an incremented version number and create a new file.
    - If the queries haven't changed, the previous csv file will be updated.
6. If validation fails in step 3, LambdaHandleValidationFailure is called. Currently this function does nothing, but it can be developed to send notifications.