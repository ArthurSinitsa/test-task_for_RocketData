import re
import json

import requests
from bs4 import BeautifulSoup


def get_soup() -> BeautifulSoup:
    url = 'https://dentalia.com/clinicas'
    response = requests.get(url)
    return BeautifulSoup(response.text, "html.parser")


def get_phone(text: str) -> list:
    regex = re.compile(r"\d{3}[ -]?\d{3}[ -]?\d{4}")
    numbers = re.findall(regex, text)
    numbers.append('8000033682')
    return numbers


def get_working_hour(text: str) -> list:
    return [text.split('\n\n\n')[-1]
            .replace('L', 'Пн')
            .replace('V', 'Пт')
            .replace('a', '-')
            .replace('S', 'Сб')
            .replace('D', 'Вс')
            ]


def parse():
    clinics_info: list = []
    soup = get_soup()
    clinics = soup.find_all('div', 'dg-map_clinic-card w-dyn-item')

    for clinic in clinics:
        clinics_info.append(
            {
                'name': clinic.attrs['m8l-c-list-name'],
                'address': clinic.attrs['m8l-c-filter-location'],
                'latlon': clinic.attrs['m8l-c-list-coord'].split(', '),
                'phones': get_phone(clinic.text),
                'working_hours': get_working_hour(clinic.text),
            }
        )

    with open('site1result.json', 'w', encoding='utf-8') as fp:
        json.dump(clinics_info, fp, ensure_ascii=False)


if __name__ == '__main__':
    parse()
