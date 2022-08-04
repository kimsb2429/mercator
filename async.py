import boto3, time, io

s3 = boto3.resource('s3', region_name='us-east-1')
bucket = s3.Bucket('mercator-test')
obj = bucket.Object('0.jpg')
response = obj.get()
img_bytes = response['Body']

textract = boto3.client('textract')
response = textract.analyze_document(
    Document={
        'Bytes': img_bytes
    },
    FeatureTypes=["QUERIES"],
    QueriesConfig={
        "Queries": [{
            "Text": "What is the address of the registered office?",
            "Alias": "ADDRESS_REGISTERED_OFFICE"
        }]
    }
    # NotificationChannel={
    #     'SNSTopicArn': 'arn:aws:sns:us-east-1:706676680875:textract',
    #     'RoleArn': 'arn:aws:iam::706676680875:role/textract'
    # },
    # OutputConfig={
    #     'S3Bucket': 'mercator-test',
    #     'S3Prefix': 'textract'
    # }
)
print(response)
# job_id = response['JobId']
# response = textract.get_document_analysis(
#     JobId = job_id
# )
# while (response['JobStatus'] != 'SUCCEEDED'):
#     time.sleep(10)
#     response = textract.get_document_analysis(
#         JobId = job_id
#     )
#     print(job_id, response['JobStatus'])
    
# print(response)


    # DocumentLocation={
    #     'S3Object': {
    #         'Bucket': 'mercator-test',
    #         'Name': '1.jpg'
    #     }
    # },