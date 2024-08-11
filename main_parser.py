import json
from site1_parser import main_domain as m1, parse as p1
from site2_parser import main_domain as m2, parse as p2
from site3_parser import main_domain as m3, parse as p3


def parse_all():
    data = {
        m1: p1(),
        m2: p2(),
        m3: p3(),
    }
    with open('result.json', 'w', encoding='utf-8') as fp:
        json.dump(data, fp, ensure_ascii=False)


if __name__ == '__main__':
    parse_all()
