from typing import List, Tuple
import re
import requests
from alive_progress import alive_bar


def extract_links_with_titles(md_content: str) -> List:
    links = []

    url_pattern = r'https?://[^\s\)<>\[\]"\']+[^\s\)<>\[\]"\'\.,;:]'
    for match in re.finditer(url_pattern, md_content):
        url = match.group(0)

        already_exists = any(link == url for link in links)
        if not already_exists:
            links.append(url)

    seen = set()
    unique_links = []
    for link in links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)

    return unique_links


def check_url(url: str, timeout: int = 5) -> Tuple[str, int, str]:
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        status_code = response.status_code

        if status_code == 200:
            return url, status_code, "OK"
        elif 300 <= status_code < 400:
            return url, status_code, f"Redirect ({status_code})"
        elif 400 <= status_code < 500:
            return url, status_code, f"Not Found ({status_code})"
        else:
            return url, status_code, f"Server Error ({status_code})"
    except requests.exceptions.Timeout:
        return url, 0, "Timeout"
    except requests.exceptions.ConnectionError:
        return url, 0, "Connection Error"
    except requests.exceptions.RequestException:
        return url, 0, "Error"
    except Exception:
        return url, 0, "Unknown Error"


f = open("readme.md", "r")
content = f.read()
f.close()

links = extract_links_with_titles(content)
dead_links: List[str] = []

with alive_bar(len(links), title="Checking dead links") as bar:
    for link in links:
        response = check_url(link)

        if response[1] > 399 or response[1] == 0:
            dead_links.append(response[0])
        bar()

new_content = ""

print(dead_links)

for line in content.splitlines():
    if not any(s in line for s in dead_links):
        new_content += line + "\n"


with open("readme.md", "w") as f:
    f.write(new_content)
