import os

import requests
from requests.auth import HTTPBasicAuth

AUTH_BASE_BY_ENV = {
    "prelive": "https://prelive-oauth2.quran.foundation",
    "production": "https://oauth2.quran.foundation",
}

env = "production"
if env not in AUTH_BASE_BY_ENV:
    raise ValueError(
        f"Invalid QF_ENV value: {env!r}. Expected 'prelive' or 'production'."
    )

AUTH_BASE_URL = AUTH_BASE_BY_ENV[env]

response = requests.post(
    f"{AUTH_BASE_URL}/oauth2/token",
    auth=HTTPBasicAuth(
        "49ca33ef-8476-4e2f-b47c-d7274e937594",
        "Z.Ilh8B--H5BSfR96I-S5tHi8E",
    ),
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    data={
        "grant_type": "client_credentials",
        "scope": "content",
    },
    timeout=30,
)
response.raise_for_status()

token = response.json()
access_token = token["access_token"]
expires_in = token["expires_in"]

print("Token", access_token)



# import requests
# from data.data import comprehensive_surah_metadata

# response = requests.get("https://api.alquran.cloud/v1/quran/en.asad")

# if not response.ok:
#     raise Exception("Some error occured while fetching data")

# data = response.json()
# surahs = data['data']['surahs']


# revelationTypes = [surah["revelationType"] for surah in surahs]


# for i,surah in enumerate(comprehensive_surah_metadata):
#     surah['revelationType'] = revelationTypes[i]

# print(comprehensive_surah_metadata)