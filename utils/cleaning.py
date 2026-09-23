"""
Data cleaning utilities for videogame market analysis.

This module provides functions to clean and parse data from the Steam
and Video Games Sales datasets.
"""

import ast
from datetime import datetime
from typing import Any, Dict, List, Tuple, Union

import pandas as pd


def parse_string_list(value: Any) -> List[Any]:
    """
    Parses a string representation of a list into a Python list.

    Handles NaN, None, and empty strings by returning an empty list.
    Uses ast.literal_eval with a fallback to simple string splitting if needed.

    Args:
        value (Any): The string representation of a list (e.g., "['Action', 'RPG']").
            Can also be NaN or None.

    Returns:
        List[Any]: A Python list extracted from the string, or an empty list if
            the input is invalid or null.

    Examples:
        >>> parse_string_list("['Action', 'RPG']")
        ['Action', 'RPG']
        >>> parse_string_list(None)
        []
    """
    if pd.isna(value) or value is None or value == "":
        return []
    
    if isinstance(value, list):
        return value

    if not isinstance(value, str):
        return []

    try:
        parsed = ast.literal_eval(value)
        if isinstance(parsed, list):
            return parsed
        return []
    except (ValueError, SyntaxError):
        # Fallback if literal_eval fails
        cleaned = value.strip("[]")
        if not cleaned:
            return []
        return [item.strip(" '\"") for item in cleaned.split(",")]


def parse_tag_dict(value: Any) -> Dict[Any, Any]:
    """
    Parses a string representation of a dictionary into a Python dictionary.

    Handles NaN, None, and empty strings by returning an empty dictionary.

    Args:
        value (Any): The string representation of a dictionary 
            (e.g., "{'FPS': 90857, 'Shooter': 65397}").

    Returns:
        Dict[Any, Any]: A Python dictionary extracted from the string, or an
            empty dictionary if the input is invalid or null.

    Examples:
        >>> parse_tag_dict("{'FPS': 90857}")
        {'FPS': 90857}
        >>> parse_tag_dict(pd.NA)
        {}
    """
    if pd.isna(value) or value is None or value == "":
        return {}
        
    if isinstance(value, dict):
        return value
        
    if not isinstance(value, str):
        return {}

    try:
        parsed = ast.literal_eval(value)
        if isinstance(parsed, dict):
            return parsed
        return {}
    except (ValueError, SyntaxError):
        return {}


def parse_owner_range(value: Any) -> Tuple[int, int, int]:
    """
    Parses an owner range string into lower, upper, and midpoint values.

    Args:
        value (Any): The owner range string (e.g., "20000 - 50000").

    Returns:
        Tuple[int, int, int]: A tuple containing (lower_bound, upper_bound, midpoint).
            If parsing fails, returns (0, 0, 0).

    Examples:
        >>> parse_owner_range("20000 - 50000")
        (20000, 50000, 35000)
        >>> parse_owner_range("0 - 0")
        (0, 0, 0)
    """
    if pd.isna(value) or not isinstance(value, str):
        return (0, 0, 0)

    parts = value.split("-")
    if len(parts) == 2:
        try:
            lower = int(parts[0].strip().replace(",", ""))
            upper = int(parts[1].strip().replace(",", ""))
            midpoint = (lower + upper) // 2
            return (lower, upper, midpoint)
        except ValueError:
            pass
            
    return (0, 0, 0)


def categorize_price(price: float) -> str:
    """
    Categorizes a game's price into a discrete tier.

    Categories:
        - 'Free' (0)
        - 'Budget' (0.01 - 4.99)
        - 'Mid' (5 - 14.99)
        - 'Premium' (15 - 29.99)
        - 'AAA' (30+)

    Args:
        price (float): The price of the game.

    Returns:
        str: The price category, or 'Unknown' if price is NaN.

    Examples:
        >>> categorize_price(0.0)
        'Free'
        >>> categorize_price(19.99)
        'Premium'
    """
    if pd.isna(price):
        return "Unknown"
        
    try:
        p = float(price)
        if p == 0:
            return "Free"
        elif 0 < p < 5.0:
            return "Budget"
        elif 5.0 <= p < 15.0:
            return "Mid"
        elif 15.0 <= p < 30.0:
            return "Premium"
        elif p >= 30.0:
            return "AAA"
        else:
            return "Unknown"
    except (ValueError, TypeError):
        return "Unknown"


def parse_sales_date(date_str: Any) -> Union[datetime, pd.Timestamp, Any]:
    """
    Parses a sales date string in 'dd-mm-yyyy' format to a datetime object.

    Args:
        date_str (Any): The date string to parse.

    Returns:
        datetime or pd.NaT: The parsed datetime object, or pd.NaT if the input
            is missing or invalid.

    Examples:
        >>> parse_sales_date("25-12-2020")
        datetime.datetime(2020, 12, 25, 0, 0)
        >>> parse_sales_date(None)
        NaT
    """
    if pd.isna(date_str) or not isinstance(date_str, str):
        return pd.NaT

    try:
        return datetime.strptime(date_str.strip(), "%d-%m-%Y")
    except ValueError:
        try:
            return pd.to_datetime(date_str, errors='coerce', dayfirst=True)
        except Exception:
            return pd.NaT


def standardize_console_name(console: str) -> str:
    """
    Standardizes a console abbreviation to its full name.

    Args:
        console (str): The console abbreviation (e.g., 'PS4').

    Returns:
        str: The full console name, or the original string if not found in mappings.

    Examples:
        >>> standardize_console_name("PS4")
        'PlayStation 4'
        >>> standardize_console_name("NS")
        'Nintendo Switch'
    """
    if pd.isna(console) or not isinstance(console, str):
        return "Unknown"
        
    mappings = {
        "PS": "PlayStation",
        "PS2": "PlayStation 2",
        "PS3": "PlayStation 3",
        "PS4": "PlayStation 4",
        "PS5": "PlayStation 5",
        "PSP": "PSP",
        "PSV": "PS Vita",
        "PSN": "PlayStation Network",
        "XB": "Xbox",
        "X360": "Xbox 360",
        "XOne": "Xbox One",
        "XS": "Xbox Series",
        "XBL": "Xbox Live",
        "NS": "Nintendo Switch",
        "Wii": "Wii",
        "WiiU": "Wii U",
        "DS": "Nintendo DS",
        "3DS": "Nintendo 3DS",
        "GBA": "Game Boy Advance",
        "GB": "Game Boy",
        "GBC": "Game Boy Color",
        "GC": "GameCube",
        "N64": "Nintendo 64",
        "SNES": "Super NES",
        "NES": "NES",
        "PC": "PC",
        "DC": "Dreamcast",
        "SAT": "Saturn",
        "GEN": "Genesis",
        "GG": "Game Gear",
        "Mob": "Mobile",
        "iOS": "iOS",
        "AND": "Android"
    }
    
    return mappings.get(console.strip(), console.strip())


def categorize_console_generation(console: str) -> str:
    """
    Maps a console to its generation number or name.

    Args:
        console (str): The console abbreviation or full name.

    Returns:
        str: The console generation, or 'Unknown' if not matched.

    Examples:
        >>> categorize_console_generation("SNES")
        '4th Gen'
        >>> categorize_console_generation("PS4")
        '8th Gen'
    """
    if pd.isna(console) or not isinstance(console, str):
        return "Unknown"
        
    c = console.strip().upper()
    
    generations = {
        '3rd Gen': ['NES', 'MASTER SYSTEM'],
        '4th Gen': ['SNES', 'SUPER NES', 'GEN', 'GENESIS', 'GB', 'GAME BOY', 'GG', 'GAME GEAR'],
        '5th Gen': ['PS', 'PLAYSTATION', 'N64', 'NINTENDO 64', 'SAT', 'SATURN', 'GBC', 'GAME BOY COLOR'],
        '6th Gen': ['PS2', 'PLAYSTATION 2', 'XB', 'XBOX', 'GC', 'GAMECUBE', 'DC', 'DREAMCAST', 'GBA', 'GAME BOY ADVANCE'],
        '7th Gen': ['PS3', 'PLAYSTATION 3', 'X360', 'XBOX 360', 'WII', 'DS', 'NINTENDO DS', 'PSP'],
        '8th Gen': ['PS4', 'PLAYSTATION 4', 'XONE', 'XBOX ONE', 'WIIU', 'WII U', '3DS', 'NINTENDO 3DS', 'PSV', 'PS VITA'],
        '9th Gen': ['PS5', 'PLAYSTATION 5', 'XS', 'XBOX SERIES', 'NS', 'NINTENDO SWITCH'],
        'PC': ['PC'],
        'Mobile': ['MOB', 'MOBILE', 'IOS', 'AND', 'ANDROID']
    }
    
    for gen, consoles in generations.items():
        if c in consoles:
            return gen
            
    return "Unknown"


def get_console_manufacturer(console: str) -> str:
    """
    Returns the manufacturer for a given console.

    Args:
        console (str): The console abbreviation or full name.

    Returns:
        str: The manufacturer ('Sony', 'Nintendo', 'Microsoft', 'Sega', 'PC', 'Mobile', or 'Other').

    Examples:
        >>> get_console_manufacturer("PS2")
        'Sony'
        >>> get_console_manufacturer("GBA")
        'Nintendo'
    """
    if pd.isna(console) or not isinstance(console, str):
        return "Other"
        
    c = console.strip().upper()
    
    manufacturers = {
        'Sony': ['PS', 'PLAYSTATION', 'PS2', 'PLAYSTATION 2', 'PS3', 'PLAYSTATION 3', 
                 'PS4', 'PLAYSTATION 4', 'PS5', 'PLAYSTATION 5', 'PSP', 'PSV', 'PS VITA', 'PSN'],
        'Nintendo': ['NES', 'SNES', 'SUPER NES', 'N64', 'NINTENDO 64', 'GC', 'GAMECUBE', 
                     'WII', 'WIIU', 'WII U', 'NS', 'NINTENDO SWITCH', 'GB', 'GAME BOY', 
                     'GBC', 'GAME BOY COLOR', 'GBA', 'GAME BOY ADVANCE', 'DS', 'NINTENDO DS', 
                     '3DS', 'NINTENDO 3DS'],
        'Microsoft': ['XB', 'XBOX', 'X360', 'XBOX 360', 'XONE', 'XBOX ONE', 'XS', 'XBOX SERIES', 'XBL'],
        'Sega': ['MASTER SYSTEM', 'GEN', 'GENESIS', 'SAT', 'SATURN', 'DC', 'DREAMCAST', 'GG', 'GAME GEAR'],
        'PC': ['PC'],
        'Mobile': ['MOB', 'MOBILE', 'IOS', 'AND', 'ANDROID']
    }
    
    for mfg, consoles in manufacturers.items():
        if c in consoles:
            return mfg
            
    return "Other"
