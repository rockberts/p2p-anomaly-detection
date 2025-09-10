import os
from dotenv import load_dotenv

load_dotenv()

azure_api_key = os.getenv("azure_api_key")
azure_endpoint = os.getenv("azure_endpoint")
azure_deployment_name = os.getenv("azure_deployment_name")
azure_api_version = os.getenv("azure_api_version")
azure_vector_store_id = os.getenv("azure_vector_store_id")
az_logic_app_url = os.getenv("logicapp_url")