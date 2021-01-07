import unicodedata
from typing import List, Optional, Callable, Tuple, Union
from curtsies import FullscreenWindow, Input, FSArray
from curtsies.fmtfuncs import red, bold, green, on_blue, yellow, on_yellow, plain


def update_fsarray(a, title, columns, index):
    count = 1
    a[0:count, 0:title.width] = [title]
    for idx, col in enumerate(columns):
        if idx == index:
            msg = bold('>  ' + col)
        else:
            msg = plain('   ' + col)
        a[count:count + 1, 0:msg.width] = [msg]
        count += 1
    return a


def select_menus(title, columns):
    with FullscreenWindow() as window:
        with Input() as input_generator:
            a = FSArray(window.height, window.width)
            title = bold(title)
            index = 0
            a = update_fsarray(a, title, columns, index)
            window.render_to_terminal(a)
            for c in input_generator:
                if c == '<ESC>':
                    break
                elif c == '<UP>':
                    index = max(0, index - 1)
                elif c == '<DOWN>':
                    index = min(len(columns) - 1, index + 1)
                elif c == '<RIGHT>':
                    return 'right'
                elif c == '<Ctrl-j>':
                    return index

                a = update_fsarray(a, title, columns, index)
                window.render_to_terminal(a)


class Ezdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def wide_chars(s):
    return sum(unicodedata.east_asian_width(x) in ['W', 'F'] for x in s)


def width(s):
    return len(s) + wide_chars(s)


class Table:
    def __init__(self, display_table=False, base_width_count=2):
        self.base_width_count = base_width_count
        self.len_list = []
        self.display_table = display_table
        self.columns = []
        self.data = []
        self.under_line_count = 0
        self.type_mapping = {
            'left': '<',
            'center': '^',
            'right': '>',
        }

    def add_column(self,
                   name: str,
                   _type: Optional[str] = 'right',  # left center right
                   width: Optional[int] = 10):
        self.columns.append(Ezdict(
            name=name,
            type=_type,
            width=width
        ))

    @property
    def columns_count(self):
        return len(self.columns)

    def add_row(self, row: Union[Tuple, List]):
        assert len(row) == self.columns_count
        self.data.append(row)

    def get_under_line_string(self):
        return "_" * self.under_line_count

    def get_string(self):
        rows = self.get_string_rows()
        return '\n'.join(rows)

    def get_string_rows(self):
        self.calc_under_line_count()
        headers = self.get_headers_string()
        if self.display_table:
            rows = [self.get_under_line_string(), headers, self.get_under_line_string()]
        else:
            rows = [headers]
        for row in self.data:
            rows.append(self.get_row_string(row))
            if self.display_table:
                rows.append(self.get_under_line_string())
        return rows

    def get_row_string(self, row: Union[Tuple, List]):
        text = '|'
        for index, col_text in enumerate(row):
            width = min(self.len_list[index], self.columns[index].width)
            width -= wide_chars(col_text)
            _type = self.columns[index].type
            sign = self.type_mapping.get(_type, '^')
            text += f'{col_text:{sign}{width}}|'
        return text

    def get_headers_string(self):
        col_rows = [col.name for col in self.columns]
        return self.get_row_string(col_rows)

    def calc_under_line_count(self):
        for col_index in range(self.columns_count):
            calc_list = [width(row[col_index]) + self.base_width_count for row in self.data]
            calc_list.append(width(self.columns[col_index].name) + self.base_width_count)
            self.len_list.append(max(calc_list))
        self.under_line_count = (sum(self.len_list)) * 2 + 4

    def show(self):
        print(self.get_string())


if __name__ == '__main__':

    raw_data = '''乘客姓名,性别,出生日期
        HuangTianhui,男,1948/05/28
        姜，翠云,女,1952/03/27
        李红晶,女,1994/12/09
        LuiChing,女,1969/08/02
        宋飞飞,男,1982/03/01
        唐旭东,男,1983/08/03
        YangJiabao,女,1988/08/25
        买买提江·阿布拉,男,1979/07/10
        安文兰,女,1949/10/20
        胡偲婠(婴儿),女,2011/02/25
        (有待确定姓名),男,1985/07/20'''
    data = [[cell.strip() for cell in row.split(",")] for row in raw_data.split("\n") if row]
    columns = data[0]
    data = data[1:]
    table = Table()
    table.add_column('乘客姓名', width=24)
    table.add_column('性别', width=4)
    table.add_column('出生日期', width=10)
    for row in data:
        table.add_row(row)
    table.show()
