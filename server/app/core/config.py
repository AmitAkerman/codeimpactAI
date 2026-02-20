# app/core/config.py
import os
from infisical_client import InfisicalClient, ClientSettings, GetSecretOptions


class Settings:
    def __init__(self):
        # Initialize Infisical Client
        self.client = InfisicalClient(ClientSettings(
            client_id=os.getenv("INFISICAL_CLIENT_ID"),
            client_secret=os.getenv("INFISICAL_CLIENT_SECRET")
        ))

        # Replace 'your-project-id' with your actual Infisical Project ID
        secret = self.client.get_secret(options=GetSecretOptions(
            secret_name="GEMINI_API_KEY",
            project_id="3c86141a-da90-4e92-8af1-bdd868890585",
            environment="dev"
        ))

        self.GEMINI_API_KEY = secret.secret_value


# Create a single instance to be imported elsewhere
settings = Settings()