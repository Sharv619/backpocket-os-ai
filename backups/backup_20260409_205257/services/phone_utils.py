import re
import logging

logger = logging.getLogger(__name__)

def format_phone_number(phone):
    """Convert any phone format to WhatsApp API format"""
    if not phone:
        return None
        
    # Remove all non-digit characters except + (temporarily)
    clean_phone = re.sub(r'[^\d+]', '', phone)
    
    # Remove + if present
    clean_phone = clean_phone.replace('+', '')
    
    # Ensure it's the right length (Australian numbers are 10 digits)
    if len(clean_phone) == 10:  # 0424180030 format
        formatted = clean_phone + '@s.whatsapp.net'
    elif len(clean_phone) == 11:  # 61424180030 format  
        formatted = clean_phone + '@s.whatsapp.net'
    else:
        logger.warning(f"Unexpected phone length: {clean_phone} (length: {len(clean_phone)})")
        formatted = clean_phone + '@s.whatsapp.net'  # Try anyway
    
    logger.info(f"📱 Formatted '{phone}' → '{formatted}'")
    return formatted