import re
from django import template

register = template.Library()

@register.filter
def drive_url(url):
    """
    Converts Google Drive share URL to direct image URL.
    Input:  https://drive.google.com/file/d/FILE_ID/view?...
    Output: https://drive.google.com/uc?export=view&id=FILE_ID
    """
    if not url:
        return url
    match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
    if match:
        file_id = match.group(1)
        return f'https://drive.google.com/uc?export=view&id={file_id}'
    return url
