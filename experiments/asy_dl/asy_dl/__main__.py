import argparse
import asyncio
import os
import aiohttp

from bs4 import BeautifulSoup
from indicator import progress, BrailleLoadingIndicator


def download_file_handler(content):
    soup = BeautifulSoup(content, "html.parser")
    filename = soup.title.string
    with open(f"{filename}.html", "wb") as f:
        f.write(content)


async def download_file(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            content = await response.content.read()
            download_file_handler(content)


# indicator = BrailleLoadingIndicator()
# @progress(indicator)
async def download_batch(batch_urls):
    tasks = []
    for url in batch_urls:
        tasks.append(asyncio.ensure_future(download_file(url)))
    await asyncio.gather(*tasks)


def download_files(url_list_path, batch_size=10):
    with open(url_list_path, "r") as f:
        urls = [url for url in f.read().splitlines() if url]

    # make download directory
    os.makedirs("downloads", exist_ok=True)
    os.chdir("downloads")

    loop = asyncio.get_event_loop()
    try:
        for i in range(0, len(urls), batch_size):
            batch_urls = urls[i : i + batch_size]
            loop.run_until_complete(download_batch(batch_urls))
    finally:
        print("Done!")

    os.chdir("..")


def main():
    parser = argparse.ArgumentParser(description="Async web downloader")
    parser.add_argument(
        "file_path", metavar="FILE", help="Path to file containing URLs"
    )
    parser.add_argument(
        "-b",
        "--batch-size",
        type=int,
        default=10,
        help="Number of files to download in each batch",
    )
    args = parser.parse_args()

    download_files(args.file_path, batch_size=args.batch_size)
