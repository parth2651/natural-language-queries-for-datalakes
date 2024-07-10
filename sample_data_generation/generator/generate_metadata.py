import json
import boto3
import os
import argparse

# This script generates metadata from a DDL file and a database name.

# Example usage:
# python3 generate_metadata.py --db_name "Chinook.db" --ddl_file "ddl.txt"

# By default, we assume that the database is stored in a SQLite database.
DEFAULT_CHANNEL = "sqlite"

# Get database_name and ddl file from arguments passed in the command line
parser = argparse.ArgumentParser()
parser.add_argument("--db_name", type=str, required=True)
parser.add_argument("--ddl_file", type=str, required=True)
parser.add_argument("--channel", type=str, default=DEFAULT_CHANNEL)
args = parser.parse_args()
database_name = args.db_name
ddl_file = args.ddl_file
channel = args.channel

def invoke_llm(prompt):
    bedrock_client = boto3.client(
        'bedrock-runtime',
        region_name='us-west-2',
        )
    
    body = {
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 20000,
        "temperature": 0, 
        "top_p": 0,
        "top_k": 250,
        "anthropic_version":"",
    }
    
    body = json.dumps(body)
    
    response = bedrock_client.invoke_model(
                body=body,
                modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                accept='application/json',
                contentType='application/json'
            )
            
    response_content = json.loads(response['body'].read().decode('utf-8'))['content'][0]['text']
            
    return response_content
    
# Loads the DDL from a file
with open(ddl_file, 'r') as file:
    ddl = file.read()
    
prompt = f"""
You are an expert data analyst.
Use the following DDL to write metadata that can be used later to map verbal descriptions and natural language questions to the tables in the DDL.

<DDL>
{ddl}
</DDL>
<DATABASE_NAME>{database_name}</DATABASE_NAME>
<CHANNEL>{channel}</CHANNEL>

Leave out any housekeeping columns like IDs and create/update timestamps.
Only describe the business data in each table.
For each column (especially confusing ones like "ean"), add a description
For example, for the "address" table in a "WebShop" database (from the <DDL> tag attribute), you'd create a metadata tag that looks like this:

<METADATA CHANNEL="{channel}" DATABASE="{database_name}" TABLE="address">
- Description: Addresses for receipts and shipping.
- Data:
-- firstname: Legal first name of the person living at this address
-- lastname: Legal last name of the person living at this address
-- address1: House number, street, apartment
-- address2: Street, floor, room, office number
-- city: City and state name
-- zip: US Zip Code or world postal code
- Relationships:
-- (address.customerid → customer.id) - Table containing information about the customers who purchase products
</METADATA>

Separate eaeach metadata tag with two blank lines.
"""

print("Generating metadata, please wait...")

metadata = invoke_llm(prompt)

tables_metadata = metadata.split("\n\n")
tables_metadata = [table_metadata.strip() for table_metadata in tables_metadata]
tables_metadata = [table_metadata for table_metadata in tables_metadata if table_metadata]

# Create output directory if not exists
if not os.path.exists('output'):
    os.makedirs('output')

# Save tables_metadata to separate files
for table_metadata in tables_metadata:
    # Get database name and table name from metadata tag
    # <METADATA DATABASE="XXXXXXX" TABLE="address">
    database_name = table_metadata.split(" DATABASE=")[1].split("\"")[1]
    table_name = table_metadata.split(" TABLE=")[1].split("\"")[1]
    with open(f"output/{database_name}_{table_name}.txt", "w") as file:
        file.write(table_metadata)

print("Done.")