import os
import requests
from bs4 import BeautifulSoup

import psycopg2


db_params = {
    'host': 'localhost',
    'database': 'PizzaExpress',
    'user': 'postgres',
    'password': '',
}
conn = psycopg2.connect(**db_params)
cur = conn.cursor()

url = "https://dominos.by/pizza"

response = requests.get(url)

if not os.path.exists('images'):
    os.makedirs('images')


if response.status_code == 200:
    soup = BeautifulSoup(response.text, "lxml")
    pizza_containers = soup.find_all("div", class_="product-card product-card--vertical")

    for pizza_container in pizza_containers:

        pizza_name = pizza_container.find("div", class_="product-card__title").text
        pizza_description = pizza_container.find("div", class_="product-card__description").text
        pizza_price = pizza_container.find("p", class_="product-card__modification-info-price").text
        pizza_weight = pizza_container.find("p", class_="product-card__modification-info-weight").text
        image_url = pizza_container.find("img", class_="media-image__element product-card-media__element")['src']

        image_response = requests.get(image_url)

        if image_response.status_code == 200:
            image_filename = os.path.join('images', os.path.basename(image_url))
            with open(image_filename, 'wb') as image_file:
                image_file.write(image_response.content)
            insert_query = 'INSERT INTO "PExpress_dish" (pizza_name, price, weight, photo) VALUES (%s, %s, %s, %s);'
            cur.execute(insert_query, (pizza_name, pizza_price, pizza_weight, image_filename))
            conn.commit()

            print("Название пиццы:", pizza_name)
            print("Состав:", pizza_description)
            print("Цена пиццы:", pizza_price)
            print("Вес:", pizza_weight)
            print("Фото URL:", image_url)
            print("Фото сохранено как:", image_filename)
            print("\n")
        else:
            print(f"Failed to download image for pizza: {pizza_name}")
else:
    print("Failed to retrieve the webpage.")