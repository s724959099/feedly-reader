from pyppeteer import launch
from pyquery import PyQuery as pq
import webbrowser
import asyncio
import typing
from util import Ezdict
import os


def get_env_file():
    with open('.env') as f:
        env = f.read()
    dct = dict()
    for line in env.split():
        key, val = line.split('=')
        dct[key.strip()] = val.strip()
    return dct


class FeedlyCralwer:
    def __init__(self):
        self.browser = None
        self.page = None

    async def init_browser(self):
        self.browser = await launch(dict(
            headless=False,
            defaultViewport=None,
            handleSIGINT=False, handleSIGTERM=False, handleSIGHUP=False,
            executablePath=""
        ))
        self.page = await self.browser.newPage()

    async def close_browser(self):
        await self.browser.close()

    async def goto_feedly_index(self):
        await self.page.goto('https://feedly.com/i/welcome/logged-out')

    async def goto_fb_login_page(self):
        await self.page.click('button.LandingHeaderBar__action')
        await self.page.waitForSelector('a.button.facebook')
        await self.page.click('a.button.facebook')

    async def fb_login(self):
        env = get_env_file()
        account = env.get('ACCOUNT')
        password = env.get('PASSWORD')
        await self.page.waitForSelector('#email')
        await self.page.type('#email', account)
        await self.page.type('#pass', password)
        await self.page.click('input[name="login"]')

    async def click_all_page(self):
        await self.page.waitForSelector('div[title="All"]')
        await self.page.click('div[title="All"]')

    async def scroll_page(self):
        await self.page.waitForSelector('#header-title')
        while True:
            await self.page.evaluate("""document.getElementById('feedlyFrame').scrollBy(0,5000);""")
            await asyncio.sleep(2)
            in_end = await self.page.querySelector('button.giant-mark-as-read')
            if in_end:
                break

    async def get_data(self):
        doc = await self.page.content()
        return self.process_raw_doc(doc)

    def process_raw_doc(self, doc: str) -> typing.List:
        dom = pq(doc)
        ret = []
        for el in dom('.entry').items():
            source = el('.meta-column').text()
            popular = el('.span.EntryEngagement').text()
            title = el('.entry__title').text()
            href = el('.entry__title').attr('href')
            summary = el('.summary').text()
            item = Ezdict(
                source=source,
                popular=popular,
                title=title,
                href=href,
                summary=summary
            )
            ret.append(item)
        return ret

    async def get_result(self):
        # todo 耦合怎麼辦 跟進度
        await self.init_browser()
        await self.goto_feedly_index()
        await self.goto_fb_login_page()
        await self.fb_login()
        await self.click_all_page()
        await self.scroll_page()
        return await self.get_data()


if __name__ == '__main__':
    crawler = FeedlyCralwer()
    data = asyncio.run(crawler.get_result())
    print()
