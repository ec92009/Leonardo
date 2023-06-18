# !pip install python-dotenv    # https://pypi.org/project/python-dotenv/
from dotenv import dotenv_values
import openai   # https://pypi.org/project/openai/
# pip install openai
import json  # https://docs.python.org/3/library/json.html


config = dotenv_values(".env")
openai.api_key = config["OPENAI_KEY"]


def pizza_info(pizza_style, quantity):
    struct1 = {
        "name": pizza_style,
        "price": float(quantity) * 10.99,
    }
    if pizza_style.lower() == "mushroom":
        struct1["price"] = float(quantity) * 9.99

    return json.dumps(struct1)


def salad_info(salad_name, quantity):
    struct1 = {
        "name": salad_name,
        "price": float(quantity) * 4.95,
    }
    if salad_name.lower() == "caesar":
        struct1["price"] = float(quantity) * 6.49

    return json.dumps(struct1)


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
                        "quantity": {
                            "type": "number",
                            "description": "Number of pizzas to get price about, e.g. 3",
                        },
                    },
                    "required": ["pizza_name", "quantity"],
                }
            },
            {
                "name": "get_salad_info",
                "description": "Get various info about salads, including price.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "salad_name": {
                            "type": "string",
                            "description": "The name of the salad to get info about, e.g. \"caesar\".",
                        },
                        "quantity": {
                            "type": "number",
                            "description": "Number of salads to get price about, e.g. 3",
                        },
                    },
                    "required": ["salad_name", "quantity"],
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
        amount = arguments.get("quantity")
        if function_name == "get_pizza_info":
            pizza_name = arguments.get("pizza_name")
            function_response = pizza_info(
                pizza_style=pizza_name,
                quantity=amount
            )
            # print(f'function_response = {function_response}')
        else:
            salad_name = arguments.get("salad_name")
            function_response = salad_info(
                salad_name=salad_name,
                quantity=amount
            )
            # print(f'function_response = {function_response}')

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
        return f'(Function) {second_response["choices"][0]["message"]["content"]}'

    return "(Direct) "+message["content"]


for prompt in [
    "What is the capital of Sweden? Of France?, Of Spain?",
    "Price for 3 salmon pizzas? For 2 caesar salads?",
    "Price for 2 caesar salads? For 3 salmon pizzas?",
    "What's the cost for 4 shrimp salads?",
    "In great detail, calculate the price for 3 salmon pizzas plus a mushroom salad?",
    "How to calculate the cost of two items? Be brief.",
    # "How expensive is a pepperoni pizza?",
    # "How much for two four cheese pizzas?",
    # "The cost of a mushroom pizza is $12.99. Calculate the cost of 2 pepperoni pizzas. What is the total for all the pizzas?"
]:
    output = run_conversation(prompt)
    print(f'Q: {prompt}\nA: {output}\n')
