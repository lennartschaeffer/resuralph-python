import os
import logging
from flask import Flask, jsonify, request
from mangum import Mangum
from asgiref.wsgi import WsgiToAsgi
from discord_interactions import verify_key_decorator
from dotenv import load_dotenv
from commands.upload import handle_upload_command
from commands.get_latest_resume import handle_get_latest_resume_command

# logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

DISCORD_PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY")

app = Flask(__name__)
asgi_app = WsgiToAsgi(app)
handler = Mangum(asgi_app)

@app.route("/", methods=["POST"])
async def interactions():
    raw_request = request.json
    return interact(raw_request)


@verify_key_decorator(DISCORD_PUBLIC_KEY)
def interact(raw_request):
    try:
        if raw_request["type"] == 1:  # discord health check
            logger.info("Discord health check received")
            response_data = {"type": 1} 
        else:
            data = raw_request["data"]
            command_name = data["name"]
            user_id = raw_request.get('member', {}).get('user', {}).get('id', 'unknown')
            logger.info(f"Processing command '{command_name}' for user {user_id}")

            if command_name == "hello":
                message_content = "Hello there!"
            elif command_name == "echo":
                original_message = data["options"][0]["value"]
                message_content = f"Echoing: {original_message}"
            elif command_name == "get_latest_resume":
                message_content = handle_get_latest_resume_command(raw_request)
            elif command_name == "upload":
                message_content = handle_upload_command(raw_request)
            elif command_name == "get_annotations":
                message_content = "Getting annotations for your resume..."
            elif command_name == "update":
                message_content = "Resume updated successfully!"
            elif command_name == "get_resume_diff":
                message_content = "Getting resume differences..."
            else:
                message_content = f"Command '{command_name}' is not implemented yet."
                logger.warning(f"Unimplemented command: {command_name}")

            response_data = {
                "type": 4,
                "data": {"content": message_content},
            }
            
            logger.info(f"Sending response for command '{command_name}': {len(message_content)} characters")

        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"Error processing Discord interaction: {str(e)}")
        return jsonify({
            "type": 4,
            "data": {"content": "An error occurred while processing your request. 😔"},
        })


if __name__ == "__main__":
    app.run(debug=True, port=8000)