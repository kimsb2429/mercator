import textractcaller as tc
import trp.trp2 as t2
import boto3, os, json

def query_document(queries, input_document_key):
    '''Queries a document in S3 using textract queries.'''

    # call textract
    region_name = os.environ['TextractRegionName']
    textract = boto3.client('textract', region_name=region_name)
    tc_queries = [tc.Query(**query) for query in queries]
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
    
def lambda_handler(event, context):
    '''Lambda handler for querying the application forms via Textract'''
    
    # get client
    s3 = boto3.resource('s3')
    
    # read params and queries
    queries_answers_bucket = os.environ['QueriesAnswersS3Bucket']
    queries_key = os.environ['QueriesS3Key']
    input_document_bucket = os.environ['FormsBucket']
    input_document_key = f"s3://{input_document_bucket}/{event['InputDocumentKey']}"
    form_id = event['FormId']
    queries = json.loads(s3.Object(queries_answers_bucket, queries_key).get()['Body'].read().decode('utf-8'))
    print(f"Queries: {queries}")
    
    # query document
    query_answers = query_document(queries, input_document_key)

    return query_answers