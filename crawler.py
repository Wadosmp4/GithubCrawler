import aiohttp
import asyncio
import json
import random

from typing import List, Optional, Dict, Union

from aiohttp import ClientSession
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

WIKIS = "Wikis"
REPOSITORIES = "Repositories"

# keys to remove from wikis response body
WIKIS_BODY = '{"body":'
WIKIS_FILENAME = '"filename":'
WIKIS_HL_BODY = '"hl_body":'
WIKIS_HL_TITLE = '"hl_title":'


async def process_wikis_body(body: str) -> str:
    """We need to process additionally response with Wikis
       because it has code samples that cannot be cast to json"""
    body_index = 0
    while (new_index := body.find(WIKIS_BODY, body_index)) != -1:
        # removing part with programming code in body
        filename_index = body.find(WIKIS_FILENAME, body_index)
        body = body[:new_index] + "{" + body[filename_index:]

        # removing part with programming code in hl_body
        hl_body_index = body.find(WIKIS_HL_BODY, body_index)
        hl_title_index = body.find(WIKIS_HL_TITLE, hl_body_index)
        body = body[:hl_body_index] + body[hl_title_index:]

        body_index = new_index + 2

    return body


async def extract_link_from_resource(data_type: str, obj: Dict[str, Union[str, List, Dict]]):
    repository = obj.get('repo').get('repository')
    repo_name = repository.get('name')
    repo_owner = repository.get('owner_login')
    repo_number = obj.get('number') or obj.get('hl_title')

    return f'{GITHUB_LINK}/{repo_owner}/{repo_name}/{data_type.lower()}/{repo_number}'


async def request_html(session: ClientSession, path: str, proxies: List[str]) -> Optional[bytes]:
    proxy = PROXY.format(random.choice(proxies))
    async with session.get(f"/{path}") as response:
        if response.status == 200:
            return await response.read()
        print(f"Failed to retrieve data. Status code: {response.status}")
        return None


async def fetch_github_links(input_info: Dict[str, Union[str, List[str]]]) -> List[Dict[str, str]]:
    proxies = input_info["proxies"]

    data_type = input_info["type"]
    search_url = SEARCH_PATH.format(keywords='+'.join(input_info["keywords"]),
                                    resource_type=data_type)

    timeout = aiohttp.ClientTimeout(total=30)
    try:
        async with aiohttp.ClientSession(base_url=GITHUB_LINK, timeout=timeout) as session:
            html = await request_html(session, search_url, proxies)
            soup = BeautifulSoup(html.decode(ENCODING), HTML_PARSER)
            body = soup.find(BODY).text
            if data_type == WIKIS:
                body = await process_wikis_body(body)

            json_object = json.loads(body)

            result = []
            objects = json_object.get('payload', {}).get('results', [])
            if data_type == REPOSITORIES:
                tasks = []
                for obj in objects:
                    task = asyncio.create_task(
                        fetch_extra_github_information(session, obj.get(GITHUB_PAGE_URL_PATH), proxies)
                    )
                    tasks.append(task)
                result.extend(await asyncio.gather(*tasks))
            else:
                for obj in objects:
                    result.append({'url': await extract_link_from_resource(data_type, obj)})
            return result

    except Exception as e:
        print(f"An error occurred: {type(e), str(e)}")
        return []


async def fetch_extra_github_information(session: ClientSession, path: str, proxies: List[str]) -> Dict[str, str]:
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
