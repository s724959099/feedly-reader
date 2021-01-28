from model import db, Item
from pony.orm import db_session, select, raw_sql
from typing import List, Optional, Callable, Tuple, Union
from loguru import logger
from util import Ezdict, Table, select_menus
import os
import re

with open(os.path.join(os.path.dirname(__file__), 'keyword.txt'), 'r', encoding="utf-8") as f:
    keywords = f.read().split('\n')
pattern = "|".join(keywords)


class ItemCRUD:
    @db_session()
    def create_list(self, batch: List):
        for el in batch:
            item = Item.select(lambda x: x.href == el.href).first()
            if item:
                logger.warning(f'find {el.title}({el.href})')
                continue
            try:
                Item(**el)
            except Exception as e:
                logger.error(f'error {el.title}({el.href})')
                pass

        logger.info(f'create done| count: {len(batch)}')

    @db_session()
    def get_count(self,
                  lambda_fn: Optional[Callable] = lambda x: True
                  ):
        return Item.select(lambda_fn).count()

    @db_session()
    def update_all_to_read(self):
        for el in Item.select(lambda x: not x.read):
            el.read = True

    @db_session()
    def get_list(self,
                 offset: Optional[int] = 0,
                 limit: Optional[int] = 10,
                 lambda_fn: Optional[Callable] = lambda x: True
                 ):
        return Item.select(lambda_fn).limit(limit, offset=offset)[:]


item_crud = ItemCRUD()

if __name__ == '__main__':
    items = item_crud.get_list(
        lambda_fn=lambda x: '金' in x.title
    )
    table = Table()
    table.add_column(name='source', width=20, _type='left')
    table.add_column(name='title', width=100, _type='left')
    table.add_column(name='popular', _type='left')
    table.add_column(name='href', width=200, _type='left')
    for item in items:
        row = (item.source, item.title, item.popular, item.href)
        table.add_row(row)

    data = table.get_string_rows()
    index = select_menus('test api', data)
    if index == 'right':
        table.data = []
        items = item_crud.get_list(
            offset=10,
            lambda_fn=lambda x: '金' in x.title,
        )
        print(len(items))
        for item in items:
            row = (item.source, item.title, item.popular, item.href)
            table.add_row(row)
        data = table.get_string_rows()
        index = select_menus('test api', data)
        # index = select_menus('test api', table.get_under_line_string())

    print(index)
    # table.show()
