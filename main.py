from functools import wraps
import os

import openai
from openai import OpenAI

from validate import StoryRating

"""
If I had more time, I would do the following:
-write tests
-refactor the num attempts code into a helper function with retry logic, so that I could re-use it
-add more types

"""

MAX_TOKENS = 3000
TEMPERATURE = 0.1
openai.api_key = os.getenv("OPENAI_API_KEY")


def get_completion(content: str, description=None, parameters=None) -> str:

    client = OpenAI()
    tools = None
    tool_choice = None
    if parameters is not None and description is not None:
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "Requirements",
                    "description": description,
                    "parameters": parameters.model_json_schema(),
                },
            }
        ]
        tool_choice = {
            "type": "function",
            "function": {"name": "Requirements"},
        }

    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": content}],
        stream=False,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        tools=tools,
        tool_choice=tool_choice,
    )
    if parameters:
        return parameters.model_validate_json(
            resp.choices[0].message.tool_calls[0].function.arguments
        )
    else:
        return resp.choices[0].message.content


def call_model(prompt: str) -> str:
    return get_completion(f"Tell a story for ages 5 to 10 using this prompt: {prompt}")


def call_judge(story: str) -> str:
    completion = get_completion(
        f"Return adequate or inadequate based on appropriateness of the story for ages 5 to 10: {story}",
        "A one word rating",
        StoryRating,
    )
    return completion.rating


def edit_story(story, prompt: str) -> str:
    completion = get_completion(
        f"Please modify {story} with the user requests: {prompt}"
    )
    return completion


def tell_a_story(user_input):
    story_judgement = "inadequate"
    new_story_judgement = "inadequate"

    num_attempts = 0
    while story_judgement == "inadequate":
        num_attempts += 1
        if num_attempts > 5:
            raise Exception("Could not tell an appropriate story.")

        story = call_model(user_input)

        story_judgement = judge(story)

    num_attempts = 0
    while new_story_judgement == "inadequate":
        num_attempts += 1
        new_story, new_story_judgement = modify_story(story)

        if num_attempts > 5:
            raise Exception("Could not tell an appropriate story.")

        story = new_story

    print(f"Here is the final story: {new_story}")


def main():
    user_input = input("What kind of story do you want to hear? ")
    return tell_a_story(user_input)


def judge(story):
    assessment = call_judge(story)
    return assessment


def modify_story(original_story):
    print(f"Here is the proposed story: {original_story}")
    user_input = input(
        "Are there any edits to the story that you'd like to request? Leave blank if not. "
    )

    if user_input:
        new_story = edit_story(original_story, user_input)
        return new_story, judge(new_story)
    else:
        return original_story, "adequate"


if __name__ == "__main__":
    main()
