import re
from django import template

register = template.Library()

@register.filter
def extract_youtube_id(value):
    """
    Extracts the YouTube ID from various YouTube URL formats.
    If it's already an ID, returns it as is.
    """
    if not value:
        return ''
    
    value = str(value).strip()
    
    # Regex to match youtube URLs and extract the 11-character video ID
    pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, value)
    
    if match:
        return match.group(1)
        
    # If the input itself looks like an 11-character ID
    if len(value) == 11 and re.match(r'^[a-zA-Z0-9_-]{11}$', value):
        return value
        
    return value
