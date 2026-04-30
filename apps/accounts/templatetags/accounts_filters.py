import re
from django import template

register = template.Library()

@register.filter
def drive_url(url):
    if not url:
        return url
    import re
    # Google Drive: /file/d/ID/view
    match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
    if match:
        file_id = match.group(1)
        return f'https://lh3.googleusercontent.com/d/{file_id}'
    # Google Drive: id= parameter
    match2 = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', url)
    if match2:
        file_id = match2.group(1)
        return f'https://lh3.googleusercontent.com/d/{file_id}'
    return url
