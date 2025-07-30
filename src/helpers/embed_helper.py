def create_success_embed(title, description, fields=None):
    
    embed = {
        "color": 0x00ff00,  # Green color for success
        "title": f"✅ {title}",
        "description": description,
        "footer": {
            "text": "🤖 ResuRalph by @Lenny"
        }
    }
    
    if fields:
        embed["fields"] = fields
    
    return {"embeds": [embed]}


def create_error_embed(title, description, fields=None):
    
    embed = {
        "color": 0xff0000,  # Red color for error
        "title": f"❌ {title}",
        "description": description,
        "footer": {
            "text": "🤖 ResuRalph by @Lenny"
        }
    }
    
    if fields:
        embed["fields"] = fields
    
    return {"embeds": [embed]}


def create_info_embed(title, description, fields=None):
    
    embed = {
        "color": 0x0099ff,  # Blue color for info
        "title": f"📝 {title}",
        "description": description,
        "footer": {
            "text": "🤖 ResuRalph by @Lenny"
        }
    }
    
    if fields:
        embed["fields"] = fields
    
    return {"embeds": [embed]}


def create_warning_embed(title, description, fields=None):
    
    embed = {
        "color": 0xff9900,  # Orange color for warning
        "title": f"⚠️ {title}",
        "description": description,
        "footer": {
            "text": "🤖 ResuRalph by @Lenny"
        }
    }
    
    if fields:
        embed["fields"] = fields
    
    return {"embeds": [embed]}