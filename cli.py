import re
import asyncio
from controller import item_crud
from util import Ezdict, Table, select_menus
from functools import partial
import os
from pony.orm import raw_sql
from gui_terminal import terminal_window, TerminalCLI
from typing import Callable

# todo 用global 這樣寫不好
offset = 0
lambda_fn = None
execute_fn = None


async def execute_url(terminal: TerminalCLI, fn: Callable, url: str, **kwargs):
    if url:
        webbrowser.open(url)
    await fn(terminal, **kwargs)


async def right_command(terminal: TerminalCLI, fn: Callable, count: int):
    global offset
    max_offset = count // 10
    offset = min(offset + 10, max_offset * 10)
    await fn(terminal)


async def left_command(terminal: TerminalCLI, fn: Callable):
    global offset
    offset = max(offset - 10, 0)
    await fn(terminal)


async def read_articles(terminal: TerminalCLI, **kwargs):
    # todo 這個function 太大了
    global offset
    global lambda_fn
    count = item_crud.get_count(lambda_fn=lambda_fn)
    page_count = round((count / 10) + 0.5)
    items = item_crud.get_list(
        lambda_fn=lambda_fn,
        offset=offset
    )
    table = Table()
    table.add_column(name='source', width=80, _type='left')
    table.add_column(name='title', width=400, _type='left')
    for item in items:
        row = (item.source, item.title)
        table.add_row(row)

    data = table.get_string_rows()
    menu_select_index = terminal.menu_select_index
    terminal.init()
    if kwargs.get('after_enter'):
        terminal.menu_select_index = menu_select_index
    terminal.add_row('<bold>Feddly 閱讀器</bold>')

    for index, el in enumerate(data):
        if index == 0:
            url = None
        else:
            url = items[index - 1].href
        _execute_url = partial(execute_url, fn=execute_fn, url=url, after_enter=True)
        terminal.add_menu(el, command=_execute_url)

    page = (offset / 10) + 1
    page_list = []
    for num in range(1, page_count + 1):
        if num == page:
            page_list.append(str(bold(cyan(str(num)))))
        else:
            page_list.append(str(num))
    page_text = " ".join(page_list)
    terminal.add_row('')
    terminal.add_row('')
    terminal.add_row(page_text)

    # key register
    _right_command = partial(right_command, fn=execute_fn, count=count)
    _left_command = partial(left_command, fn=execute_fn)
    terminal.keys_register('<RIGHT>', _right_command)
    terminal.keys_register('<LEFT>', _left_command)


async def read_all_not_read_article(terminal: TerminalCLI, **kwargs):
    global lambda_fn
    global execute_fn
    execute_fn = read_all_not_read_article
    lambda_fn = lambda x: not x.read
    await read_articles(terminal, **kwargs)


async def read_all_point_article(terminal: TerminalCLI, **kwargs):
    global lambda_fn
    global execute_fn
    import os
    from model import db
    from pony.orm import db_session
    with open(os.path.join(os.path.dirname(__file__), 'keyword.txt'), 'r', encoding="utf-8") as f:
        keywords = f.read().split('\n')
    pattern = "|".join(keywords)

    def regexp(expr, item):
        reg = re.compile(expr)
        return reg.search(item.lower()) is not None

    with db_session():
        conn = db.get_connection()
        conn.create_function('REGEXP', 2, regexp)

        execute_fn = read_all_point_article

        lambda_fn = lambda x: not x.read and (
                raw_sql("x.title REGEXP $(pattern)") or
                raw_sql("x.summary REGEXP $(pattern)")
        )
        await read_articles(terminal, **kwargs)


async def read_article_template(terminal: TerminalCLI):
    terminal.init()
    terminal.add_row('<bold>Feddly 閱讀器</bold>')
    terminal.add_menu('重點未讀文章', command=read_all_point_article)
    terminal.add_menu('所有未讀文章', command=read_all_not_read_article)
    terminal.add_menu('全部更新為已讀', command=read_all_not_read_article)


async def get_feedly_content(process_step):
    # todo delete
    browser = await launch(dict(
        headless=False,
        defaultViewport=None,
        handleSIGINT=False, handleSIGTERM=False, handleSIGHUP=False,
        executablePath=""
    ))
    # browser = await launch({'headless': True, 'args': []}, handleSIGINT=False, handleSIGTERM=False, handleSIGHUP=False,
    #                        executablePath="")
    page = await browser.newPage()
    await page.goto('https://feedly.com/i/welcome/logged-out')
    process_step.add_progress(text='login')
    await page.click('button.LandingHeaderBar__action')
    process_step.add_progress(text='click facebook')
    await page.waitForSelector('a.button.facebook')
    await page.click('a.button.facebook')
    process_step.add_progress(text='after click facebook')
    await page.waitForSelector('#email')
    process_step.add_progress(text='in facebook login')
    # todo email/password
    await page.type('#email', '')
    await page.type('#pass', '')
    await page.click('input[name="login"]')
    process_step.add_progress(text='in feedly')
    await page.waitForSelector('div[title="All"]')
    await page.click('div[title="All"]')

    process_step.add_progress(text='after click all')
    await page.waitForSelector('#header-title')
    process_step.add_progress(text='ready while')
    while True:
        await page.evaluate("""document.getElementById('feedlyFrame').scrollBy(0,5000);""")
        await asyncio.sleep(2)
        in_end = await page.querySelector('button.giant-mark-as-read')
        if in_end:
            break
    ret = await page.content()
    process_step.add_progress(text='get content')
    await browser.close()
    process_step.add_progress(text='brower close')
    return ret


def update_progress(total: int, progress: int):
    barLength = 100  # 5%
    progress = float(progress) / float(total)
    if progress >= 1.:
        progress = 1
    block = int(round(barLength * progress))
    text = "[{}] {:.0f}% ".format(
        "#" * block + "-" * (barLength - block), round(progress * 100, 0))
    # sys.stdout.write(text)
    return text


# todo change module
class ProgressStep:
    def __init__(self, total: int):
        self.total = total
        self.progress = 0
        self.text = ''

    def add_progress(self, add: int = 1, text: str = ''):
        temp = self.progress + add
        assert temp <= self.total
        self.progress = temp
        self.text = text

    def is_done(self):
        return self.total <= self.progress

    def get_progress_text(self):
        return update_progress(self.total, self.progress) + f'    {self.text}'


async def update_articles(terminal: TerminalCLI):
    from threading import Thread
    progress_step = ProgressStep(total=9)

    def job(progress_step):
        asyncio.run(get_feedly_content(progress_step))

    t = Thread(target=job, args=(progress_step,))
    t.start()

    terminal.init()
    terminal.add_row('<bold>Feddly 閱讀器</bold>')
    terminal.add_row('下載中...')
    terminal.add_row('')
    while True:
        if progress_step.is_done():
            break
        await asyncio.sleep(0.1)
        text = progress_step.get_progress_text()
        terminal.add_row(text, next_count=False)
        terminal.render()
    await index_template(terminal)


async def index_template(terminal: TerminalCLI):
    terminal.init()
    terminal.add_row('<bold>Feddly 閱讀器</bold>')
    terminal.add_menu('閱讀文章', command=read_article_template)
    terminal.add_menu('更新資料', command=None)


async def main():
    """
    閱讀文章
    - 重點未讀文章
    - 所有未讀文章
    - 全部更新為已讀
    更新資料
    - 抓取文章
    - 抓取文章並且標記為閱讀(pypeeter)
    """
    await terminal_window(index_template)


if __name__ == '__main__':
    asyncio.run(main())
