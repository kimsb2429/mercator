import textractcaller as tc
import trp.trp2 as t2
import boto3, os, json


    
def validate_answers(query_answers, valid_answers):
    '''
    Validates textractor query answers against predetermined valid answers.
    The validation answers json can be configured to ask any number of questions for any given form.
    If any one of the answers is correct, the function returns true.
    NOTE: Each alias must be unique in the validation_queries.json. # Turn this into another lambda function "validate_json_files"
    '''

    # make query answers into dict
    query_answer_dict = {answer[1]: answer[2] for answer in query_answers}
    print(query_answer_dict)

    # look for valid answers in query answers dict
    is_valid = False
    for form in valid_answers:
        for item in form['aliasAnswers']:
            if (item['alias'] in query_answer_dict) and (query_answer_dict[item['alias']] in item['validAnswers']):
                is_valid = True
                break

    # return validation result
    print(valid_answers)
    return is_valid #return form id as well so that the next lambda can be configured to make form-specific queries


def validate_document(validation_queries):
    '''Validates a document in S3 using textract queries and predetermined valid answers.'''

    # get input document key 
    input_document_key = "s3://amazon-textract-public-content/blogs/2-pager.pdf" # get from event

    # call textract
    region_name = os.environ['RegionName']
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
    print(query_answers)
    return query_answers

def lambda_handler(event, context):
    '''lambda handler for textractor'''
    
    # read bucket and key from env
    bucket = os.environ['ValidationQueriesS3Bucket']
    validation_queries_key = os.environ['ValidationQueriesS3Key']
    validation_answers_key = os.environ['ValidationAnswersS3Key']
    
    # read validation queries and valid answers from s3
    s3 = boto3.resource('s3')
    validation_queries = json.loads(s3.Object(bucket, validation_queries_key).get()['Body'].read().decode('utf-8'))
    valid_answers = json.loads(s3.Object(bucket, validation_answers_key).get()['Body'].read().decode('utf-8'))
    
    # validate document
    query_answers = validate_document(validation_queries)
    
    # validate answers
    validation_status = validate_answers(query_answers, valid_answers)

    return validation_status