from enum import Enum

class DeckType(Enum):
    CHANCE = 0
    COMMUNITY_CHEST = 1

class PlayerTokens(Enum):
    BATTLESHIP = "battleship"
    BOOT = "boot"
    CANNON = "cannon"
    HORSE = "horse"
    IRON = "iron"
    RACECAR = "racecar"
    DOG = "dog"
    THIMBLE = "thimble"
    TOPHAT = "top hat"
    WHEELBARROW = "wheelbarrow"
    
class OwnershipDegree(Enum):
    NONE = 0
    ONE = 1 # trumped by close_to_monopoly (in case of brown and dark blue)
    ALMOST_MONOPOLY = 2
    MONOPOLY = 3

class Colors(Enum):
    BROWN = "137"
    LIGHTBLUE = "80"
    PINK = "162"
    ORANGE = "208"
    RED = "196"
    YELLOW = "226"
    GREEN = "41"
    DARKBLUE = "33"
    RR = "249"
    UTILITY = "250"
    WHITE = "251"

# locations have the same value as their board space index, but for best practice,
# use the Board class's board space variable to access locations instead. When needing
# to go to a precise location, these can be used, as long as the destination isn't chance
# or community chest, since there are multiple board spaces for both.
class LocationKeys(Enum):
    GO = "Go"
    MEDITERRANEAN = "Mediterranean Avenue"
    COMMUNITY_CHEST = "Community Chest"
    BALTIC = "Baltic Avenue"
    INCOME_TAX = "Income Tax"
    READING_RR = "Reading Railroad"
    ORIENTAL = "Oriental Avenue"
    CHANCE = "Chance"
    VERMONT = "Vermont Avenue"
    CONNECTICUT = "Connecticut Avenue"
    VISITING_JAIL = "Visiting Jail"
    ST_CHARLES = "St. Charles Place"
    ELECTRIC = "Electric Company"
    STATES = "States Avenue"
    VIRGINIA = "Virginia Avenue"
    PENNSYLVANIA_RR = "Pennsylvania Railroad"
    ST_JAMES = "St. James Place"
    TENNESSEE = "Tennessee Avenue"
    NEW_YORK = "New York Avenue"
    FREE_PARKING = "Free Parking"
    KENTUCKY = "Kentucky Avenue"
    INDIANA = "Indiana Avenue"
    ILLINOIS = "Illinois Avenue"
    BO_RR = "B. & O. Railroad"
    ATLANTIC = "Atlantic Avenue"
    VENTNOR = "Ventnor Avenue"
    WATER = "Water Works"
    MARVIN = "Marvin Gardens"
    GO_TO_JAIL = "Go to Jail"
    PACIFIC = "Pacific Avenue"
    NORTH_CAROLINA = "North Carolina Avenue"
    PENNSYLVANIA = "Pennsylvania Avenue"
    SHORT_LINE = "Short Line"
    PARK_PLACE = "Park Place"
    LUXURY_TAX = "Luxury Tax"
    BOARDWALK = "Boardwalk"
    JAIL = "Jail"
