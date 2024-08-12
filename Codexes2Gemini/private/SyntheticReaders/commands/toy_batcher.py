import json
from os import environ as osenv

import openai

openai.api_key = osenv['OPENAI_API_KEY']

promptsArray = ["Hello world, from", "How are you B", "I am fine. W", "The  fifth planet from the Sun is "]

stringifiedPromptsArray = json.dumps(promptsArray)

print(promptsArray)
preprompt = [{"role": "system", "content": "Speak in French."}]
print(preprompt)
prompts = [
    {
        "role": "user",
        "content": stringifiedPromptsArray
    }
]

batchInstruction = {
    "role":
        "system",
    "content":
        "Complete every element of the array. Reply with an array of all completions."
}

prompts.append(batchInstruction)
# insert variable at beginning of prompts
system = {"role": "system", "content": "Speak in French."}
prompts.insert(0, system)
print('promptsubmit', prompts)
print("ChatGPT: ")
stringifiedBatchCompletion = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                                          messages=prompts,
                                                          max_tokens=1000)
batchCompletion = json.loads(stringifiedBatchCompletion.choices[0].message.content)
print(batchCompletion)