import os
import django
import sys
import json

# Setup Django
sys.path.append(os.path.abspath("backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.test import RequestFactory
from intelligence.views import AgenticChatView
from rest_framework.response import Response

def test_chat(message: str, platform: str = "kinahub"):
    print(f"\n--- Testing message: '{message}' on platform '{platform}' ---")
    factory = RequestFactory()
    
    payload = {
        "messages": [{"role": "user", "content": message}],
        "context": {
            "platform": platform,
            "cart": {"items": []},
            "catalog": []
        }
    }
    
    request = factory.post(
        '/api/ai/chat/',
        data=json.dumps(payload),
        content_type='application/json'
    )
    
    view = AgenticChatView.as_view()
    response = view(request)
    
    if hasattr(response, 'render'):
        response.render()
        
    data = json.loads(response.content)
    
    print(f"Agent routed to: {data.get('agent')}")
    print(f"Response: {data.get('content')}")

if __name__ == "__main__":
    test_chat("Hi, who made this app?")
    test_chat("Show me some rice options")
    test_chat("What is your return policy?")
