from langchain.chat_models import init_chat_model

from dotenv import load_dotenv
load_dotenv(override=True)

# Optionally specify the model version
def get_openai_model(model = 'gpt-4.1', azure_openai=False):
    model = init_chat_model(model, model_provider="azure_openai" if azure_openai else None) # Uses Azure OpenAI
    return model

def get_gemini_model(model = 'gemini-3-pro-preview', include_thoughts=False):
    model = init_chat_model(model, model_provider="google_genai", include_thoughts=include_thoughts) # Uses Google Gemini
    return model

# def get_embedding_model():
#     embedding_model = init_embedding_model('text-embedding-3-small')
#     return embedding_model