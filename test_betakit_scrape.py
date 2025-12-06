import requests
from bs4 import BeautifulSoup

url = "https://betakit.com/schooling-canada-in-faster-ai-adoption/"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.content, "html.parser")

# Remove unwanted elements
for element in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
    element.decompose()

article = soup.find("article")
if article:
    ps = [
        p.get_text().strip()
        for p in article.find_all("p")
        if len(p.get_text().strip()) > 50
    ]
    print(f"Found {len(ps)} paragraphs")
    print("\n\n=====\n\n".join(ps[:10]))
else:
    print("No article element found")
