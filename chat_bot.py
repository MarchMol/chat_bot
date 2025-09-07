from dotenv import load_dotenv
import os
import requests
import anthropic

# Loading .env
load_dotenv()
MODEL = os.getenv("ANTHROPIC_MODEL") if os.getenv("ANTHROPIC_MODEL") else None
API_KEY = os.getenv("ANTHROPIC_API_KEY") if os.getenv("ANTHROPIC_API_KEY") else None
MAX_TOKENS = 20

# ---- Chat ----- #
class Chat():
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=API_KEY)
        self.test_connection()
        
    def test_connection(self):
        try:
            _ = self.client.messages.create(
                model=MODEL,
                messages=[{"role": "user", "content": [{"type": "text", "text": "hola"}]}],
                max_tokens=1
            )
        except:
            raise("No se pudo establecer conexion con LLM!")
    
    def ask(self, msg):
        parsed_msg = [{"role": "user", "content": [{"type": "text", "text": msg}]}]
        try:
            resp = self.client.messages.create(
                model=MODEL,
                messages=parsed_msg,
                max_tokens=MAX_TOKENS
            )
            return resp.content
        except:
            raise("No se pudo establecer conexion con LLM!")


# ----- Main ----- #
def main():

    chatbot = Chat()
    content = chatbot.ask("Devuelve un emoji de corazon")
    final_text = "".join([c.text for c in content if getattr(c, "type", "") == "text"])
    print(final_text)


if __name__ == "__main__":
    main()
