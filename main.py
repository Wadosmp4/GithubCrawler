import asyncio

from crawler import fetch_github_links


async def main():
    input_info = {
        "keywords": [
            "python",
            "django"
        ],
        "proxies": [
            "194.126.37.94:8080",
            "13.78.125.167:8080"
        ],
        "type": "Repositories"
    }

    github_links = await fetch_github_links(input_info)

    # Print the results
    print(github_links)
    for link in github_links:
        print(f"GitHub Link: {link}")


if __name__ == "__main__":
    asyncio.run(main())
