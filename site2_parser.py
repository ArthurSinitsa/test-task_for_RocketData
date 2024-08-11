import re
import json

import requests
from bs4 import BeautifulSoup

main_domain = 'https://yapdomik.ru/'

def get_soup(url: str) -> BeautifulSoup:
    st_accept = "text/html"
    st_useragent = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/88.0.4324.96 Safari/537.36")
    headers = {
        "Accept": st_accept,
        "User-Agent": st_useragent
    }
    response = requests.get(url, headers=headers)
    return BeautifulSoup(response.content, "lxml")


def get_extract(soup: BeautifulSoup) -> list[dict]:
    extract = json.loads(soup.find_all('script')[-3].text.lstrip('windontalSte.= '))['shops']
    for elem in extract:
        del elem['payment_type']
        del elem['rules']
        del elem['options']
        del elem['customCookingTime']
        del elem['workingHours']
        del elem['only_delivery']
    return extract


def get_phones(soup: BeautifulSoup) -> list[str]:
    return soup.find('div', class_='contacts__phone').contents[3].contents


def get_address(soup: BeautifulSoup, extracted_shop: dict) -> str:
    return soup.find('a', class_='city-select__current link link--underline').text + ', ' + extracted_shop['address']


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


def parse() -> list[dict]:
    parsed_shops: list[dict] = []
    urls: list = [
        'https://omsk.yapdomik.ru/about',
        'https://achinsk.yapdomik.ru/about',
        'https://berdsk.yapdomik.ru/about',
        'https://krsk.yapdomik.ru/about',
        'https://nsk.yapdomik.ru/about',
        'https://tomsk.yapdomik.ru/about',
    ]
    for url in urls:
        soup = get_soup(url)
        extract = get_extract(soup)
        for shop in extract:
            parsed_shops.append(
                {
                    'name': get_name(shop),
                    'address': get_address(soup, shop),
                    'latlon': get_coords(shop),
                    'phones': get_phones(soup),
                    'working_hours': get_working_hours(shop),
                }
            )
    return parsed_shops


if __name__ == '__main__':
    data = parse()
    with open('site2result.json', 'w', encoding='utf-8') as fp:
        json.dump(data, fp, ensure_ascii=False)
