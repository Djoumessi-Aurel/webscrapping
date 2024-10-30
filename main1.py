import requests

try:
    response = requests.get("https://softweight.vercel.app/")
    print(response)
    print("\n## ENCODING:",response.encoding, "##")
    print("\n## HEADERS:", response.headers, "##")
    # print("\n\n## CONTENT ##")
    # print(response.text)
    response.raise_for_status()
    with open("fichier2.html", "w") as f:
        f.write(response.text)
except requests.exceptions.HTTPError as errh:
    print("Http Error:", errh)
except requests.exceptions.ConnectionError as errc:
    print("Error Connecting:", errc)
except requests.exceptions.Timeout as errt:
    print("Timeout Error:", errt)
except requests.exceptions.RequestException as err:
    print("Oops! Something Else:", err)
except Exception as e:
    print("OTHER ERROR:", e)

