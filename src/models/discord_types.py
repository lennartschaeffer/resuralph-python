from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass

@dataclass
class User:
    id: str
    username: str
    discriminator: str
    global_name: Optional[str]
    avatar: Optional[str]
    public_flags: int

@dataclass
class Member:
    user: User
    roles: List[str]
    joined_at: str
    permissions: str
    nick: Optional[str]

@dataclass
class Channel:
    id: str
    name: str
    type: int
    guild_id: str
    permissions: str

@dataclass
class Guild:
    id: str
    locale: str
    features: List[str]

@dataclass 
class CommandOption:
    name: str
    type: int
    value: Union[str, int, bool]

@dataclass
class CommandData:
    id: str
    name: str
    type: int
    options: Optional[List[CommandOption]] = None

@dataclass
class DiscordInteraction:
    id: str
    type: int  # 1=PING, 2=APPLICATION_COMMAND, 3=MESSAGE_COMPONENT
    application_id: str
    token: str
    version: int
    data: Optional[CommandData]
    guild_id: Optional[str]
    channel_id: Optional[str]
    member: Optional[Member]
    user: Optional[User]
    channel: Optional[Channel]
    guild: Optional[Guild]
    locale: Optional[str]
    guild_locale: Optional[str]