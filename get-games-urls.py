#!/usr/bin/env python3.8

import requests
import time
import argparse
import datetime
from bs4 import BeautifulSoup

BASE_URL = "https://globalgamejam.org"

# Argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("-o", "--output", type=argparse.FileType('w'), default=f"url-list.txt", help="Output file")
parser.add_argument("-y", "--year", type=int, default=datetime.datetime.now().year, help="Year of the game jam")
args = parser.parse_args()

def request(url):
    print(url)
    response = requests.get(url)
    if response.status_code != 200:
        raise RuntimeError(f"Request failed with error code {response.status_code}")
    return response.text

def get_games_list():
    game_list = []

    # Get list of game per country
    page=0
    while True:
        text = request(f"{BASE_URL}/{args.year}/games?title=&country=All&city=&tools=All&diversifier=All&platforms=All&page={page}")
        soup = BeautifulSoup(text, "lxml")
        l = soup.find("div", {"class":"l-content--inner"}).find("div", {"class": "item-list"})
        if not l:
            break
        l = l.find_all("a")
        for a in l:
            game_list.append(a.get("href"))
        page += 1
    return game_list

l = get_games_list()

with args.output as output_file:
    for url in l:
        output_file.write(f"{BASE_URL}{url}\n")
