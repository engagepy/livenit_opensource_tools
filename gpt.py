import openai

# Awaiting access and full fledged development roadmap

openai.api_key = "<API_KEY_HERE>"


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
