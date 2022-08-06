import textractcaller as tc
import trp.trp2 as t2
import boto3, os, json

class Validated(Exception):
    '''Raised when a query answer is found to be valid.'''
    pass

def validate_answers(query_answers, valid_answers):
    '''Validates textractor query answers against predetermined valid answers. Returns true when a correct answer is found.'''

    # make query answers into dict
    query_answer_dict = {answer[1]: answer[2] for answer in query_answers}

    # look for valid answers in query answers dict
    try:
        for form in valid_answers:
            form_id = form['formId']
            for item in form['aliasAnswers']:
                if (item['alias'] in query_answer_dict) and (query_answer_dict[item['alias']] in item['validAnswers']):
                    raise Validated
    except Validated:
        return {
            "is_valid": True, 
            "form_id": form_id, 
            "comment": "Success"
        }
    return {
        "is_valid": False, 
        "comment": "Responses to validation queries did not match any of the answers in the validation answers json file."
    }

def validate_document(validation_queries, input_document_key):
    '''Validates a document in S3 using textract queries and predetermined valid answers.'''

    # call textract
    region_name = os.environ['TextractRegionName']
    textract = boto3.client('textract', region_name=region_name)
    tc_queries = [tc.Query(**query) for query in validation_queries]
    textract_json = tc.call_textract(
        input_document=input_document_key,
        queries_config=tc.QueriesConfig(queries=tc_queries),
        features=[tc.Textract_Features.QUERIES],
        force_async_api=True,
        boto3_textract_client=textract
    )    
    
    # format returned json
    t_doc: t2.TDocument = t2.TDocumentSchema().load(textract_json) 
    query_answers = []
    for page in t_doc.pages:
        query_answers.extend(t_doc.get_query_answers(page=page))
        
    # return query answers
    print(f'Query Answers: {query_answers}')
    return query_answers

def validate_queries(queries, input_document_key):
    '''Validates the validation queries json file.'''
    
    aliases = []
    for query in queries:
        if "text" not in query or "alias" not in query:
            return {"is_valid": False, "comment": f"'text' and 'alias' are required fields in the queries json file and the validation queries json file. Please correct the json file and re-upload {input_document_key}"}
        aliases.append(query['alias'])
    if len(aliases) != len(set(aliases)):
        return {"is_valid": False, "comment": f"alias must be unique for each query in the queries json file and the validation queries json file. Please correct the json file and re-upload {input_document_key}"}
    return {"is_valid": True}
    
def validate_validation_answers(valid_answers, input_document_key):
    '''Validates the validation answers json file.'''
    
    for answer in valid_answers:
        if "formId" not in answer or "aliasAnswers" not in answer:
            return {"is_valid": False, "comment": f"'form_id' and 'aliasAnswers' are required fields in the validation answers json file. Please correct the json file and re-upload {input_document_key}"}
        for aliasAnswer in answer['aliasAnswers']:
            if "alias" not in aliasAnswer or "validAnswers" not in aliasAnswer:
                return {"is_valid": False, "comment": f"'alias' and 'validAnswers' are required fields in the 'aliasAnswers' field of the validation answers json file. Please correct the json file and re-upload {input_document_key}"}
    return {"is_valid": True}
    
def lambda_handler(event, context):
    '''Lambda handler for validating the application forms via Textract'''
    
    # get client
    s3 = boto3.resource('s3')
    
    # read params and validation files
    bucket = os.environ['QueriesAnswersS3Bucket']
    queries_key = os.environ['QueriesS3Key']
    validation_queries_key = os.environ['ValidationQueriesS3Key']
    validation_answers_key = os.environ['ValidationAnswersS3Key']
    input_document_bucket = os.environ['FormsBucket']
    input_document_key = f"s3://{input_document_bucket}/{event['InputDocumentKey']}"
    queries = json.loads(s3.Object(bucket, queries_key).get()['Body'].read().decode('utf-8'))
    validation_queries = json.loads(s3.Object(bucket, validation_queries_key).get()['Body'].read().decode('utf-8'))
    valid_answers = json.loads(s3.Object(bucket, validation_answers_key).get()['Body'].read().decode('utf-8'))
    print(f"Validation Queries: {validation_queries}")
    print(f"Valid Answers: {valid_answers}")
    
    # validate file extension
    if not input_document_key.lower().endswith('.pdf'):
        return {"is_valid": False, "comment": "Document must be a PDF with the extension '.pdf'"}
    
    # validate json files
    validate_result = validate_queries(validation_queries, input_document_key)
    if not validate_result['is_valid']:
        return validate_result
    validate_result = validate_validation_answers(valid_answers, input_document_key)
    if not validate_result['is_valid']:
        return validate_result
    validate_result = validate_queries(queries, input_document_key)
    if not validate_result['is_valid']:
        return validate_result
        
    # validate document
    query_answers = validate_document(validation_queries, input_document_key)
    
    # validate answers
    return validate_answers(query_answers, valid_answers)