import openai

openai.api_key = "YOUR_OPENAI_API_KEY"

def generate():
    prompt = request.form['prompt']
    completions = openai.Completion.create(
        engine="davinci",
        prompt=prompt,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
    )

    message = completions.choices[0].text
    return message
