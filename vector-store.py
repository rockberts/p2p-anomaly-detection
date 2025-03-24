import config
from openai import OpenAI
import json

client = OpenAI(api_key=config.api_key)

# This is to create a vector store in OpenAI
# vector_store = client.vector_stores.create(
#   name="BusinessRules"
# )
# print(vector_store)


# Ready the files for upload to OpenAI
# file_paths = ["data_files/p2p-rules.txt"]
# file_streams = [open(path, "rb") for path in file_paths]

# vector_store = client.vector_stores.retrieve(
#   vector_store_id=config.vector_store_id
# )
# # Use the upload and poll SDK helper to upload the files, add them to the vector store,
# # and poll the status of the file batch for completion.
# file_batch = client.vector_stores.file_batches.upload_and_poll(
#   vector_store_id=vector_store.id, files=file_streams
# )

# # You can print the status and the file counts of the batch to see the result of this operation.
# print(file_batch.status)
# print(file_batch.file_counts)

# test the vector store
response = client.responses.create(
    model="gpt-4o",
    tools=[{
      "type": "file_search",
      "vector_store_ids": [config.vector_store_id],
      "max_num_results": 20
    }],
    input="What are business rules in procure to pay process?",
)

print(json.dumps(response, default=lambda o: o.__dict__, indent=4))
