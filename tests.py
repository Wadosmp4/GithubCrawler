import unittest
from unittest.mock import patch

from crawler import (request_html, fetch_github_links, fetch_extra_github_information,
                     extract_link_from_resource, process_wikis_body)


GITHUB_REPOSITORY_INFORMATION = b"""<ul class="list-style-none">
    <li class="d-inline">
        <a class="d-inline-flex flex-items-center flex-nowrap Link--secondary no-underline text-small mr-3" data-ga-click="Repository, language stats search click, location:repo overview" href="/atuldjadhav/DropBox-Cloud-Storage/search?l=css">
          <svg aria-hidden="true" class="octicon octicon-dot-fill mr-2" data-view-component="true" height="16" style="color:#563d7c;" version="1.1" viewBox="0 0 16 16" width="16">
    <path d="M8 4a4 4 0 1 1 0 8 4 4 0 0 1 0-8Z"></path>
</svg>
          <span class="color-fg-default text-bold mr-1">CSS</span>
          <span>52.0%</span>
        </a>
    </li>
    <li class="d-inline">
        <a class="d-inline-flex flex-items-center flex-nowrap Link--secondary no-underline text-small mr-3" data-ga-click="Repository, language stats search click, location:repo overview" href="/atuldjadhav/DropBox-Cloud-Storage/search?l=javascript">
          <svg aria-hidden="true" class="octicon octicon-dot-fill mr-2" data-view-component="true" height="16" style="color:#f1e05a;" version="1.1" viewBox="0 0 16 16" width="16">
    <path d="M8 4a4 4 0 1 1 0 8 4 4 0 0 1 0-8Z"></path>
</svg>
          <span class="color-fg-default text-bold mr-1">JavaScript</span>
          <span>47.2%</span>
        </a>
    </li>
    <li class="d-inline">
        <a class="d-inline-flex flex-items-center flex-nowrap Link--secondary no-underline text-small mr-3" data-ga-click="Repository, language stats search click, location:repo overview" href="/atuldjadhav/DropBox-Cloud-Storage/search?l=html">
          <svg aria-hidden="true" class="octicon octicon-dot-fill mr-2" data-view-component="true" height="16" style="color:#e34c26;" version="1.1" viewBox="0 0 16 16" width="16">
    <path d="M8 4a4 4 0 1 1 0 8 4 4 0 0 1 0-8Z"></path>
</svg>
          <span class="color-fg-default text-bold mr-1">HTML</span>
          <span>0.8%</span>
        </a>
    </li>
</ul>"""

GITHUB_REPOSITORY_LIST = b"""<body>{"payload": {"results": [{"id": "55005225", "archived": false, "color": "#563d7c", "followers": 0, "has_funding_file": false, "hl_name": "atuldjadhav/DropBox-Cloud-Storage", "hl_trunc_description": "Technologies:- Openstack NOVA, NEUTRON, SWIFT, CINDER API's, JAVA, JAX-RS, MAVEN, JSON, HTML5, CSS, JAVASCRIPT, ANGULARJS", "language": "CSS", "mirror": false, "owned_by_organization": false, "public": true, "repo": {"repository": {"id": 55005225, "name": "DropBox-Cloud-Storage", "owner_id": 17938694, "owner_login": "atuldjadhav", "updated_at": "2016-03-29T19:40:33.966Z", "has_issues": true}}, "sponsorable": false, "topics": [], "type": "Public", "help_wanted_issues_count": 0, "good_first_issue_issues_count": 0, "starred_by_current_user": false}]}}</body>"""

WIKIS_RESPONSE = """{"payload":{"header_redesign_enabled":false,"results":[{"body":"football data api をローカルでテスト実行したいとき import http.client\nimport json def fetch_api_data():\ntry:\nconnection = http.client.HTTPConnection('api.football-data.org')\nheaders = { 'X-Auth-Token': 'API キー' }\nconnection.request('GET', '/v4/competitions/PL/teams', None, headers)\nresponse = json.loads(connection.getresponse().read().decode())\nreturn response\nexcept Exception as e:\nprint(f\"Error occurred while fetching data from API: {e}\")\nreturn None data = fetch_api_data()\nif data is not None:\nprint(json.dumps(data, indent=4))","filename":"Python(Django).md","format":"markdown","hl_body":"football data api をローカルでテスト実行したいとき import http.client\nimport json def fetch_api_data():\ntry:\nconnection = http.client.HTTPConnection('api.football-data.org')\nheaders = { 'X-Auth-Token': ...","hl_title":"Python(Django)","id":"19a3d5048458b7a2a41158a807746b8d7ca9bfe2","path":"Python(Django).md","public":true,"repo":{"repository":{"id":672209564,"name":"PostMatch","owner_id":132193935,"owner_login":"Kota-Oshiro","updated_at":"2023-10-10T09:28:59.270Z","has_issues":true}},"repo_id":672209564,"title":"Python(Django)","updated_at":"2023-07-30T17:30:30.000+09:00"}"""
WIKIS_PROCESSED_RESPONSE = """{"payload":{"header_redesign_enabled":false,"results":[{"filename":"Python(Django).md","format":"markdown","hl_title":"Python(Django)","id":"19a3d5048458b7a2a41158a807746b8d7ca9bfe2","path":"Python(Django).md","public":true,"repo":{"repository":{"id":672209564,"name":"PostMatch","owner_id":132193935,"owner_login":"Kota-Oshiro","updated_at":"2023-10-10T09:28:59.270Z","has_issues":true}},"repo_id":672209564,"title":"Python(Django)","updated_at":"2023-07-30T17:30:30.000+09:00"}"""


class AsyncSession:
    def __init__(self, responses):
        self.responses = responses

    def get(self, *args, **kwargs):
        return self.responses.pop(0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return self


class AsyncResponse:
    def __init__(self, status, value):
        self.status = status
        self.value = value

    async def read(self, *args):
        return self.value

    async def __aenter__(self, *args):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return self


class TestGitHubScraper(unittest.IsolatedAsyncioTestCase):

    async def test_request_html_success(self):
        mock_response = AsyncResponse(200, b"Mock HTML Content")

        mock_session = AsyncSession(responses=[mock_response])

        html_content = await request_html(mock_session, "path", ["proxy1", "proxy2"])

        self.assertEqual(html_content, b"Mock HTML Content")

    async def test_request_html_failure(self):
        mock_response = AsyncResponse(500, b"Mock HTML Content")

        mock_session = AsyncSession(responses=[mock_response])

        html_content = await request_html(mock_session, "path", ["proxy1", "proxy2"])

        self.assertIsNone(html_content)

    async def test_fetch_extra_github_information_no_data(self):
        mock_response = AsyncResponse(200, b"<html>Mock HTML Content</html>")

        mock_session = AsyncSession(responses=[mock_response])

        result = await fetch_extra_github_information(mock_session, "path", ["proxy1", "proxy2"])

        expected_result = {
            "link": "https://github.com/path",
            "extra": {
                "owner": "path",
                "language_stats": {}
            }
        }

        self.assertEqual(result, expected_result)

    async def test_fetch_extra_github_information_with_data(self):
        mock_response = AsyncResponse(200, GITHUB_REPOSITORY_INFORMATION)

        mock_session = AsyncSession(responses=[mock_response])

        result = await fetch_extra_github_information(mock_session, "path", ["proxy1", "proxy2"])

        expected_result = {
            "link": "https://github.com/path",
            "extra": {
                "owner": "path",
                "language_stats": {'CSS': 52.0, 'HTML': 0.8, 'JavaScript': 47.2}
            }
        }

        self.assertEqual(result, expected_result)

    @patch("crawler.aiohttp.ClientSession")
    async def test_fetch_github_links_no_data(self, mock_session):
        mock_response = AsyncResponse(200, b'<body>{"test": "Mock HTML Content"}</body>')

        mock_session.return_value = AsyncSession(responses=[mock_response])

        result = await fetch_github_links({
            "keywords": [
                "openstack",
                "nova",
                "css"
            ],
            "proxies": [
                "194.126.37.94:8080",
                "13.78.125.167:8080"
            ],
            "type": "Repositories"
        })

        expected_result = []

        self.assertEqual(result, expected_result)

    @patch("crawler.aiohttp.ClientSession")
    async def test_fetch_github_links_with_data(self, mock_session):
        mock_links_response = AsyncResponse(200, GITHUB_REPOSITORY_LIST)
        mock_repository_response = AsyncResponse(200, GITHUB_REPOSITORY_INFORMATION)

        mock_session.return_value = AsyncSession(responses=[mock_links_response, mock_repository_response])

        result = await fetch_github_links({
            "keywords": [
                "openstack",
                "nova",
                "css"
            ],
            "proxies": [
                "194.126.37.94:8080",
                "13.78.125.167:8080"
            ],
            "type": "Repositories"
        })

        expected_result = [
            {
                'link': 'https://github.com/atuldjadhav/DropBox-Cloud-Storage',
                'extra':
                    {
                        'owner': 'atuldjadhav',
                        'language_stats': {'CSS': 52.0, 'JavaScript': 47.2, 'HTML': 0.8}
                    }
            }
        ]

        self.assertEqual(result, expected_result)

    @patch("crawler.GITHUB_LINK", 'https://github.com')
    async def test_extract_link_from_resource(self):
        data = {
            'repo': {
                'repository': {
                    'name': 'myrepo',
                    'owner_login': 'myuser'
                }
            },
            'number': 42,
            'hl_title': 'MyTitle'
        }

        result = await extract_link_from_resource('Issues', data)

        expected_result = 'https://github.com/myuser/myrepo/issues/42'
        self.assertEqual(result, expected_result)

    @patch("crawler.GITHUB_LINK", 'https://github.com')
    async def test_extract_link_from_resource_no_number(self):
        data = {
            'repo': {
                'repository': {
                    'name': 'myrepo',
                    'owner_login': 'myuser'
                }
            },
            'hl_title': 'MyTitle'
        }

        result = await extract_link_from_resource('Wikis', data)

        expected_result = 'https://github.com/myuser/myrepo/wikis/MyTitle'
        self.assertEqual(result, expected_result)

    async def test_process_wikis_body_no_matches(self):
        input_body = "This is a test body with no matches."
        result = await process_wikis_body(input_body)
        self.assertEqual(result, input_body)

    async def test_process_wikis_body_single_match(self):
        input_body = WIKIS_RESPONSE
        expected_result = WIKIS_PROCESSED_RESPONSE
        result = await process_wikis_body(input_body)
        self.assertEqual(result, expected_result)


if __name__ == "__main__":
    unittest.main()
