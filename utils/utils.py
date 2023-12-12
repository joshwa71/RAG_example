import time
import json
import os
import mimetypes
from openai import OpenAI

def show_json(obj):
    # Load and return a JSON representation of an object's model dump
    return json.loads(obj.model_dump_json())

def wait_on_run(run, thread, client):
    # Wait until a run is no longer queued or in progress
    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)  # Pause for half a second to prevent overloading
    return run

def embed_files(data_dir, client):
    file_ids = []      # List to store file IDs
    current_list = []  # Current batch of file IDs

    # Walk through the directory tree
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            file_path = os.path.join(root, file)

            # Determine the MIME type of the file
            mime_type, _ = mimetypes.guess_type(file_path)

            # Process only plain text files
            if mime_type == 'text/plain':
                embed_file = client.files.create(
                    file=open(file_path, "rb"),
                    purpose="assistants",
                )
                file_id = embed_file.id  
                current_list.append(file_id)

                # Once we have 20 file IDs, start a new batch
                if len(current_list) == 20:
                    file_ids.append(current_list)
                    current_list = []
            else:
                # Skip unsupported file types
                print(f"Skipping unsupported file type: {file_path}")

    # Add any remaining file IDs
    if current_list:
        file_ids.append(current_list)

    return file_ids

def create_assistant(data_dir="../data/txt/"):
    client = OpenAI()
    file_ids = embed_files(data_dir, client)

    # Create a new assistant with specific instructions and a model
    assistant = client.beta.assistants.create(
        name="Tech expert",
        instructions="You are a customer service assistant for a tech company named PrivacyLabs." +
        "Your purpose is to answer questions about potential tech solutions for customers." + 
        "You have access to a database of information about companies providing technology which may be useful to customers.",
        model="gpt-4-1106-preview",
        )
    
    # Update the assistant with file IDs for data access
    for id_list in file_ids:
        assistant = client.beta.assistants.update(
            assistant_id=assistant.id,
            tools=[{"type": "retrieval"}],
            file_ids=id_list,
        )

    # Save the assistant ID to a file
    file_path = 'assistant_id.txt'
    with open(file_path, 'w') as file:
        file.write(assistant.id)

    return assistant.id

def send_message(query, client, thread, assistant):
    # Send a query to the assistant
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=query,
    )

    # Create and wait for the run to complete
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )
    run = wait_on_run(run, thread, client)

    # Retrieve and return the list of messages in the thread
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    return messages
