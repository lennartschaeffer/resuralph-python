import requests
import yaml
import dotenv
import os
dotenv.load_dotenv()

TOKEN = os.getenv("DEV_BOT_TOKEN")
APPLICATION_ID = os.getenv("DEV_APPLICATION_ID")
URL = f"https://discord.com/api/v9/applications/{APPLICATION_ID}/commands"

with open("commands/temp_clear_resumes.yaml", "r") as file:
    yaml_content = file.read()

commands = yaml.safe_load(yaml_content)
headers = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}

# Send the POST request for each command
for command in commands:
    response = requests.post(URL, json=command, headers=headers)
    print(response.json())
    command_name = command["name"]
    print(f"Command {command_name} created: {response.status_code}")