# !pip install python-dotenv    # https://pypi.org/project/python-dotenv/
from dotenv import dotenv_values
import openai   # https://pypi.org/project/openai/
# pip install openai
import json  # https://docs.python.org/3/library/json.html


config = dotenv_values(".env")
openai.api_key = config["OPENAI_KEY"]


def get_pizza_info(pizza_name):
    if pizza_name.lower() == "mushroom":
        pizza_info = {
            "name": pizza_name,
            "price": "$10.99",
        }
    else:
        pizza_info = {
            "name": pizza_name,
            "price": "$9.99",
        }
    retval = json.dumps(pizza_info)
    return retval


def run_conversation(query):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=[{"role": "user", "content": query}],
        functions=[
            {
                "name": "get_pizza_info",
                "description": "Get various info about a pizza, including price.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pizza_name": {
                            "type": "string",
                            "description": "The name of the pizza to get info about, e.g. \"pepperoni\".",
                        },
                    },
                    "required": ["pizza_name"],
                }
            }
        ],
        function_call="auto"
    )

    message = response["choices"][0]["message"]
    # print(f'message = {message}')
    if message.get("function_call"):
        function_name = message["function_call"]["name"]
        arguments = json.loads(message["function_call"]["arguments"])
        pizzza_name = arguments.get("pizza_name")
        function_response = get_pizza_info(
            pizza_name=pizzza_name,
        )

        second_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=[
                {"role": "user", "content": query},
                message,
                {
                    "role": "function",
                    "name": function_name,
                    "content": function_response,
                }
            ],

        )
        return second_response["choices"][0]["message"]["content"]

    return message["content"]


for prompt in [
    "What is the capital of Sweden?",
    "What is the price of a mushroom pizza?",
    "How much does it cost for a mushroom pizza and a pepperoni pizza?",
    "How expensive is a pepperoni pizza?",
    "Price for 3 shitakee mushroom pizzas?",
    "How much for 2 hawaian pizzas?"
]:
    output = run_conversation(prompt)
    print(f'Q:{prompt}\nA:{output}')
