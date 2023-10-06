import aiohttp
import asyncio
import json
import random
from bs4 import BeautifulSoup

GITHUB_LINK = "https://github.com"
SEARCH_PATH = "search?q={keywords}&type={resource_type}"
PROXY = "http://{}"

SPAN = "span"
BODY = "body"
LANGUAGES_CLASS = "d-inline-flex flex-items-center flex-nowrap Link--secondary no-underline text-small mr-3"
GITHUB_PAGE_URL_PATH = "hl_name"

ENCODING = "utf-8"
HTML_PARSER = "html5lib"


async def request_html(session, path, proxies):
    proxy = PROXY.format(random.choice(proxies))
    async with session.get(f"/{path}", proxy=proxy) as response:
        if response.status == 200:
            return await response.read()
        print(f"Failed to retrieve data. Status code: {response.status}")
        return None


async def fetch_github_links(input_info):
    proxies = input_info["proxies"]

    search_url = SEARCH_PATH.format(keywords='+'.join(input_info["keywords"]),
                                    resource_type=input_info["type"])

    timeout = aiohttp.ClientTimeout(total=30)
    try:
        async with aiohttp.ClientSession(base_url=GITHUB_LINK, timeout=timeout) as session:
            html = await request_html(session, search_url, proxies)
            soup = BeautifulSoup(html.decode(ENCODING), HTML_PARSER)
            body = soup.find(BODY).text
            json_object = json.loads(body)

            tasks = []
            for obj in json_object.get('payload', {'results': []})['results']:
                task = asyncio.create_task(
                    fetch_extra_github_information(session, obj.get(GITHUB_PAGE_URL_PATH), proxies)
                )
                tasks.append(task)

            result = await asyncio.gather(*tasks)
            return result

    except Exception as e:
        print(f"An error occurred: {type(e), str(e)}")
        return []


async def fetch_extra_github_information(session, path, proxies):
    html = await request_html(session, path, proxies)

    soup = BeautifulSoup(html.decode(ENCODING), HTML_PARSER)
    languages = [[language.text for language in languages.find_all(SPAN)]
                 for languages in soup.find_all(class_=LANGUAGES_CLASS)]

    result = {
        "link": f"{GITHUB_LINK}/{path}",
        "extra": {
            "owner": path.split("/")[0],
            "language_stats": {key: float(value[:-1]) for key, value in languages}
        }
    }

    return result
