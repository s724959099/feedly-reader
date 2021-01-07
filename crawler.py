from pyppeteer import launch
from pyquery import PyQuery as pq
import webbrowser


class FeedlyCralwer:
    def __init__(self):
        pass

    async def init_browser(self):
        pass

    async def goto_feedly_index(self):
        pass

    async def goto_fb_login_page(self):
        pass

    async def fb_login(self):
        pass

    async def click_all_page(self):
        pass

    async def scroll_page(self):
        pass

    async def get_content(self):
        pass

    async def get_result(self):
        # todo 耦合怎麼辦 跟進度
        await self.init_browser()
        await self.goto_feedly_index()
        await self.goto_fb_login_page()
        await self.fb_login()
        await self.click_all_page()
        await self.scroll_page()
        return await self.get_content()


if __name__ == '__main__':
    pass
