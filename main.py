from utils_2 import *
import time

url = "https://books.toscrape.com"

# livres_df = get_books_in_one_page(url)
# livres_df.to_excel("Livres.xlsx")
# print(livres_df)

# categories = get_categories(url)
# print("Il y a ", len(categories), "catégorie(s).")
# print(categories)

# nb = get_books_count_in_one_page(url)
# print(nb)

# cats_and_books_count = get_categories_and_books_count(url)
# print(cats_and_books_count)
# cats_and_books_count.to_excel("cats_and_books_count.xlsx")


# Catégories qui ont moins de 10 livres
# cats = get_categories_with_less_than(url, 10)
# print(cats)


def main():
    # lien="https://books.toscrape.com/catalogue/its-only-the-himalayas_981/index.html"
    # print(extraire_id_livre(lien))
    # data=dict()
    # print(data["magie"])
    with requests.Session() as session:
        debut = time.perf_counter()
        # df = get_all_books_with_category(url, session=session)
        df = get_books_in_one_page(url, session=session, go_next=True)
        fin = time.perf_counter()
        print(f"Durée d'exécution de la fonction 'get_books_in_one_page': {fin - debut} secondes.")

        print(df.columns)

        for col in ['title', 'price', 'description']:
            df[col] = df[col].apply(lambda x: x.encode('latin1').decode('utf-8') if isinstance(x, str) else x)

        df.to_excel("all_books_with_category.xlsx", index=False)
        df.to_csv("all_books_with_category.csv", sep=";", index=False, encoding="utf-8")
        print("Enregistrement terminé.")


if __name__ == "__main__":
    # main()
    df = pd.read_excel("all_books_with_category_e.xlsx")
    # for col in ['title', 'price', 'description']:
    #     df[col] = df[col].apply(lambda x: x.encode('latin1').decode('utf-8') if isinstance(x, str) else x)
    # df["currency"] = df["price"].apply(extract_currency)
    # df["price"] = df["price"].apply(extract_price)

    # print(df[['title', 'price', 'currency', 'description']].head())
    # df.to_excel("all_books_with_category_e.xlsx", index=False)
    print(f"Nombre total de livres: {df["stock"].sum()}")
    print(f"Prix total des livres: {df["currency"][0]}{(df["stock"]*df["price"]).sum()}")
