import asyncio
import signal
import argparse
import os
import requests
from urllib.parse import urlparse


class WebDownloader:
    def __init__(self, max_concurrent_downloads=3):
        self.max_concurrent_downloads = max_concurrent_downloads
        self.downloads = asyncio.Queue()
        self.active_downloads = []

    async def download(self, dl):
        url, download_dir = dl
        # Set default download directory to current working directory
        download_dir = download_dir or os.getcwd()

        # Parse the URL to get the filename
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)

        # Create the download directory if it does not exist
        os.makedirs(download_dir, exist_ok=True)

        # Send the request and download the file
        response = requests.get(url, stream=True)
        with open(os.path.join(download_dir, filename), "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)

        return dl

    async def queue_download(self, url, download_dir=None):
        await self.downloads.put((url, download_dir))

    async def _start_downloads(self):
        while len(self.active_downloads) < self.max_concurrent_downloads and not self.downloads.empty():
            dl = await self.downloads.get()
            download_task = asyncio.ensure_future(self.download(dl))
            self.active_downloads.append(download_task)
            download_task.add_done_callback(self._on_download_complete)

    def _on_download_complete(self, task):
        result = task.result()
        self.active_downloads.remove(task)

    def is_idle(self):
        print(f"Active downloads: {len(self.active_downloads)}, Queued downloads: {self.downloads.qsize()}")
        return len(self.active_downloads) == 0 and self.downloads.empty()


async def asy_main(args):
    try:
        downloader = WebDownloader(max_concurrent_downloads=args.concurrency)
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, downloader.is_idle)

        for url in args.urls:
            await downloader.queue_download(url, args.output)

        await downloader._start_downloads()

        while not downloader.is_idle():
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        pass

    finally:
        loop.remove_signal_handler(signal.SIGINT)



def main():
    parser = argparse.ArgumentParser(description="Asynchronous web downloader")
    parser.add_argument("urls", nargs="*", default=[], help="List of URLs to download")
    parser.add_argument("-f", "--file", default=None, help="File containing list of URLs to download")
    parser.add_argument("-o", "--output", default=None, help="Output directory")
    parser.add_argument("-c", "--concurrency", type=int, default=3, help="Maximum concurrent downloads")

    args = parser.parse_args()

    if not args.urls and not args.file:
        print("Please provide either a list of URLs or a file containing URLs.")
        exit(1)

    if args.file:
        with open(args.file, "r") as f:
            urls_from_file = f.read().splitlines()
        args.urls.extend(urls_from_file)

    asyncio.run(asy_main(args))

