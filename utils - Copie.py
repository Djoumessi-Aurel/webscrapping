import requests
from bs4 import BeautifulSoup
from pprint import pprint
import pandas as pd
from word2number import w2n
from urllib.parse import urljoin


def traverse_dom(element: BeautifulSoup, level:int = 0):
    if element.name:
        print(f"{'  ' * level}<{element.name}>")
    
    if hasattr(element, "children"):
        for child in element.children:
            traverse_dom(child, level + 1)



# Tous les livres par catégorie, dans un dataframe
def get_all_books_with_category(url: str):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser') # ou xml, html5lib

    cats = soup.find('aside').find("div", class_="side_categories").find("ul").find("li").find("ul")
    links = cats.find_all("a")

    i=1
    length = len(links)
    df_list = [] # Liste de dataframes
    for lien in links:
        url_to_go = urljoin(url, lien.get("href"))
        category = lien.text.strip()

        print(f"Scraping: link {i} of {length}...")
        df_list.append(get_books_in_one_page(url=url_to_go, category=category, category_link=url_to_go))
        i += 1

    return pd.concat(df_list, axis=0).reset_index()



# Catégories qui ont moins de x livres
def get_categories_with_less_than(url:str, x: int):
    cats_and_books_count = get_categories_and_books_count(url)
    return cats_and_books_count[cats_and_books_count["books_count"] < x].drop(["category_link"], axis='columns').reset_index()

# Catégories et nombre de livres
def get_categories_and_books_count(url: str):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser') # ou xml, html5lib

    cat_dict = {"category":[], "books_count":[], "category_link":[]}

    cats = soup.find('aside').find("div", class_="side_categories").find("ul").find("li").find("ul")
    links = cats.find_all("a")

    root_url = url if url.endswith("/") else f'{url}/'
    i=1
    length = len(links)
    for lien in links:
        url_to_go = f'{root_url}{lien.get("href")}'
        category = lien.text.strip()

        print(f"Scraping: link {i} of {length}...")
        books_count = get_books_count_in_one_page(url_to_go)
        i += 1

        cat_dict["category"].append(category)
        cat_dict["books_count"].append(books_count)
        cat_dict["category_link"].append(url_to_go)

    return pd.DataFrame.from_dict(cat_dict)


# Liste des catégories de livres
def get_categories(url: str):
    response = requests.get(url)

    soup = BeautifulSoup(response.text, 'html.parser') # ou xml, html5lib

    aside = soup.find('aside')
    cats = aside.find("div", class_="side_categories").find("ul").find("li").find("ul")

    categories = [child.text.strip() for child in cats.children if child.name]
    return categories


# Récupère les livres d'une page avec ses caractéristiques. Renvoie les données sous forme de dataframe
# Les attributs category et category_link sont nécessaire lorsqu'on veut spécifier qu'on est sur une page qui présente les livres d'une catégorie donnée
def get_books_in_one_page(url: str, category: str = None, category_link: str = None):
    response = requests.get(url)

    soup = BeautifulSoup(response.text, 'html.parser') # ou xml, html5lib

    # 2. LES CARACTERISTIQUES DES LIVRES (Titre, catégorie, prix, notation, lien de l'image, disponibilité)
    livres_dict = {"title": [], "category":[], "price":[], "rating":[], "availability":[], "image_link":[], "book_link":[], "category_link":[]}
    livres_soup = soup.find("section").find("ol").find_all("li")
    # print(livres_soup)

    for ls in livres_soup:
        book_title = ls.find("h3").find("a").get("title")
        book_link = ls.find("h3").find("a").get("href")
        image_link = ls.find("div", class_="image_container").find("img").get("src")
        disponibilite = ls.find("p", class_="instock availability").text.strip()
        prix = ls.find("p", class_="price_color").text.strip()
        notation = ls.select_one(".star-rating").get("class")
        if notation is not None and len(notation) == 2:
            try:
                notation = w2n.word_to_num(notation[1])
            except Exception as e:
                notation = notation[1]
        else:
            notation = None

        livres_dict["title"].append(book_title)
        livres_dict["category"].append(category)
        livres_dict["category_link"].append(category_link)
        livres_dict["price"].append(prix)
        livres_dict["rating"].append(notation)
        livres_dict["image_link"].append(urljoin(url, image_link))
        livres_dict["book_link"].append(urljoin(url, book_link))
        livres_dict["availability"].append(disponibilite)

    livres_df = pd.DataFrame.from_dict(livres_dict)
    return livres_df


# Nombre de livres affichés dans une page
def get_books_count_in_one_page(url: str):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser') # ou xml, html5lib
        livres_soup = soup.find("section").find("ol").find_all("li")
        return len(livres_soup)
    except Exception as e:
        print("Une erreur est survenue dans la fonction 'get_books_count_in_one_page':", e)
        return 0


def test(url: str):
    response = requests.get(url)

    soup = BeautifulSoup(response.text, 'html.parser') # ou xml, html5lib
    # print(soup.prettify())
    # traverse_dom(soup)
    # images = soup.find_all('img')
    # pprint(images)

    aside = soup.find('aside')
    cats = aside.find("div", class_="side_categories").find("ul").find("li").find("ul")

    # print(cats.prettify())
    # categories = [lien.text.strip() for lien in cats.find_all("a")]

    categories = [child.text.strip() for child in cats.children if child.name]
    return categories