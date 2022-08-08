import textractcaller as tc
import trp.trp2 as t2
import boto3, os, json, io
from pdf2image import convert_from_bytes
from PIL import Image
from trp import Document

def query_image(img_byte_arr, queries):
    '''Queries an image using textract queries.'''
    
    # call textract
    textract = boto3.client('textract')
    tc_queries = [tc.Query(**query) for query in queries]
    textract_json = tc.call_textract(
        input_document=img_byte_arr,
        queries_config=tc.QueriesConfig(queries=tc_queries),
        features=[tc.Textract_Features.QUERIES],
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
    
def query_document(form_queries, input_document_key):
    '''Queries a document in S3 using textract queries.'''

    # read input document
    s3 = boto3.resource('s3', region_name=os.environ['TextractRegionName'])
    bucket = s3.Bucket(os.environ['FormsBucket'])
    obj = bucket.Object(input_document_key)
    fs = obj.get()['Body'].read()
    
    # convert to images
    images = convert_from_bytes(fs)
    
    # query each image
    query_answers = []
    for idx, img in enumerate(images):
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='png')
        img_byte_arr = img_byte_arr.getvalue()
        queries = get_page_queries(img_byte_arr, idx, form_queries)
        if len(queries) > 0:
            query_answers.extend(query_image(img_byte_arr, queries))

    return query_answers

def get_page_queries(img_byte_arr, idx, form_queries):
    '''Find the queries for the page.'''
    
    # call textract
    textract = boto3.client('textract')
    textract_json = tc.call_textract(
        input_document=img_byte_arr,
        boto3_textract_client=textract
    )
    
    # get response text
    doc = Document(textract_json)
    wordlist = []
    for page in doc.pages:
        for line in page.lines:
            for word in line.words:
                wordlist.append(word.text)
    words = " ".join(wordlist)
    print(f"Text in page {idx+1}: {words}")
    
    # identify page, get queries
    for item in form_queries:
        if item['pageIdentifyingPhrase'] in words:
            return item['queries']
    return []

def get_form_queries(all_queries, form_name):
    '''Find page-identifying phrases and queries for the form.'''
    
    for item in all_queries:
        if item['formName']==form_name:    
            return item['formQueries']
    return {'InvalidStatus': 'Form name not found in the queries json file.'}
            
def lambda_handler(event, context):
    '''Lambda handler for querying the application forms via Textract'''
    
    # get client
    s3 = boto3.resource('s3')
    
    # read params and queries
    input_document_key = event['InputDocumentKey']
    form_name = event['FormName']
    all_queries = json.loads(s3.Object(os.environ['QueriesAnswersS3Bucket'], os.environ['QueriesS3Key']).get()['Body'].read().decode('utf-8'))
    form_queries = get_form_queries(all_queries, form_name)
    if 'InvalidStatus' in form_queries:
        return form_queries
    else:
        
        # query document
        print(f'Page-identifying phrases and queries for the form "{form_name}" are: {form_queries}')
        query_answers = query_document(form_queries, input_document_key)

    return {'FormName': form_name, 'QueryAnswers': query_answers}