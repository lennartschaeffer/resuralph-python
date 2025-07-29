def create_success_embed(title, description, fields=None):
    """
    Create a success embed with green color
    
    Args:
        title (str): Embed title
        description (str): Embed description
        fields (list, optional): List of field dictionaries
        
    Returns:
        dict: Discord embed response data
    """
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
    """
    Create an error embed with red color
    
    Args:
        title (str): Embed title
        description (str): Embed description
        fields (list, optional): List of field dictionaries
        
    Returns:
        dict: Discord embed response data
    """
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
    """
    Create an info embed with blue color
    
    Args:
        title (str): Embed title
        description (str): Embed description
        fields (list, optional): List of field dictionaries
        
    Returns:
        dict: Discord embed response data
    """
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
    """
    Create a warning embed with orange color
    
    Args:
        title (str): Embed title
        description (str): Embed description
        fields (list, optional): List of field dictionaries
        
    Returns:
        dict: Discord embed response data
    """
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