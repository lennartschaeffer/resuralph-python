import os
import logging
from flask import Flask, jsonify, request
from mangum import Mangum
from asgiref.wsgi import WsgiToAsgi
from discord_interactions import verify_key_decorator
from dotenv import load_dotenv
from commands.upload import handle_upload_command
from commands.get_latest_resume import handle_get_latest_resume_command
from commands.update import handle_update_command
from commands.clear_resumes import handle_clear_resumes_command
from commands.get_annotations import handle_get_annotations_command
from helpers.discord_followup import start_async_update_command
from helpers.embed_helper import create_success_embed, create_error_embed, create_info_embed

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
                message_content = create_info_embed(
                    "Hello!",
                    "Hello there! I'm ResuRalph, your resume review assistant. 👋"
                )
            elif command_name == "echo":
                original_message = data["options"][0]["value"]
                message_content = create_info_embed(
                    "Echo Response",
                    f"Echoing: {original_message}"
                )
            elif command_name == "get_latest_resume":
                message_content = handle_get_latest_resume_command(raw_request)
            elif command_name == "upload":
                message_content = handle_upload_command(raw_request)
            elif command_name == "get_annotations":
                response_data_content = handle_get_annotations_command(raw_request)
            elif command_name == "update":
                # Use deferred response for potentially long-running update operations
                response_data = start_async_update_command(raw_request)
            elif command_name == "get_resume_diff":
                message_content = create_info_embed(
                    "Processing",
                    "Getting resume differences..."
                )
            elif command_name == "clear_resumes":
                message_content = handle_clear_resumes_command(raw_request)
            else:
                message_content = create_error_embed(
                    "Command Not Found",
                    f"Command '{command_name}' is not implemented yet."
                )
                logger.warning(f"Unimplemented command: {command_name}")

            # Handle non-update commands with standard response format
            if command_name != "update":
                if command_name == "get_annotations":
                    # get_annotations can return either embeds or plain text content
                    if isinstance(response_data_content, dict) and "embeds" in response_data_content:
                        response_data = {
                            "type": 4,
                            "data": response_data_content,
                        }
                    else:
                        response_data = {
                            "type": 4,
                            "data": {"content": response_data_content},
                        }
                else:
                    # All other commands now return embed format
                    if isinstance(message_content, dict) and "embeds" in message_content:
                        response_data = {
                            "type": 4,
                            "data": message_content,
                        }
                    else:
                        # Fallback for any plain text responses
                        response_data = {
                            "type": 4,
                            "data": {"content": message_content},
                        }
            
            if command_name == "update":
                logger.info(f"Sending deferred response for command '{command_name}'")
            else:
                if command_name == "get_annotations":
                    if isinstance(response_data_content, dict):
                        logger.info(f"Sending embed response for command '{command_name}'")
                    else:
                        logger.info(f"Sending response for command '{command_name}': {len(response_data_content)} characters")
                else:
                    if isinstance(message_content, dict):
                        logger.info(f"Sending embed response for command '{command_name}'")
                    else:
                        logger.info(f"Sending response for command '{command_name}'")

        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"Error processing Discord interaction: {str(e)}")
        error_embed = create_error_embed(
            "Processing Error",
            "An error occurred while processing your request. 😔"
        )
        return jsonify({
            "type": 4,
            "data": error_embed,
        })


if __name__ == "__main__":
    app.run(debug=True, port=8000)