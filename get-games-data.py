#!/usr/bin/env python3.8

import asyncio
import time
import argparse
import re
import json
import httpx
from threading import get_ident, Thread, RLock
from bs4 import BeautifulSoup

# Argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("input", type=argparse.FileType('r'), help="Input file with list of urls to request")
parser.add_argument("-o", "--output", type=argparse.FileType('w'), default="games-data.json", help="Output file")
args = parser.parse_args()

async def request(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30)
        if response.status_code != 200:
            raise RuntimeError(f"Request failed with error code {response.status_code}")
        return response.text

splitter = re.compile(r'(?:[^,(]|\([^)]*\))+')

def parse_field(label, value):
    content = [val.contents[0] for val in value.find_all("div", {"class":"field__item"}) if val.contents]
    if label == "description":
        return {label : str(content[0])}
    elif label == "jam_site":
        return {label : str(content[0].contents[0]), "jam_site_url" : content[0].get("href")}
    elif label == "jam_year":
        return {label : int(content[0])}
    elif label == "diversifiers":
        return {label : content}
    elif label == "platforms":
        return {label : [x.strip() for x in splitter.findall(content[0].contents[0])]}
    elif label == "tools_and_technologies":
        return {label : [x.strip() for x in splitter.findall(content[0].contents[0])]} # TODO there might be a bug here
    elif label == "credits":
        return {label : str(content[0])}
    elif label == "game_tags":
        return {label : [x.strip() for x in splitter.findall(str(content[0]))]}
    elif label == "executable":
        return None
    elif label == "source_files":
        return None
    elif label == "installation_instructions":
        return None
    elif label == "game_stills":
        return None
    elif label == "repository_link":
        return None
    elif label == "game_website":
        return None
    elif label == "technology_notes":
        return None
    elif label == "video_link":
        return None
    elif label == "download_link":
        return None
    elif label == "play_now!":
        return None
    elif label == "embed_code":
        return None
    else:
        print("UNKNOWN LABEL " + label)
        return None

# Get per game data
async def request_game_data(games_data, url):
    print(f"Requesting game data {url}")
    try:
        text = await request(url)
    except RuntimeError:
        return

    soup = BeautifulSoup(text, "lxml")
    fields = soup.find("article").find_all("div", {"class":"field"})
    game_data = {}
    for field in fields:
        label = field.find("div", {"class":"field__label"})
        if not label:
            label = "description"
        else:
            label = str(label.contents[0])
        label = label.strip().replace(':','').lower().replace(" ","_")
        value = parse_field(label, field.find("div", {"class":"field__items"}))
        if value:
            game_data.update(value)

    games_data.append(game_data)

async def request_jam_site_country(jam_site_countries, site_url):
    if site_url in jam_site_countries:
        return

    print(f"Requesting jam site data {site_url}")
    jam_site_countries[site_url] = "PROCESSING"
    text = await request(site_url)
    soup = BeautifulSoup(text, "lxml")
    country = str(soup.find("div", {"class":"jam-site-address"}).find("div").contents[0])
    jam_site_countries[site_url] = country

async def request_games_data(games_data, urls, chunk_size):
    chunks = [urls[i:i + chunk_size] for i in range(0, len(urls), chunk_size)]
    for chunk_id, chunk in enumerate(chunks):
        print(f"Handling chunk {chunk_id+1} / {len(chunks)}")
        tasks = [asyncio.create_task(request_game_data(games_data, url)) for url in chunk]
        for task in tasks:
            await task

    # Get the per-site data
    jam_site_countries = {}
    chunks = [games_data[i:i + chunk_size] for i in range(0, len(games_data), chunk_size)]
    for chunk_id, chunk in enumerate(chunks):
        print(f"Handling chunk {chunk_id+1} / {len(chunks)}")
        tasks = [asyncio.create_task(request_jam_site_country(jam_site_countries, game_data["jam_site_url"])) for game_data in chunk]
        for task in tasks:
            await task

    # Put the country in the data
    for game_data in games_data:
        game_data["jam_site_country"] = jam_site_countries[game_data["jam_site_url"]]

#Read the input file
urls = [url.strip() for url in args.input]
games_data = []
asyncio.run(request_games_data(games_data, urls, 100))

# Print results to a file
with args.output as output_file:
    output_file.write(json.dumps(games_data, indent=2))
