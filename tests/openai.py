import copy
import uuid

from pathlib import Path

from curl_cffi import requests
from tclogger import logger, OSEnver

secrets_path = Path(__file__).parents[1] / "secrets.json"
ENVER = OSEnver(secrets_path)


class OpenaiAPI:
    def __init__(self):
        self.init_requests_params()

    def init_requests_params(self):
        self.api_base = "https://chat.openai.com/backend-anon"
        self.api_me = f"{self.api_base}/me"
        self.api_models = f"{self.api_base}/models"
        self.api_chat_requirements = f"{self.api_base}/sentinel/chat-requirements"
        self.api_conversation = f"{self.api_base}/conversation"
        self.uuid = str(uuid.uuid4())
        self.requests_headers = {
            # "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "Oai-Device-Id": self.uuid,
            "Oai-Language": "en-US",
            "Pragma": "no-cache",
            "Referer": "https://chat.openai.com/",
            "Sec-Ch-Ua": 'Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        }

        http_proxy = ENVER["http_proxy"]
        if http_proxy:
            self.requests_proxies = {
                "http": http_proxy,
                "https": http_proxy,
            }
        else:
            self.requests_proxies = None

    def log_request(self, url, method="GET"):
        if ENVER["http_proxy"]:
            logger.note(f"> Using Proxy:", end=" ")
            logger.mesg(f"{ENVER['http_proxy']}")
        logger.note(f"> {method}:", end=" ")
        logger.mesg(f"{url}", end=" ")

    def log_response(self, res: requests.Response, stream=False):
        status_code = res.status_code
        status_code_str = f"[{status_code}]"

        if status_code == 200:
            logger_func = logger.success
        else:
            logger_func = logger.warn
        logger_func(status_code_str)

        if stream:
            logger_func(res.text)
        else:
            logger_func(res.json())

    def get_models(self):
        self.log_request(self.api_models)
        res = requests.get(
            self.api_models,
            headers=self.requests_headers,
            proxies=self.requests_proxies,
            timeout=10,
            impersonate="chrome120",
        )
        self.log_response(res)

    def auth(self):
        self.log_request(self.api_chat_requirements, method="POST")
        res = requests.post(
            self.api_chat_requirements,
            headers=self.requests_headers,
            proxies=self.requests_proxies,
            timeout=10,
            impersonate="chrome120",
        )
        self.chat_requirements_token = res.json()["token"]
        self.log_response(res)

    def chat_completions(self, prompt: str):
        new_headers = {
            "Accept": "text/event-stream",
            "Openai-Sentinel-Chat-Requirements-Token": self.chat_requirements_token,
        }
        requests_headers = copy.deepcopy(self.requests_headers)
        requests_headers.update(new_headers)
        post_data = {
            "action": "next",
            "messages": [
                {
                    "id": self.uuid,
                    "author": {"role": "user"},
                    "content": {"content_type": "text", "parts": [prompt]},
                    "metadata": {},
                }
            ],
            "parent_message_id": str(uuid.uuid4()),
            "model": "text-davinci-002-render-sha",
            "timezone_offset_min": -480,
            "suggestions": [],
            "history_and_training_disabled": False,
            "conversation_mode": {"kind": "primary_assistant"},
            "force_paragen": False,
            "force_paragen_model_slug": "",
            "force_nulligen": False,
            "force_rate_limit": False,
            "websocket_request_id": str(uuid.uuid4()),
        }
        self.log_request(self.api_conversation, method="POST")
        res = requests.post(
            self.api_conversation,
            headers=requests_headers,
            json=post_data,
            proxies=self.requests_proxies,
            timeout=10,
            impersonate="chrome120",
        )
        self.log_response(res, stream=True)


if __name__ == "__main__":
    api = OpenaiAPI()
    # api.get_models()
    api.auth()
    prompt = "who are you?"
    api.chat_completions(prompt)

    # python -m tests.openai