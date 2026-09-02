"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

django_asgi_app = get_asgi_application()

# Import FastAPI app
from agent_gateway.main import app as fastapi_app

async def application(scope, receive, send):
    if scope['type'] == 'http':
        if scope['path'].startswith('/api/agents'):
            # Strip the /api/agents prefix before passing to FastAPI
            scope['path'] = scope['path'][len('/api/agents'):]
            if scope['path'] == '':
                scope['path'] = '/'
            await fastapi_app(scope, receive, send)
        else:
            await django_asgi_app(scope, receive, send)
    else:
        await django_asgi_app(scope, receive, send)
