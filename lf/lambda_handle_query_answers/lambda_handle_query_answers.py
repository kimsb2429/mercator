import json, os
import awswrangler as wr
import pandas as pd
from datetime import datetime

def lambda_handler(event, context):
    '''Lambda handler for saving query answers to s3'''
    
    # set parameters
    form_name = event['FormName']
    query_answers = event['QueryAnswers']
    form_name_dir = "-".join(form_name.split(" "))
    output_bucket = os.environ['OutputBucket']
    output_folder = 'extracted'
    output_filename = 'output.csv'
    output_path = f's3://{output_bucket}/{output_folder}/{form_name_dir}'
    datetime_str = datetime.now().strftime('%Y%m%d%H%M%S')
  
    # convert answers to dataframe
    query_answers_json = {}
    for item in query_answers:
        query_answers_json.update({item[1]: item[2]})
    df = pd.DataFrame([query_answers_json])
    
    # if no csv file exists for this form, write the output
    if not wr.s3.does_object_exist(f'{output_path}/0/csv/{output_filename}'):
        wr.s3.to_csv(df=df, path=f'{output_path}/0/csv/{output_filename}', sep='|')
        wr.s3.to_parquet(df=df, path=f'{output_path}/0/partitions/{datetime_str}.parquet')
        return f'New csv file created for the form {form_name} at: {output_path}/0/csv/{output_filename}'
    
    # else, get the latest version
    else:
        for i in range(1,250):
            if not wr.s3.does_object_exist(f'{output_path}/{i}/csv/{output_filename}'):
                existing_df = wr.s3.read_parquet(path=f'{output_path}/{i-1}/partitions/*')

                # if same set of columns, update the form
                if set(existing_df.columns)==set(df.columns):
                    wr.s3.to_parquet(df=df, path=f'{output_path}/{i-1}/partitions/{datetime_str}.parquet')
                    sum_df = wr.s3.read_parquet(path=f'{output_path}/{i-1}/partitions/*')
                    wr.s3.delete_objects(f'{output_path}/{i-1}/csv/{output_filename}')
                    wr.s3.to_csv(df=sum_df, path=f'{output_path}/{i-1}/csv/{output_filename}', sep='|')
                    return f'Updated csv file in: {output_path}/{i-1}/csv/{output_filename}'
                
                # else, write output into a new directory with the incremented version number
                else:
                    wr.s3.to_parquet(df=df, path=f'{output_path}/{i}/partitions/{datetime_str}.parquet')
                    wr.s3.to_csv(df=df, path=f'{output_path}/{i}/csv/{output_filename}', sep='|')
                    return f'Schema change detected. New file created at: {output_path}/{i}/csv/{output_filename}'

        return f"You may have too many versions. Please update range max and re-upload {event['InputDocumentKey']}."
