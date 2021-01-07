from curtsies import FullscreenWindow, Input, FSArray
from curtsies.fmtfuncs import (
    black, red, green, yellow, blue, magenta, cyan, gray, on_black, on_dark, on_red,
    on_green, on_yellow, on_blue, on_magenta, on_cyan, on_gray, bold, dark, underline, blink,
    invert, plain
)
from typing import Callable, Any
import re
from util import Ezdict


class TerminalCLI:
    _fn_mapping = {
        'black': black,
        'red': red,
        'green': green,
        'yellow': yellow,
        'blue': blue,
        'magenta': magenta,
        'cyan': cyan,
        'gray': gray,
        'on_black': on_black,
        'on_dark': on_dark,
        'on_red': on_red,
        'on_green': on_green,
        'on_yellow': on_yellow,
        'on_blue': on_blue,
        'on_magenta': on_magenta,
        'on_cyan': on_cyan,
        'on_gray': on_gray,
        'bold': bold,
        'dark': dark,
        'underline': underline,
        'blink': blink,
        'invert': invert,
        'plain': plain,
    }

    def __init__(self, window: FullscreenWindow):
        self.window = window
        self.menu_select_index = 0
        self.menu_count = 0
        self.count = 0
        self.fsa = None
        self.menu_list = []
        self.keys_comannad = dict()
        self.init()

    def to_terminal_color(self, text: str):
        find_to_change = False
        # todo 這樣寫不夠優雅，有機會在重構
        while re.findall('<.+?>.+?</.+?>', text):
            find_to_change = True
            el = re.findall('<.+?>.+?</.+?>', text)[0]
            start_idx = text.index(el)
            end_idx = start_idx + len(el)
            start_text = text[:start_idx]
            end_text = text[end_idx:]
            fn_str = re.findall('</(.+?)>', el)[0]
            fn = self._fn_mapping[fn_str]
            new_str = re.sub('<.+?>', '', el)
            text = start_text + fn(new_str) + end_text
            text = str(text)
        else:
            if not find_to_change:
                text = str(plain(text))
        return text

    def init(self):
        window = self.window
        self.count = 0
        self.menu_select_index = 0
        self.menu_count = 0
        self.menu_list = []
        self.keys_comannad = dict()
        self.fsa = FSArray(window.height, window.width)
        self.keys_register('<UP>', self.up_command)
        self.keys_register('<DOWN>', self.down_command)
        self.keys_register('<Ctrl-j>', self.enter_command)

    async def enter_command(self, terminal: Any):
        menu = self.menu_list[self.menu_select_index]
        await menu.command(terminal)

    async def up_command(self):
        self.menu_select_index = max(0, self.menu_select_index - 1)

    async def down_command(self):
        self.menu_select_index = min(len(self.menu_list) - 1, self.menu_select_index + 1)

    def add_row(self, text, next_count=True):
        text = self.to_terminal_color(text)
        self.fsa[self.count:self.count + 1, 0:len(text)] = [text]
        if next_count:
            self.count += 1
        return self.count

    def keys_register(self, key, command):
        self.keys_comannad[key] = command

    async def input_execute(self, c):
        for key, command in self.keys_comannad.items():
            if key == c:
                await command(self)

    def menu_text_process(self, text, count):
        if self.menu_select_index == count:
            text = bold(f'>  {text}')
            text = str(text)
        else:
            text = '   ' + text
        text = self.to_terminal_color(text)
        return text

    def add_menu(self, text, command):
        self.menu_list.append(Ezdict(
            original_text=text,
            command=command,
            line_count=self.count,
            menu_index=self.menu_count
        ))
        text = self.menu_text_process(text, self.menu_count)
        self.menu_count += 1
        self.fsa[self.count:self.count + 1, 0:len(text)] = [text]

        self.count += 1
        return self.count

    def render(self):
        # render menu
        for el in self.menu_list:
            text = self.menu_text_process(el.original_text, el.menu_index)
            self.fsa[el.line_count:el.line_count + 1, 0:len(text)] = [text]

        self.window.render_to_terminal(self.fsa)


async def terminal_window(index_async_function: Callable):
    with FullscreenWindow() as window:
        with Input() as input_generator:
            terminal = TerminalCLI(window)
            await index_async_function(terminal)
            terminal.render()

            for c in input_generator:
                await terminal.input_execute(c)
                terminal.render()


if __name__ == '__main__':
    import asyncio


    async def main():
        terminal_window()


    asyncio.run(main())
