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
from commands.get_resume_diff import handle_get_resume_diff_command
from commands.get_all_resumes import handle_get_all_resumes_command
from commands.ai_review import handle_ai_review_command
from helpers.discord_followup import start_async_command
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
        if raw_request["type"] == 1:
            logger.info("Discord health check received")
            return jsonify({"type": 1})
        
        data = raw_request["data"]
        command_name = data["name"]
        user_id = raw_request.get('member', {}).get('user', {}).get('id', 'unknown')
        logger.info(f"Processing command '{command_name}' for user {user_id}")
        
        response_content = handle_command_routing(command_name, raw_request)
        response_data = format_command_response(command_name, response_content)
        
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

def handle_command_routing(command_name, raw_request):
    # Commands that need async processing
    async_commands = {
        "update": "update",
        "ai_review": "ai_review"
    }
    
    # Regular synchronous commands
    sync_command_handlers = {
        "get_latest_resume": handle_get_latest_resume_command,
        "upload": handle_upload_command,
        "get_annotations": handle_get_annotations_command,
        "clear_resumes": handle_clear_resumes_command,
        "get_resume_diff": handle_get_resume_diff_command,
        "get_all_resumes": handle_get_all_resumes_command,
    }
    
    if command_name in async_commands:
        return start_async_command(raw_request, async_commands[command_name])
    elif command_name in sync_command_handlers:
        return sync_command_handlers[command_name](raw_request)
    else:
        logger.warning(f"Unimplemented command: {command_name}")
        return create_error_embed(
            "Command Not Found",
            f"Command '{command_name}' is not implemented yet."
        )

def format_command_response(command_name, response_content):
    # Async commands return deferred responses that are already formatted
    async_commands = ["update", "ai_review"]
    if command_name in async_commands:
        return response_content # deferred response already handled in async processing

    if isinstance(response_content, dict) and "embeds" in response_content:
        return {"type": 4, "data": response_content}
    else:
        return {"type": 4, "data": {"content": response_content}}

if __name__ == "__main__":
    app.run(debug=True, port=8000)