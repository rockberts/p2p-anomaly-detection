import config
from openai import OpenAI
from openai import AzureOpenAI
from tools import retrieve_contract
import base64
import json
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.core.credentials import AzureKeyCredential

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)


### client = OpenAI(api_key=config.api_key)
client = AzureOpenAI(
    azure_endpoint="https://aoai-gpt4-001.openai.azure.com/",
    azure_ad_token_provider=token_provider,
    api_version="2025-03-01-preview"
)


available_functions = {
    "retrieve_contract": retrieve_contract,
}

# read the Purchase Invoice image(s) to be sent as input to the model
image_paths = ["data_files/Invoice-002.png"]


def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


# Encode images
base64_images = [encode_image_to_base64(image_path) for image_path in image_paths]

# These are the tools that will be used by the Responses API.
tools_list = [
    {
        "type": "file_search",
        "vector_store_ids": [config.vector_store_id],
        "max_num_results": 20,
    },
    {
        "type": "function",
        "name": "retrieve_contract",
        "description": "fetch contract details for the given contract_id and supplier_id",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_id": {
                    "type": "string",
                    "description": "The contract id registered for the Supplier in the System",
                },
                "supplier_id": {
                    "type": "string",
                    "description": "The Supplier ID registered in the System",
                },
            },
            "required": ["contract_id", "supplier_id"],
        },
    },
]



instructions = """
This is a Procure to Pay process. You will be provided with the Purchase Invoice image as input.
Note that Step 3 can be performed only after Step 1 and Step 2 are completed.
Step 1: As a first step, you will extract the Contract ID and Supplier ID from the Invoice and also all the line items from the Invoice in the form of a table.
Step 2: You will then use the function tool to call the Logic app with the Contract ID and Supplier ID to get the contract details.
Step 3: You will then use the file search tool to retrieve the business rules applicable to detection of anomalies in the Procure to Pay process.
Step 4: Then, apply the retrieved business rules to match the invoice line items with the contract details fetched from the system, and detect anomalies if any.
Provide the list of anomalies detected in the Invoice, and the business rules that were violated.
"""

user_prompt = """
here are the Purchase Invoice image(s) as input. Detect anomalies in the procure to pay process and give me a detailed report
"""


input_messages = [
    {
        "role": "user",
        "content": [
            {"type": "input_text", "text": user_prompt},
            *[
                {
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{base64_image}",
                    "detail": "high",
                }
                for base64_image in base64_images
            ],
        ],
    }
]


# The following code is to call the Responses API with the input messages and tools
response = client.responses.create(
    model=config.model,
    instructions=instructions,
    input=input_messages,
    tools=tools_list,
    tool_choice="auto",
    parallel_tool_calls=False,
)
tool_call = response.output[0]
print("Response from the model:", response)
# print(f"tool call: {tool_call}")

# We know this needs a function call, that needs to be executed from here in the application code.
# Lets get hold of the function name and arguments from the Responses API response.
function_response = None
function_to_call = None
function_name = None

# When a function call is entailed, Responses API gives us control so that we can make the call from our application.
# Note that this is because function call is to run our own custom code, it is not a hosted tool that Responses API can directly access and run.
if response.output[0].type == "function_call":
    function_name = response.output[0].name
    function_to_call = available_functions[function_name]
    function_args = json.loads(response.output[0].arguments)
    # Lets call the Logic app with the function arguments to get the contract details.
    function_response = function_to_call(**function_args)

# append the response message to the input messages, and proceed with the next call to the Responses API.
input_messages.append(tool_call)  # append model's function call message
input_messages.append(
    {  # append result message
        "type": "function_call_output",
        "call_id": tool_call.call_id,
        "output": str(function_response),
    }
)

# This is the final call to the Responses API with the input messages and tools
response_2 = client.responses.create(
    model=config.model,
    instructions=instructions,
    input=input_messages,
    tools=tools_list,
)
print(response_2.output_text)
# print("Response from the model:")
# print(json.dumps(response_2, default=lambda o: o.__dict__, indent=4))
