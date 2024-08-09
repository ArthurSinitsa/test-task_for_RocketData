import re
import json

import requests
from bs4 import BeautifulSoup


def get_soup() -> BeautifulSoup:
    st_accept = "text/html"
    st_useragent = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/88.0.4324.96 Safari/537.36")
    headers = {
        "Accept": st_accept,
        "User-Agent": st_useragent
    }
    url = 'https://omsk.yapdomik.ru/about'

    response = requests.get(url, headers=headers)
    return BeautifulSoup(response.content, "lxml")


def get_extract(soup: BeautifulSoup) -> list:
    extract = json.loads(soup.find_all('script')[-3].text.lstrip('windontalSte.= '))['shops']
    for elem in extract:
        del elem['payment_type']
        del elem['rules']
        del elem['options']
        del elem['customCookingTime']
        del elem['workingHours']
        del elem['only_delivery']
    return extract


def get_working_hours(extracted_shop: dict) -> list[str]:
    working_hours: list[str] = []
    days: dict[int, str] = {
        1: 'Пн',
        2: 'Вт',
        3: 'Ср',
        4: 'Чт',
        5: 'Пт',
        6: 'Сб',
        0: 'Вс',
    }
    for period in extracted_shop['schedule']:
        working_days: str = f'{days[period['startDay']]}-{days[period['endDay']]}' if days[period['startDay']] != days[
            period['endDay']] else days[period['startDay']]
        working_hours.append(
            f'{working_days}: {period['openTime'][:5]}-{period['closeTime'][:5]}'
        )
    return working_hours


def get_name(extracted_shop: dict) -> str:
    return 'Японский Домик ' + extracted_shop['geoPoint']


def get_coords(extracted_shop: dict) -> list[str]:
    return [extracted_shop['coord']['latitude'], extracted_shop['coord']['longitude'], ]


def parse():
    soup = get_soup()
    extract = get_extract(soup)
    parsed_shops: list[dict] = []
    for shop in extract:
        parsed_shops.append(
            {
                'name': get_name(shop),
                'address': shop['address'],
                'latlon': get_coords(shop),
                'phones': ['+7(962)058-70-97',],
                'working_hours': get_working_hours(shop),
            }
        )
    with open('site2result.json', 'w', encoding='utf-8') as fp:
        json.dump(parsed_shops, fp, ensure_ascii=False)


if __name__ == '__main__':
    parse()
