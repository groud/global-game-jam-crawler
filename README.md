# Global Game Jam crawler

A crawler to retrieve games data from the Global Game Jam website.

It consists of two scripts:
- `get-games-urls.py` produces a text file with the list of all games ulrs
- `get-games-data.py` uses the text file from `get-games-urls.py` to get the
  data from each game, and produces a JSON file with this data.

Each of those scripts can be run with the `-h` option to retrieve usage
information.

## Dependencies

Install required dependencies with:
```
pip install -r requirements.txt
```

This software requires python 3.8 to run.

## License

This project is available under the GPLv3 license.
