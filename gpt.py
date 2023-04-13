import os
import openai
from flask import jsonify
import tiktoken
encoding = tiktoken.encoding_for_model("gpt-4")
# Awaiting access and full fledged development roadmap

openai.api_key = os.environ["openai_key"]

#start = "Your are a AI Search Engine, answer the following query with a witty answer and include validated facts only."

conversation_history = []

def reset_history_if_needed():
    global conversation_history

    total_tokens = 0
    for message in conversation_history:
        try:
            tokens = encoding.encode(message["content"])
            total_tokens += len(tokens)
            
        except tiktoken.TokenizerException:
            pass

    if total_tokens > 4000:
        conversation_history.clear()
        conversation_history.append(system_message)
        print("Cleared Conversation History Just Now")

    
    print("Token = " + str(total_tokens))

# Primer prompts
system_message = {
  "role":
  "system",
  "content":
  "You are the most accurate and factual search engine on the internet. You are witty and will not answer any harmful or pornographic questions."
}

conversation_history.extend([
  system_message
])

def generate(prompt):
    global conversation_history
    
    conversation_history.append({"role": "user", "content": prompt})
    completions = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation_history,
        temperature=0,
        top_p=0,
        frequency_penalty=0.7,
        presence_penalty=0.5)
        #stop_sequence = ["\\n"]
        #stream = False,
        

    message = completions.choices[0]['message']['content'].strip()
  
    conversation_history.append({"role": "assistant", "content": message})
  
    reset_history_if_needed()

    return message
