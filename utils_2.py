import requests
import pandas as pd
from word2number import w2n
from urllib.parse import urljoin
import re
import sys
from selectolax.parser import HTMLParser
from loguru import logger


logger.remove()
logger.add("books.log", rotation="500kb", level="WARNING")
logger.add(sys.stderr)



def extraire_id_livre(url: str):
    try:
        # Utilisation d'une expression régulière pour capturer l'id du livre
        match = re.search(r'_([0-9]+)(?:/index.html)?$', url)
        if match:
            return int(match.group(1))  # Convertir l'id en entier
        else:
            return None  # Renvoyer None si aucun id n'est trouvé
    except Exception:
        return None  # Renvoyer None en cas d'erreur


def extract_price(price_str: str):
    try:
        # Utilisation d'une expression régulière pour capturer le prix
        match = re.search(r'(\d+[.]?\d*)', price_str)
        if match:
            return float(match.group(0))
        else:
            return None
    except Exception:
        return None

def extract_currency(price_str: str):
    try:
        # Utilisation d'une expression régulière pour capturer la devise
        match = re.search(r'(\D*)', price_str)
        if match:
            return match.group(0)
        else:
            return None
    except Exception:
        return None


# Tous les livres par catégorie, dans un dataframe
def get_all_books_with_category(url: str, session: requests.Session):
    response = session.get(url)
    tree = HTMLParser(response.text)

    # Obtention des catégories
    cats = tree.css_first("aside").css_first("div.side_categories").css_first("ul").css_first("li").css_first("ul")
    links = cats.css("a")

    i=1
    length = len(links)
    df_list = [] # Liste de dataframes

    # On parcourt les catégories une à une et on récupère les livres qu'elles contiennent
    for lien in links:
        url_to_go = urljoin(url, lien.attributes.get("href"))
        category = lien.text().strip()

        logger.info(f"Scraping: link {i} of {length}...")
        df_list.append(get_books_in_one_page(url=url_to_go, category=category, category_link=url_to_go, session=session, go_next=True))
        i += 1

    return pd.concat(df_list, axis=0).reset_index().drop(["index"], axis='columns')



# Catégories qui ont moins de x livres
def get_categories_with_less_than(url:str, x: int, session: requests.Session):
    cats_and_books_count = get_categories_and_books_count(url, session=session)
    return cats_and_books_count[cats_and_books_count["books_count"] < x].drop(["category_link"], axis='columns').reset_index()


# Catégories et nombre de livres
def get_categories_and_books_count(url: str, session: requests.Session):
    response = session.get(url)
    tree = HTMLParser(response.text)

    cat_dict = {"category":[], "books_count":[], "category_link":[]}

    cats = tree.css_first("aside").css_first("div.side_categories").css_first("ul").css_first("li").css_first("ul")
    links = cats.css("a")

    root_url = url if url.endswith("/") else f'{url}/'
    i=1
    length = len(links)
    for lien in links:
        url_to_go = f'{root_url}{lien.attributes.get("href")}'
        category = lien.text().strip()

        logger.info(f"Scraping: link {i} of {length}...")
        books_count = get_books_count_in_one_page(url_to_go, session=session)
        i += 1

        cat_dict["category"].append(category)
        cat_dict["books_count"].append(books_count)
        cat_dict["category_link"].append(url_to_go)

    return pd.DataFrame.from_dict(cat_dict)


# Liste des catégories de livres
def get_categories(url: str, session: requests.Session):
    response = session.get(url)

    tree = HTMLParser(response.text)

    cats = tree.css_first("aside").css_first("div.side_categories").css_first("ul").css_first("li").css_first("ul")

    categories = [lien.text().strip() for lien in cats.css("a")]
    return categories


# Récupère les livres d'une page avec ses caractéristiques. Renvoie les données sous forme de dataframe
# Si l'attribut go_next est True alors la fonction va parcourir la pagination (toutes les pages suivantes) jusqu'à la fin
# Les attributs category et category_link sont nécessaires lorsqu'on veut spécifier qu'on est sur une page qui présente les livres d'une catégorie donnée
def get_books_in_one_page(url: str, category: str = None, category_link: str = None, session: requests.Session = None, go_next: bool = False):
    response = session.get(url)

    tree = HTMLParser(response.text)

    # Affichons le niveau de la pagination de la page actuelle
    pagination = tree.css_first(".pager .current")
    pagination = pagination.text().strip() if pagination else None
    logger.info(f"\t- {pagination}")

    # LES CARACTERISTIQUES DES LIVRES (Titre, catégorie, prix, notation, lien de l'image(vignette), disponibilité, etc.)
    livres_dict = {"book_id": [], "title": [], "category":[], "price":[], "rating":[], "availability":[], "stock":[], "description":[], "review_count":[], "cover_link":[], "thumbnail_link":[], "book_link":[], "category_link":[]}
    livres_soup = tree.css_first("section").css_first("ol").css("li")
    
    book_count = 1

    for ls in livres_soup:
        book_title = ls.css_first("h3").css_first("a").attributes.get("title")
        book_link = ls.css_first("h3").css_first("a").attributes.get("href")
        book_link = urljoin(url, book_link)
        thumbnail_link = ls.css_first("div.image_container").css_first("img").attributes.get("src")
        disponibilite = ls.css_first("p.instock.availability").text().strip()
        prix = ls.css_first("p.price_color").text().strip()
        notation = ls.css_first(".star-rating").attributes.get("class")
        if notation is not None and len(notation) == 2:
            try:
                notation = w2n.word_to_num(notation[1])
            except Exception as e:
                notation = notation[1]
                logger.warning(f"Impossible de convertir la note du livre {book_title} en nombre.")
        else:
            notation = None

        livres_dict["title"].append(book_title)
        livres_dict["price"].append(prix)
        livres_dict["rating"].append(notation)
        livres_dict["thumbnail_link"].append(urljoin(url, thumbnail_link))
        livres_dict["book_link"].append(book_link)
        livres_dict["availability"].append(disponibilite)

        # Obtention des autres infos sur la page de présentation du livre
        logger.info(f"\t\t- scraping book {book_count}")
        book_count += 1
        comp_data = get_one_book(book_link, session=session)

        livres_dict["category"].append(category if category else comp_data["category"])
        livres_dict["category_link"].append(category_link if category_link else comp_data["category_link"])

        livres_dict["book_id"].append(comp_data["book_id"])
        livres_dict["description"].append(comp_data["description"])
        livres_dict["stock"].append(comp_data["stock"])
        livres_dict["review_count"].append(comp_data["review_count"])
        livres_dict["cover_link"].append(comp_data["cover_link"])

    livres_df = pd.DataFrame.from_dict(livres_dict)

    if go_next: # On parcourt les pages suivantes
        lien_next = tree.css_first(".pager .next a")
        if lien_next:
            lien_next = urljoin(url, lien_next.attributes.get("href"))
            next_df = get_books_in_one_page(url=lien_next, category=category, category_link=category_link, session=session, go_next=True)
            return pd.concat([livres_df, next_df], axis=0).reset_index().drop(["index"], axis='columns')
        else: # il n'y a pas de page suivante
            return livres_df        

    else:
        return livres_df



# Nombre de livres affichés dans une page
def get_books_count_in_one_page(url: str, session: requests.Session):
    try:
        response = session.get(url)
        tree = HTMLParser(response.text)
        livres_soup = tree.css_first("section").css_first("ol").css("li")
        return len(livres_soup)
    except Exception as e:
        logger.error(f"Une erreur est survenue dans la fonction 'get_books_count_in_one_page': {e}")
        return 0


# Récupère les caractéristiques d'un livre. Renvoie les données sous forme de dictionnaire
# Le paramètre url est la l'url de la page de présentation dudit livre
def get_one_book(url: str, session: requests.Session = None):
    response = session.get(url)

    tree = HTMLParser(response.text)

    # *. LES CARACTERISTIQUES DU LIVRE (id, description, qté en stock, lien de l'image, nombre de commentaires)
    data = dict()    

    try:
        data["book_id"] = extraire_id_livre(url)

        data["cover_link"] = tree.css_first("div.thumbnail img").attributes.get("src")
        data["cover_link"] = urljoin(url, data["cover_link"])

        data["description"] = tree.css_first("div#product_description + p")
        data["description"] = data["description"].text().strip() if data["description"] else None

        category = tree.css_first("ul.breadcrumb li:nth-child(3) a")
        if category:
            data["category"] = category.text().strip()
            data["category_link"] = urljoin(url, category.attributes.get("href"))
        else:
            data["category"] = None
            data["category_link"] = None

        stock = tree.css_first(".instock.availability")
        stock = stock.text().strip() if stock else None
        match = re.search(r'([0-9]+)\s+available', stock)
        if match:
            data["stock"] = int(match.group(1))
        else:
            data["stock"] = None
        
        # Sélection de la dernière ligne du tableau et extraction du texte de la balise <td>
        dernier_review = tree.css_first("table.table tr:last-child td")
        data["review_count"] = int(dernier_review.text().strip()) if dernier_review else None
        
    except Exception as e:
        logger.error(f"""Erreur lors de l'extraction des données du livre {data['book_id']}
                \nA l'adresse: {url}""")
        logger.error(f":{e}")

    return data

