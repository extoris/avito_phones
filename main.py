import base64
import json
import os
import re
import time

import pytesseract
from PIL import Image
from bs4 import BeautifulSoup
from seleniumwire import undetected_chromedriver as uc
from urllib.parse import unquote
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains


def get_title(soup):
    """Получаем заголовок со страницы обьявлений
    :param soup:bs4.BeautifulSoup
    :return: название обьявления
    :rtype: str"""
    print('get_json')
    script = soup.find(text=re.compile('window.__initialData__')).split(';')[0].split('=')[-1].strip()
    script = unquote(script)
    script = script[1:-1]
    data = json.loads(script)
    for key in data:
        if 'item' in key:
            item = data[key]['buyerItem']
            try:
                title = item['item']['title']
            except KeyError:
                title = None

    return title


def get_buttons_litters(soup):
    """Получаем добавочные символы класса для поиска кнопки 'Показать телефон'
    :param soup:bs4.BeautifulSoup
    :return: Добавочные символы названия класса
    :rtype: str"""
    # символы дописываемые к классу
    print('searching button')
    classes = soup.find('button', attrs={'data-marker': "item-phone-button/card"}).get('class')
    for i in classes:
        if 'button-button_card' in i:
            return i.replace('button-button_card-', '')


def get_phone_number(soup):
    """Получаем номер телефона
    :param soup: bs4.BeautifulSoup
    :return: номер телефона
    :rtype: str"""
    phone_number = None
    config = r'--oem 3 --psm 13'
    try:
        true_img = ""
        for img in soup.find_all("img"):
            if "data:image/png" in str(img):
                true_img = img.get('src')
        img_str = true_img.split(',')[1]
        img_data = base64.b64decode(img_str)
        with open('phone_image.png', 'wb') as f:
            f.write(img_data)
        phone_number = pytesseract.image_to_string('phone_image.png', config=config).strip()
        print(phone_number)
        os.remove('phone_image.png')
    except Exception as e:
        print(e)
    return phone_number


def get_answer(url):
    """Собираем донные обьявления
    :param str url: ссылка
    :return: ссылка на обьявление и телефон
    :rtype: dict"""

    offer = {'url': url, 'phone': None, 'title': None}

    options = uc.ChromeOptions()
    options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1420,1080")
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    driver = uc.Chrome(options=options)

    try:
        driver.get(url=url)
        soup = BeautifulSoup(driver.page_source, "lxml")
        buttons_litters = get_buttons_litters(soup)

        button = driver.find_element(By.CSS_SELECTOR, f'.button-button_card-{buttons_litters}')
        ActionChains(driver).move_to_element(button).click(button).perform()
        offer['title'] = get_title(soup)
        # data = get_json(soup)
        time.sleep(2)  # Необходимо для прогрузки кода HTML, но лучше заменить на wait
        soup = BeautifulSoup(driver.page_source, "lxml")
        phone_number = get_phone_number(soup)
        offer['phone'] = phone_number

    except Exception as ex:
        print(ex)
    finally:
        driver.close()
        driver.quit()
    return offer


def main():
    url = 'https://www.avito.ru/yuzhno-sahalinsk/kvartiry/apartamenty-studiya_466m_89et._2601326830'

    print(get_answer(url))


if __name__ == '__main__':
    main()
