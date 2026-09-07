import json
import requests

from prompts import SYSTEM_PROMPT
from tools import search_log, read_file, list_files


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5-coder:7b"


def call_llm(messages):

    print("\n----- Sending messages to LLM -----")
    print("Number of messages:", len(messages))

    print("\n----- Conversation sent to LLM -----")

    for index, message in enumerate(messages):

        print(f"\nMessage {index + 1}")
        print("Role:", message["role"])
        print("Content:")
        print(message["content"])

    payload = {
        "model": MODEL,
        "messages": messages,
        "format": "json",
        "stream": False,
    }

    print("\n----- Calling Ollama -----")

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=180,
    )

    response.raise_for_status()

    response_data = response.json()

    content = response_data["message"]["content"]

    print("\nRaw LLM content:")
    print(content)

    return json.loads(content)


# --------------------------------------------------
# CI problem given to the agent
# --------------------------------------------------

problem = """
Investigate this CI failure:

Docker build failed.
COPY failed: requirements.txt not found
"""


# --------------------------------------------------
# Initial conversation
# --------------------------------------------------

messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT,
    },
    {
        "role": "user",
        "content": problem,
    },
]


# Prevent infinite investigation loops
max_steps = 8


# Store tool calls already used
used_tool_calls = []


# --------------------------------------------------
# Agent loop
# --------------------------------------------------

for step in range(max_steps):

    print("\n")
    print("=" * 50)
    print(f"===== Agent step {step + 1} =====")
    print("=" * 50)


    # Ask LLM what to do next
    response = call_llm(messages)


    print("\nLLM decision:")
    print(json.dumps(response, indent=2))


    # Save the LLM's own decision in conversation history
    messages.append(
        {
            "role": "assistant",
            "content": json.dumps(response),
        }
    )

    print("\nAssistant decision added to messages.")
    print("Current number of messages:", len(messages))


    action = response["action"]

    print("\nAction selected by LLM:")
    print(action)


    # --------------------------------------------------
    # Duplicate tool-call detection
    # --------------------------------------------------

    if action != "final":

        arguments = response["arguments"]

        current_call = {
            "action": action,
            "arguments": arguments,
        }

        print("\nCurrent tool call:")
        print(current_call)

        print("\nPreviously used tool calls:")

        if used_tool_calls:

            for previous_call in used_tool_calls:
                print(previous_call)

        else:
            print("None")


        if current_call in used_tool_calls:

            print("\nDuplicate tool call detected:")
            print(current_call)

            duplicate_message = f"""
You already requested this exact tool call:

Action:
{action}

Arguments:
{arguments}

The same action has already been performed.

Use the previous tool result as evidence.

Choose a different investigation step or return final.
"""

            messages.append(
                {
                    "role": "user",
                    "content": duplicate_message,
                }
            )

            print("\nDuplicate warning added to messages.")
            print("Current number of messages:", len(messages))

            print("\nSkipping duplicate tool execution.")

            continue


        print("\nThis is a new tool call.")

        used_tool_calls.append(current_call)

        print("\nTool call added to used_tool_calls:")

        for used_call in used_tool_calls:
            print(used_call)


    # --------------------------------------------------
    # search_log
    # --------------------------------------------------

    if action == "search_log":

        keyword = response["arguments"]["keyword"]

        print("\nLLM requested tool:")
        print("search_log")

        print("\nKeyword:")
        print(keyword)

        print("\nExecuting search_log...")

        tool_result = search_log(keyword)


        print("\nTool result:")

        if tool_result:

            for line in tool_result:
                print(line)

            tool_result_text = "\n".join(tool_result)

        else:

            print("No matching log lines found.")

            tool_result_text = (
                f'No matching log lines found for "{keyword}".'
            )


        tool_message = f"""
Tool executed:

search_log("{keyword}")

Tool result:

{tool_result_text}

This is real evidence returned by the tool.

A search with no matches only means that this log did not
contain that keyword.

It does not prove that an operation succeeded.

Use this evidence to update your hypothesis.

Decide your next action.
"""

        messages.append(
            {
                "role": "user",
                "content": tool_message,
            }
        )

        print("\nsearch_log result added to messages.")
        print("Current number of messages:", len(messages))


    # --------------------------------------------------
    # read_file
    # --------------------------------------------------

    elif action == "read_file":

        path = response["arguments"]["path"]

        print("\nLLM requested tool:")
        print("read_file")

        print("\nPath:")
        print(path)

        print("\nExecuting read_file...")

        tool_result = read_file(path)


        print("\nTool result:")
        print(tool_result)


        tool_message = f"""
Tool executed:

read_file("{path}")

Tool result:

{tool_result}

This is real evidence returned by the tool.

If file contents were successfully returned,
then the file EXISTS in the project.

Do not later claim that the same project file does not exist.

Use this evidence to update your hypothesis.

Decide your next action.
"""

        messages.append(
            {
                "role": "user",
                "content": tool_message,
            }
        )

        print("\nread_file result added to messages.")
        print("Current number of messages:", len(messages))


    # --------------------------------------------------
    # list_files
    # --------------------------------------------------

    elif action == "list_files":

        directory = response["arguments"]["directory"]

        print("\nLLM requested tool:")
        print("list_files")

        print("\nDirectory:")
        print(directory)

        print("\nExecuting list_files...")

        tool_result = list_files(directory)


        print("\nTool result:")

        for item in tool_result:
            print(item)


        tool_result_text = "\n".join(tool_result)


        tool_message = f"""
Tool executed:

list_files("{directory}")

Tool result:

{tool_result_text}

This is real evidence returned by the tool.

Files shown in this result exist in the project.

Use this evidence to update your hypothesis.

Decide your next action.
"""

        messages.append(
            {
                "role": "user",
                "content": tool_message,
            }
        )

        print("\nlist_files result added to messages.")
        print("Current number of messages:", len(messages))


    # --------------------------------------------------
    # final
    # --------------------------------------------------

    elif action == "final":

        print("\n")
        print("=" * 50)
        print("===== FINAL ANSWER =====")
        print("=" * 50)

        print(
            json.dumps(
                response["answer"],
                indent=2,
            )
        )

        print("\nAgent finished successfully.")

        break


    # --------------------------------------------------
    # Unknown action
    # --------------------------------------------------

    else:

        print("\nERROR: Unknown action returned by LLM:")
        print(action)

        break


    # --------------------------------------------------
    # Debug at end of each step
    # --------------------------------------------------

    print("\n----- End of agent step -----")

    print("\nUsed tool calls:")

    for used_call in used_tool_calls:
        print(used_call)

    print("\nTotal messages stored:")
    print(len(messages))


# Runs only if no "break" happened
else:

    print("\n")
    print("=" * 50)
    print("===== AGENT STOPPED =====")
    print("=" * 50)

    print(
        f"Agent reached max_steps={max_steps} "
        "without returning a final answer."
    )