#!/usr/bin/env python

import argparse
import json
import pandas as pd
import geopandas
import descartes
import sys
import numpy as np
from pandas import DataFrame
import matplotlib.pyplot as plt

from country_mapping import COUNTRY_NAME_MAP

# Limits to consider as in the "Others" category
ENGINE_NB_GAMES_LIMIT = 100
ENGINES = [
    "A-Frame",
    "Adventure Game Studio",
    "Bitsy game maker",
    "Clickteam Fusion",
    "Cocos 2D",
    "Construct",
    "Corona SDK",
    "CryEngine",
    "Defold",
    "Enchant.JS",
    "Game Salad (Mac desktop, iPhone, iPad)",
    "GameMaker (any product)",
    "Godot Engine",
    "Greenfoot",
    "Haxe",
    "Houdini",
    "Inform",
    "Intel XDK",
    "LibGDX",
    "Play Canvas",
    "Processing",
    "Puzzlescript",
    "RPG Maker",
    "Ren/Py",
    "SDL",
    "Scratch",
    "Stencyl",
    "Tabletop Technology",
    "Unity (any product)",
    "Unreal Engine",
    "Xenko"
]

DIMENSIONS = ["2D", "2.5D", "3D"]

# Argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("input", type=argparse.FileType('r'), help="Input JSON file")
args = parser.parse_args()

def _get_world_dataframe():
    # Get world map
    world = geopandas.read_file(geopandas.datasets.get_path('naturalearth_lowres'))
    # Handmade fixes
    world.at[world["name"] == "France", "iso_a3"] = "FRA"
    world.at[world["name"] == "Uganda", "iso_a3"] = "UGA"
    world.at[world["name"] == "Norway", "iso_a3"] = "NOR"
    world.at[world["name"] == "N. Cyprus", "iso_a3"] = "CYP"
    world.at[world["name"] == "Kosovo", "iso_a3"] = "XKX"
    world = world.set_index("iso_a3")
    return world

def _map_to_map(code):
    mapping = {
            "BHR" : "SAU",
            "GGY" : "GBR",
            "HKG": "CHN",
            "MLT" : "ITA",
            "MUS" : "MDG",
            "REU" : "FRA",
            "SGP" : "MYS"
    }
    return mapping[code] if code in mapping else code


def main():
    with args.input as input_file:
        # Open the file and make it a dataframe
        games_data = json.loads(input_file.read())
        df = DataFrame.from_dict(games_data)
        df["game_id"] = df.index
        df = df.explode("tools_and_technologies")
        df = df.drop_duplicates(subset=["game_id", "tools_and_technologies"])
        df = df.explode("game_tags")
        df = df.drop_duplicates(subset=["game_id", "game_tags"])
        df["jam_site_country_code"] = df["jam_site_country"].apply(lambda x : COUNTRY_NAME_MAP[x])
        df = df.reset_index()

        # Show proportion of each engine
        per_engine_df = df[df["tools_and_technologies"].isin(ENGINES)]
        per_engine_df = per_engine_df.groupby("tools_and_technologies").size()
        per_engine_df = per_engine_df.groupby(lambda engine : "Others" if per_engine_df[engine] < ENGINE_NB_GAMES_LIMIT else engine).sum()
        per_engine_df = per_engine_df.rename("Number of games")
        per_engine_df.index = per_engine_df.index.rename("Game engine")

        per_engine_df.plot.bar(title="Number of games made per game engine")
        plt.xticks(rotation='horizontal')
        plt.subplots_adjust(left=0.05, right=0.98, top=0.96, bottom=0.06)
        plt.show()

        per_engine_df.plot.pie(title="Proportion of games made per game engine", autopct='%1.0f%%')
        plt.subplots_adjust(left=0.05, right=0.98, top=0.96, bottom=0.06)
        plt.show()

        # Show per-engine type game dimensionnality
        per_engine_dimensions_df = df[df["tools_and_technologies"].isin(ENGINES)]
        per_engine_dimensions_df = df[df["game_tags"].isin(DIMENSIONS)]
        per_engine_dimensions_df = per_engine_dimensions_df.groupby(["tools_and_technologies", "game_tags"]).size().unstack()
        per_engine_dimensions_df = per_engine_dimensions_df.groupby(lambda engine : "Others" if engine not in list(per_engine_df.index) else engine).sum()
        per_engine_dimensions_df = per_engine_dimensions_df.div(per_engine_dimensions_df.sum(axis=1), axis=0)
        per_engine_dimensions_df.index = per_engine_dimensions_df.index.rename("Game engine")
        per_engine_dimensions_df.columns = per_engine_dimensions_df.columns.rename("Dimensions")

        per_engine_dimensions_df.plot.bar(title="Proportion, per game-engine, of the games dimensionnality", stacked=True)
        plt.xticks(rotation='horizontal')
        plt.subplots_adjust(left=0.05, right=0.98, top=0.96, bottom=0.06)
        plt.show()

        # Show per-engine tags
        per_engine_dimensions_df = df[df["tools_and_technologies"].isin(ENGINES)]
        per_engine_dimensions_df = df[~df["game_tags"].isin(DIMENSIONS)]
        per_engine_dimensions_df = per_engine_dimensions_df.groupby(["tools_and_technologies", "game_tags"]).size().unstack()
        per_engine_dimensions_df = per_engine_dimensions_df.groupby(lambda engine : "Others" if engine not in list(per_engine_df.index) else engine).sum()
        per_engine_dimensions_df.index = per_engine_dimensions_df.index.rename("Game engine")
        per_engine_dimensions_df.columns = per_engine_dimensions_df.columns.rename("Game tag")

        per_engine_dimensions_df.plot.bar(title="Number of games using a given tag per engine")
        plt.xticks(rotation='horizontal')
        plt.subplots_adjust(left=0.05, right=0.98, top=0.96, bottom=0.06)
        plt.show()

        # Show per-country Godot's adoption
        per_country_df = df[df["tools_and_technologies"].isin(ENGINES)]
        per_country_df["jam_site_country_code"] = per_country_df["jam_site_country_code"].apply(_map_to_map)
        per_country_df = per_country_df.groupby(["jam_site_country_code", "tools_and_technologies"]).size().unstack()
        per_country_df = per_country_df.fillna(0)
        per_country_df = per_country_df[per_country_df.sum(axis=1) > 5]
        per_country_df = per_country_df.div(per_country_df.sum(axis=1), axis=0)

        world = _get_world_dataframe()
        per_country_df = world.merge(per_country_df, how="inner",left_index=True, right_index=True, indicator=True)

        base = world.plot(color='#BBBBBB')
        per_country_df.plot(ax=base, column="Godot Engine", legend=True)
        #per_country_df.plot(ax=base, column="Unity (any product)", legend=True)
        plt.title("Proportion, in each country, of games made with Godot")
        plt.show()

        return

main()
