import argparse
from openai import OpenAI
from utils.utils import *

def main(agent_id, data_dir, create_agent, chat):
    # Initialize the OpenAI client
    client = OpenAI()

    # Create a new thread for conversation
    thread = client.beta.threads.create()

    # Retrieve an existing assistant if agent_id is provided
    if agent_id:
        assistant = client.beta.assistants.retrieve(assistant_id=agent_id)
    # Create and retrieve a new assistant if create_agent is True and data_dir is provided
    elif create_agent and data_dir:
        assistant_id = create_assistant(data_dir)
        assistant = client.beta.assistants.retrieve(assistant_id=assistant_id)
    # Raise an error if neither agent_id is provided nor create_agent is True
    else:
        raise ValueError("Either an agent_id must be provided or create_agent must be True.")

    # If chat is enabled, enter the chat loop
    if chat:
        try:
            while True:
                # Get user input
                user_input = input("You: ")

                # Send the message and display the response
                messages = show_json(send_message(user_input, client, thread, assistant))

                # Check if there are messages and display the latest one
                if messages and 'data' in messages and len(messages['data']) > 0:
                    latest_message = messages['data'][0]['content'][0]['text']['value']
                    print("Assistant:", latest_message)
                    
        except KeyboardInterrupt:
            # Exit gracefully on a keyboard interrupt
            print("\nExiting...")

# Entry point of the script
if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Run an assistant agent.")
    parser.add_argument("-a", "--agent_id", type=str, help="The agent ID to use", default=None)
    parser.add_argument("-d", "--data_dir", type=str, help="The data directory", default="./data/txt/")
    parser.add_argument("-c", "--create_agent", type=bool, help="Whether to create a new agent", required=True)
    parser.add_argument("-ch", "--chat", type=bool, help="Do you want to chat?", required=True)

    # Parse arguments
    args = parser.parse_args()

    # Call main function with parsed arguments
    main(args.agent_id, args.data_dir, args.create_agent, args.chat)