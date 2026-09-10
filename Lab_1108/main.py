import requests
import pandas as pd

 
def call_unknown_endpoint(url: str, params: dict):
    response: requests.Response = requests.get(
        url,
        params=params,
        timeout=10
    )
    response.raise_for_status()
    #print("Initiating payload dispatch...\n")
    #print(F"[STATUS]: {response.status_code}")
    #print(F"[EXECUTIONTIME]: {response.elapsed} ms")
    #print(F"[HEADERS]: {response.headers}")
 
    json_response = response.json()
    df = pd.json_normalize(json_response,  record_path=["items"])
    print(f"Normalized DataFrame: \n{df}")
    df.to_excel(
        "df_w_arrays.xlsx", index=False, sheet_name="Normalized Orders"
    )
    #print(json_response)
    #popular_repositories = json_response.get("items", [])
    #for repo in popular_repositories[:3]:
    #    print(f"Name: {repo['name']}")
    #    print(f"Description: {repo['description']}\n")
 
 
url = "https://api.github.com/search/repositories"
params={"q": "language:python", "sort": "stars", "order": "desc"}
 
try:
    call_unknown_endpoint(url, params)
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")