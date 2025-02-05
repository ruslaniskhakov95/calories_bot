import logging
import os

from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

BOT_TOKEN = os.getenv('TLG_TOKEN')

if not BOT_TOKEN:
    raise NotImplementedError('No bot connected!')
