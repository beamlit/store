import asyncio

import requests

from .bl_config import BL_CONFIG


async def retrieve_jwt():
    global BL_CONFIG

    credentials = BL_CONFIG.get('credentials')
    headers = { "Authorization": f"Basic {credentials}" }
    body = { "grant_type": "client_credentials" }
    response = requests.post(f"{BL_CONFIG['base_url']}/oauth/token", headers=headers, json=body)
    if response.status_code == 200:
        content = response.json()
        BL_CONFIG['jwt'] = content.get('access_token')
        BL_CONFIG['jwt_expires_in'] = content.get('expires_in')
    else:
        raise Exception(f"Failed to retrieve JWT, {response.text}")

async def auth():
    # If jwt or api_key is set, we don't need to retrieve jwt dynamically
    if BL_CONFIG.get('jwt') or BL_CONFIG.get('api_key'):
        return
    if BL_CONFIG.get('credentials'):
        await retrieve_jwt()
        return
    raise Exception("No beamlit credentials found, need JWT or API Key or credentials")

async def auth_loop():
    if BL_CONFIG.get('credentials'):
        while True:
            await asyncio.sleep(BL_CONFIG['jwt_expires_in'] - 10)
            await auth()