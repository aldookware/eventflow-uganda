import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_sms_otp(phone_number, otp_code, purpose):
    """
    Send SMS OTP using Uganda telecom providers
    """
    try:
        # Format phone number for Uganda (+256)
        if not phone_number.startswith('+'):
            if phone_number.startswith('0'):
                phone_number = '+256' + phone_number[1:]
            else:
                phone_number = '+256' + phone_number
        
        # Determine provider based on phone prefix
        provider = get_telecom_provider(phone_number)
        
        message = f"Your EventFlow {purpose} OTP code is: {otp_code}. Valid for 10 minutes. Do not share this code."
        
        if provider == 'mtn':
            return send_mtn_sms(phone_number, message)
        elif provider == 'airtel':
            return send_airtel_sms(phone_number, message)
        else:
            # Fallback to generic SMS service
            return send_generic_sms(phone_number, message)
            
    except Exception as e:
        logger.error(f"SMS sending failed: {e}")
        return False


def get_telecom_provider(phone_number):
    """
    Determine telecom provider based on phone number prefix
    """
    # Remove country code and format
    number = phone_number.replace('+256', '').replace(' ', '')
    
    # MTN prefixes
    mtn_prefixes = ['77', '78', '76']
    # Airtel prefixes  
    airtel_prefixes = ['75', '70', '74']
    # UTL prefixes
    utl_prefixes = ['71', '72']
    # Africell prefixes
    africell_prefixes = ['79']
    
    prefix = number[:2]
    
    if prefix in mtn_prefixes:
        return 'mtn'
    elif prefix in airtel_prefixes:
        return 'airtel'
    elif prefix in utl_prefixes:
        return 'utl'
    elif prefix in africell_prefixes:
        return 'africell'
    else:
        return 'unknown'


def send_mtn_sms(phone_number, message):
    """
    Send SMS via MTN API
    """
    if not settings.MTN_API_KEY:
        logger.warning("MTN API key not configured")
        return mock_sms_send(phone_number, message)
    
    # MTN SMS API implementation
    # This is a placeholder - implement actual MTN API integration
    headers = {
        'Authorization': f'Bearer {settings.MTN_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'to': phone_number,
        'message': message,
        'from': 'EventFlow'
    }
    
    try:
        # Placeholder URL - replace with actual MTN endpoint
        response = requests.post(
            'https://api.mtn.ug/sms/v1/send',
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info(f"SMS sent successfully via MTN to {phone_number}")
            return True
        else:
            logger.error(f"MTN SMS failed: {response.text}")
            return False
            
    except requests.RequestException as e:
        logger.error(f"MTN SMS request failed: {e}")
        return False


def send_airtel_sms(phone_number, message):
    """
    Send SMS via Airtel API
    """
    if not settings.AIRTEL_API_KEY:
        logger.warning("Airtel API key not configured")
        return mock_sms_send(phone_number, message)
    
    # Airtel SMS API implementation
    # This is a placeholder - implement actual Airtel API integration
    headers = {
        'Authorization': f'Bearer {settings.AIRTEL_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'to': phone_number,
        'message': message,
        'sender_id': 'EventFlow'
    }
    
    try:
        # Placeholder URL - replace with actual Airtel endpoint
        response = requests.post(
            'https://api.airtel.ug/sms/v1/send',
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info(f"SMS sent successfully via Airtel to {phone_number}")
            return True
        else:
            logger.error(f"Airtel SMS failed: {response.text}")
            return False
            
    except requests.RequestException as e:
        logger.error(f"Airtel SMS request failed: {e}")
        return False


def send_generic_sms(phone_number, message):
    """
    Send SMS via generic SMS gateway (fallback)
    """
    # This could use services like Twilio, Africa's Talking, etc.
    logger.info(f"Sending generic SMS to {phone_number}")
    return mock_sms_send(phone_number, message)


def mock_sms_send(phone_number, message):
    """
    Mock SMS sending for development
    """
    if settings.DEBUG:
        logger.info(f"[MOCK SMS] To: {phone_number}")
        logger.info(f"[MOCK SMS] Message: {message}")
        return True
    return False


def validate_uganda_phone(phone_number):
    """
    Validate Uganda phone number format
    """
    import re
    
    # Remove spaces and special characters
    clean_number = re.sub(r'[^\d+]', '', phone_number)
    
    # Valid Uganda formats:
    # +256XXXXXXXXX (13 digits total)
    # 0XXXXXXXXX (10 digits)
    # XXXXXXXXX (9 digits)
    
    patterns = [
        r'^\+256[7][0-9]{8}$',  # +256 format
        r'^0[7][0-9]{8}$',      # 0 prefix format  
        r'^[7][0-9]{8}$'        # No prefix format
    ]
    
    for pattern in patterns:
        if re.match(pattern, clean_number):
            return True
    
    return False


def format_uganda_phone(phone_number):
    """
    Format phone number to standard Uganda format (+256XXXXXXXXX)
    """
    import re
    
    # Remove spaces and special characters except +
    clean_number = re.sub(r'[^\d+]', '', phone_number)
    
    # Convert to international format
    if clean_number.startswith('+256'):
        return clean_number
    elif clean_number.startswith('256'):
        return '+' + clean_number
    elif clean_number.startswith('0'):
        return '+256' + clean_number[1:]
    elif len(clean_number) == 9 and clean_number.startswith('7'):
        return '+256' + clean_number
    else:
        raise ValueError("Invalid Uganda phone number format")