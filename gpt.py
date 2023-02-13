import os
import openai

# Awaiting access and full fledged development roadmap

openai.api_key = os.environ["openai_key"]

#start = "Your are a AI Search Engine, answer the following query with a witty answer and include validated facts only."

def generate(prompt):
    start_sequence = "{} :: ".format(prompt.capitalize())
    completions = openai.Completion.create(
      model="text-davinci-003",
      prompt=start_sequence,
      temperature=0,
      max_tokens=1111,
      top_p=1,
      frequency_penalty=0.51,
      presence_penalty=0.5,
      #stop_sequence = ["\\n"]
      #stream = False,
      echo = True
    )
          
    
    message = completions.choices[0].text
      
    print(message)
    return message
