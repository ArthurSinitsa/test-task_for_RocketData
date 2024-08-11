import os
import json
from datetime import datetime
from dotenv import load_dotenv

import requests
from bs4 import BeautifulSoup
from geopy.geocoders import GoogleV3

main_domain = 'https://www.santaelena.com.co'

def get_soup(url: str) -> BeautifulSoup:
    st_accept = "text/html"
    st_useragent = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/88.0.4324.96 Safari/537.36")
    headers = {
        "Accept": st_accept,
        "User-Agent": st_useragent
    }
    url = 'https://www.santaelena.com.co/tiendas-pasteleria/' + url
    response = requests.get(url, headers=headers)
    bs = BeautifulSoup(response.content, "lxml")
    invalid_tags = ['h1', 'script', 'noscript', 'h2', 'picture', 'li', 'ul', 'span', 'a', 'label', 'form', 'search',
                    'nav', 'img', 'button', 'svg', 'source', 'strong', 'br']
    for tag in invalid_tags:
        for match in bs.find_all(tag):
            match.replaceWithChildren()
    return bs


def get_extract(soup: BeautifulSoup) -> dict[str, dict]:
    def extract_from_str(string: str) -> dict[str, str]:
        phone_start: int = string.find('Teléfono:')
        working_time_start: int = string.find('Horario de atención:')
        time, address, phone = (
            string[working_time_start:].strip().replace('\n', ' ').split(':', 1)[1].strip(),
            string[:phone_start].strip().replace('\n', ' ').split(':')[1].strip(),
            string[phone_start:working_time_start].strip().replace('\n', ' ').split(':')[-1].strip()
        )
        return {
            'address': address,
            'phones': [phone],
            'working_time': time,
        }

    extract: dict = {}
    keys: list = []
    k: int = 0
    for i in soup.find_all('h3', class_='elementor-heading-title elementor-size-default'):
        keys.append(i.text.strip())
    for i in soup.find_all('div', class_='elementor-widget-container'):
        if i.find(lambda tag: (tag.name == 'p' or tag.name == 'h4') and 'Dirección:' in tag.text):
            extract[keys[k].replace('\n', ' ').strip()] = i.text
            k += 1
    for key, value in extract.items():
        extract[key] = extract_from_str(value)
    return extract


def get_name(shop_name: str) -> str:
    return 'Pastelería Santa Elena ' + shop_name


def get_address(soup: BeautifulSoup, extract: dict) -> str:
    city = soup.find(
        lambda tag: (tag.name == 'div' and tag.attrs['class'][0] == 'elementor-widget-container' and
                     ('Ubicación de nuestras tiendas' in tag.text or 'Ubicación de nuestra tienda' in tag.text)) or
                    (tag.name == 'h1' and 'Ubicación de nuestra tienda' in tag.text)
    )
    if city is not None:
        return city.text.strip().split()[-1] + ', ' + extract['address']
    else:
        return extract['address']


def get_coords(address: str) -> list[str]:
    load_dotenv()
    api_key = os.getenv('API_KEY')
    if api_key:
        geolocator = GoogleV3(api_key=api_key, user_agent="tutorial")
        location = geolocator.geocode(address)
        return [str(location.latitude), str(location.longitude)]
    else:
        print('Check it out .env file for the presence of GoogleMaps api_key')
        return ['0', '0']


def get_phones(extract: dict) -> list[str]:
    return extract['phones']


def get_working_hours(extract: dict) -> list[str]:
    working_hours: list[str] = []

    def translate_phrase(phrase: str) -> str:
        return (phrase.replace('lunes', 'Пн')
                .replace('prestamos servicio 24 horas.', 'Мы предоставляем услуги 24 часа в сутки.').replace('sábados',
                                                                                                             'Сб')
                .replace('festivos', 'праздничные дни').replace('viernes', 'Пт').replace('sábado', 'Сб')
                .replace('domingos', 'Вс').replace('incluye', 'включая')
                .replace('prestamos servicio las 24 horas.', 'Мы предоставляем услуги 24 часа в сутки.')
                .replace('a', '-')
                .replace('y', 'и').replace('domingo', 'Вс'))

    def convert24(time: str):
        if 'A M' in time:
            time_to_convert = time.replace('A M', 'AM')
        elif 'P M' in time:
            time_to_convert = time.replace('P M', 'PM')
        else:
            time_to_convert = time
        t = datetime.strptime(time_to_convert, '%I:%M %p')
        return t.strftime('%H:%M')

    if (extract['working_time'].lower() != 'prestamos servicio 24 horas.' and
            extract['working_time'].lower() != 'prestamos servicio las 24 horas.'):
        index = extract['working_time'].find('p.m') + 4 if extract['working_time'].lower().find('p.m') != -1 else -1
        prepare = [extract['working_time'].lower()[:index], extract['working_time'].lower()[index:]]
        for prep in prepare:
            if prep is not None and prep != '' and prep != '.' and prep != ' ':
                pre = prep.replace('.', '').split(':', 1)
                if pre[0][-1].isdigit() or pre[0][-2].isdigit():
                    pre = prep.replace('.', '').split('–', 1)
                clock = ' - '.join([convert24(hour.strip()) for hour in pre[1].strip().upper().split('–')] if '–' in pre[1]
                                   else [convert24(hour.strip()) for hour in pre[1].strip().upper().split('/')])
                working_hours.append(translate_phrase(pre[0].strip()) + ': ' + clock)
    else:
        working_hours = ['Мы предоставляем услуги 24 часа в сутки.']
    return working_hours


def parse() -> list[dict]:
    parsed_shops: list[dict] = []
    urls: list = [
        'tienda-medellin/',
        'tienda-bogota/',
        'tienda-monteria/',
        'nuestra-pasteleria-en-barranquilla-santa-elena/',
        'tiendas-pastelerias-pereira/',
    ]
    for url in urls:
        soup = get_soup(url)
        extract = get_extract(soup)
        for key, value in extract.items():
            parsed_shops.append(
                {
                    'name': get_name(key),
                    'address': get_address(soup, value),
                    'latlon': get_coords(get_address(soup, value)),
                    'phones': get_phones(value),
                    'working_hours': get_working_hours(value),
                }
            )
    return parsed_shops


if __name__ == '__main__':
    data = parse()
    with open('site3result.json', 'w', encoding='utf-8') as fp:
        json.dump(data, fp, ensure_ascii=False)
