import os
import logging
from langchain.chat_models import init_chat_model

logger = logging.getLogger(__name__)

class LLMAccessProvider:
    def __init__(self):
        self.llm_model = None
    
    def _map_model_name(self, model_name, use_openrouter=False):
        # Map the following to model IDs from the providers
        if use_openrouter:
            model_mapping = {
                "Google Gemini 3.0 Flash Preview": ("google/gemini-3-flash-preview", "openrouter"),
                "Google Gemini 3.0 Pro": ("google/gemini-3-pro-preview", "openrouter"),
                "Anthropic Claude 4.5 Sonnet": ("anthropic/claude-sonnet-4.5", "openrouter"),
                "Anthropic Claude 4.5 Opus": ("anthropic/claude-opus-4.5", "openrouter"),
                "OpenAI GPT-5": ("openai/gpt-5", "openrouter"),
                "OpenAI GPT-5.2": ("openai/gpt-5.2", "openrouter"),
            }
        else:
            model_mapping = {
                "Google Gemini 3.0 Flash Preview": ("gemini-3-flash-preview", "google_genai"),
                "Google Gemini 3.0 Pro": ("gemini-3-pro-preview", "google_genai"),
                "Anthropic Claude 4.5 Sonnet": ("claude-sonnet-4-5", "anthropic"),
                "Anthropic Claude 4.5 Opus": ("claude-opus-4-5", "anthropic"),
                "OpenAI GPT-5": ("gpt-5", "openai"),
                "OpenAI GPT-5.2": ("gpt-5.2", "openai"),
            }
        return model_mapping.get(model_name)

    def set_llm_model(self, model_name=None,model_name_technical=None,model_provider=None, api_key=None, use_openrouter=False):
        if model_name:
            model_name_mapped = self._map_model_name(model_name, use_openrouter=use_openrouter)
            model_provider = model_name_mapped[1] if isinstance(model_name_mapped, tuple) else "google_genai"
            self.model_name, self.model_provider = model_name_mapped if isinstance(model_name_mapped, tuple) else (model_name_mapped, "google_genai")
        else:
            self.model_name = model_name_technical
            self.model_provider = model_provider if model_provider else "google_genai"
        self.api_key = api_key

        try:
            self.llm_model = self.init_llm_model()
            self.llm_model.invoke([{"role": "user", "content": "Test message"}])
            logger.info(f"LLMAccessProvider: Successfully initialized LLM model {self.model_name} from provider {self.model_provider}, using OpenRouter: {use_openrouter}")
        except Exception as e:
            logger.error(f"Error setting LLM model: {e}")
            self.llm_model = None
            return False

        return True
    
    def init_llm_model(self, streaming=True):

        try:
            if self.model_provider == "openrouter":
                return init_chat_model(streaming=streaming, model=self.model_name, base_url="https://openrouter.ai/api/v1", api_key=self.api_key, model_provider="openai")
            elif self.model_provider == "azure_openai":
                openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
                return init_chat_model(streaming=streaming, model=self.model_name, api_key=self.api_key, endpoint=openai_endpoint, model_provider="azure_openai") # Uses Azure OpenAI #  configurable_fields="any"
            elif self.model_provider == "openai":
                return init_chat_model(streaming=streaming, model=self.model_name, api_key=self.api_key, model_provider="openai") 
            elif self.model_provider == "google_genai":
                return init_chat_model(
                    streaming=streaming, model=self.model_name, api_key=self.api_key, 
                    model_provider="google_genai", include_thoughts=False, thinking_level="low")
            elif self.model_provider == "anthropic":
                return init_chat_model(streaming=streaming, model=self.model_name, api_key=self.api_key, model_provider="anthropic")
            else:
                raise ValueError(f"Unsupported model provider: {self.model_provider}")
        except Exception as e:
            logger.error(f"Error initializing LLM model: {e}")
            return None

    def get_llm_model(self, create_new=False, streaming=False):
        if self.llm_model is None or create_new:
            return self.init_llm_model(streaming=streaming)
        return self.llm_model
    
# if __name__ == "__main__":
#     llm_access = LLMAccessProvider()
#     #print(llm_access._map_model_name("Google Gemini 3.0 Flash Preview"))
#     llm_access.set_llm_model(model_name_technical="gemini-3-flash-preview", model_provider="google_genai")
#     model = llm_access.get_llm_model()