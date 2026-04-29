import asyncio
from services.background import inbox_polling_loop_once
import logging

logging.basicConfig(level=logging.INFO)
asyncio.run(inbox_polling_loop_once())
