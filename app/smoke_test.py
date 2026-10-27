from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()
llm = init_chat_model("groq:openai/gpt-oss-20b")
print(llm.invoke("Say hello in one line").content)