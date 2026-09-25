import requests

API_KEY = "semrtkn-pat-0Ns1PT7sQm-Cs69iPQ0iLA-rdZc42pWNmaYEeb6piFgADaP5z_eYH7V"
DOMAIN = "inspiria.edu.in"

url = f"https://api.semrush.com/?type=domain_ranks&key={API_KEY}&export_columns=Or,Ot,Oc,Ad,At,Ac&domain={DOMAIN}&database=us"
response = requests.get(url)
print(response.status_code)
print(response.text[:200])
