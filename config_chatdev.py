"""ChatDev 설정 추가"""

from dataclasses import dataclass, field

@dataclass
class ChatDevConfig:
    """ChatDev GLM API 설정"""
    glm_api_key: str = ""
    glm_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    model: str = "glm-4-plus"
    timeout_seconds: int = 1800
    max_retries: int = 3


# config.py에 추가할 내용
CHATDEV_DATACLASS = '''
@dataclass
class ChatDevConfig:
    """ChatDev GLM API 설정"""
    glm_api_key: str = ""
    glm_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    model: str = "glm-4-plus"
    timeout_seconds: int = 1800
    max_retries: int = 3
'''

CHATDEV_CONFIG_FIELD = '''
    chatdev: ChatDevConfig = field(default_factory=ChatDevConfig)
'''

CHATDEV_LOAD_LOGIC = '''
    if 'chatdev' in resolved:
        config.chatdev = _dict_to_dataclass(ChatDevConfig, resolved['chatdev'])
'''
