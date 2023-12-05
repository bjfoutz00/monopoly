from abc import abstractmethod
from collections import defaultdict
import random
import argparse
import time
from enums import DeckType, Colors, LocationKeys
from player import Player
from humanplayer import HumanPlayer
from aiplayer import AIPlayer
from cards import Deck
from trade_matrix import TradeMatrix
import settings

JAIL_BOARD_SPACE = 40
VISITING_JAIL_BOARD_SPACE = 10


class Location():
    def __init__(self, name, board_space, land, color=Colors.WHITE):
        self.name = name # Property enum value
        self.board_space = board_space # board_space index on board
        self.land = land # land function with player param
        self.color = color
        self.name_colored = f"\033[38;5;{self.color.value}m{self.name}\033[0;0m"

    @abstractmethod
    def land(self, player: Player, board, double_if_owned=False):
        pass



class RealEstate(Location):
    def __init__(self, name, board_space, cost, color, can_develop):
        super().__init__(name, board_space, self.land, color)
        self.cost = cost
        self.color = color
        self.can_develop = can_develop
        self.mortgage_amount = cost // 2
        self.unmortgage_amount = int(self.mortgage_amount * 1.1)
        self.is_mortgaged = False
        self.owner = None
   
    def land(self, player: Player, board, double_if_owned=False):
        if self.owner == player or self.is_mortgaged:
            return
        
        if self.owner is not None:
            rent = self.calculate_rent(board, double_if_owned)
            print(f"Player {player.player_number} must pay ${rent} rent to player {self.owner.player_number}")
            if not settings.fast:
                time.sleep(0.5)
            player.charge(rent)
            self.owner.add_money(rent)

        elif self.owner is None:
            if player.decide_purchase(self):
                print(f"Player {player.player_number} buys {self.name_colored}")
                if not settings.fast:
                    time.sleep(0.5)
                player.charge(self.cost)
                player.gain_real_estate(self)
            else:
                # do auction
                return True

    @abstractmethod
    def calculate_rent(self, board, double_if_owned=False):
        pass

    def mortgage(self):
        print(f"Player {self.owner.player_number} mortgages {self.name_colored}")
        if not settings.fast:
            time.sleep(0.5)
        self.is_mortgaged = True
        self.owner.add_money(self.mortgage_amount, False)
        self.owner.mortgaged_property_names.add(self.name)

    def unmortgage(self):
        print(f"Player {self.owner.player_number} unmortgages {self.name_colored}")
        if not settings.fast:
            time.sleep(0.5)
        self.owner.charge(self.unmortgage_amount)
        self.is_mortgaged = False
        self.owner.mortgaged_property_names.remove(self.name)
    
    def __lt__(self,other):
        return self.name < other.name

class Property(RealEstate):
    def __init__(self, name, board_space, cost, color, build_cost, rent):
        super().__init__(name, board_space, cost, color, True)
        self.build_cost = build_cost
        self.rent = rent # array of charges based on numHouses [base, 1, 2, 3, 4, hotel]
        self.num_houses = 0
    
    def calculate_rent(self, board, double_if_owned=False):
        if self.num_houses > 0:
            return self.rent[self.num_houses]
        if self.owner.has_full_set(self.color):
            return self.rent[0] * 2
        return self.rent[0]

    def build_house(self):
        print(f"Player {self.owner.player_number} builds a house on {self.name_colored}")
        if not settings.fast:
            time.sleep(0.5)
        self.owner.charge(self.build_cost)
        self.num_houses += 1

    def sell_house(self):
        print(f"Player {self.owner.player_number} sells a house on {self.name_colored}")
        if not settings.fast:
            time.sleep(0.5)
        self.owner.add_money(self.build_cost // 2, False)
        self.num_houses -= 1
            

class Railroad(RealEstate):
    def __init__(self, name, board_space):
        super().__init__(name, board_space, 200, Colors.RR, False)

    def calculate_rent(self, board, double=False):
        num_rrs = len(self.owner.properties_by_set[Colors.RR])
        rent = 25 * (2**(num_rrs-1)) # 25, 50, 100, 200
        return rent*2 if double else rent

class Utility(RealEstate):
    def __init__(self, name, board_space):
        super().__init__(name, board_space, 150, Colors.UTILITY, False)

    def calculate_rent(self, board, override):
        # override can happen from chance roll
        if self.owner.has_full_set(self.color) or override:
            return 10 * board.roll_total
        return 4 * board.roll_total
        
def nothing(player: Player, board, double_if_owned=False):
    return

def go_to_jail(player: Player, board, double_if_owned=False):
    board.send_to_jail(player)

def luxury_tax(player: Player, board, double_if_owned=False):
    player.charge(100)

def income_tax(player: Player, board, double_if_owned=False):
    tax = min(200, int(player.calculate_total_worth() * 0.1))
    player.charge(tax)

def draw_chance(player: Player, board, double_if_owned=False):
    board.chance_deck.draw(player, board)

def draw_community_chest(player: Player, board, double_if_owned=False):
    board.community_chest_deck.draw(player, board)


class Board():
    def __init__(self, players):
        self.players = players
        self.locations = self.init_locations()
        self.spaces = self.init_spaces()
        self.chance_deck = Deck(DeckType.CHANCE)
        self.community_chest_deck = Deck(DeckType.COMMUNITY_CHEST)
        self.roll_total = 0

    # map of each *unique* location and their "land" functions. 
    # keyed to LocationKeys enum
    def init_locations(self):
        return {
            LocationKeys.GO: Location(LocationKeys.GO.value, 0, nothing),
            LocationKeys.MEDITERRANEAN: Property(LocationKeys.MEDITERRANEAN.value, 1, 60, Colors.BROWN, 50, [2, 10, 30, 90, 160, 250]),
            LocationKeys.COMMUNITY_CHEST: Location(LocationKeys.COMMUNITY_CHEST.value, 2, draw_community_chest),
            LocationKeys.BALTIC: Property(LocationKeys.BALTIC.value, 3, 60, Colors.BROWN, 50, [4, 20, 60, 180, 320, 450]),
            LocationKeys.INCOME_TAX: Location(LocationKeys.INCOME_TAX.value, 4, income_tax),
            LocationKeys.READING_RR: Railroad(LocationKeys.READING_RR.value, 5),
            LocationKeys.ORIENTAL: Property(LocationKeys.ORIENTAL.value, 6, 100, Colors.LIGHTBLUE, 50, [6, 30, 90, 270, 400, 550]),
            LocationKeys.CHANCE: Location(LocationKeys.CHANCE.value, 7, draw_chance),
            LocationKeys.VERMONT: Property(LocationKeys.VERMONT.value, 8, 100, Colors.LIGHTBLUE, 50, [6, 30, 90, 270, 400, 550]),
            LocationKeys.CONNECTICUT: Property(LocationKeys.CONNECTICUT.value, 9, 120, Colors.LIGHTBLUE, 50, [8, 40, 100, 300, 450, 600]),
            LocationKeys.VISITING_JAIL: Location(LocationKeys.VISITING_JAIL.value, 10, nothing),
            LocationKeys.ST_CHARLES: Property(LocationKeys.ST_CHARLES.value, 11, 140, Colors.PINK, 100, [10, 50, 150, 450, 625, 750]),
            LocationKeys.ELECTRIC: Utility(LocationKeys.ELECTRIC.value, 12),
            LocationKeys.STATES: Property(LocationKeys.STATES.value, 13, 140, Colors.PINK, 100, [10, 50, 150, 450, 625, 750]),
            LocationKeys.VIRGINIA: Property(LocationKeys.VIRGINIA.value, 14, 160, Colors.PINK, 100, [12, 60, 180, 500, 700, 900]),
            LocationKeys.PENNSYLVANIA_RR: Railroad(LocationKeys.PENNSYLVANIA_RR.value, 15),
            LocationKeys.ST_JAMES: Property(LocationKeys.ST_JAMES.value, 16, 180, Colors.ORANGE, 100, [14, 70, 200, 550, 750, 950]),
            LocationKeys.TENNESSEE: Property(LocationKeys.TENNESSEE.value, 18, 180, Colors.ORANGE, 100, [14, 70, 200, 550, 750, 950]),
            LocationKeys.NEW_YORK: Property(LocationKeys.NEW_YORK.value, 19, 200, Colors.ORANGE, 100, [16, 80, 220, 600, 800, 1000]),
            LocationKeys.FREE_PARKING: Location(LocationKeys.FREE_PARKING.value, 20, nothing),
            LocationKeys.KENTUCKY: Property(LocationKeys.KENTUCKY.value, 21, 220, Colors.RED, 150, [18, 90, 250, 700, 875, 1050]),
            LocationKeys.INDIANA: Property(LocationKeys.INDIANA.value, 23, 220, Colors.RED, 150, [18, 90, 250, 700, 875, 1050]),
            LocationKeys.ILLINOIS: Property(LocationKeys.ILLINOIS.value, 24, 240, Colors.RED, 150, [20, 100, 300, 750, 925, 1100]),
            LocationKeys.BO_RR: Railroad(LocationKeys.BO_RR.value, 25),
            LocationKeys.ATLANTIC: Property(LocationKeys.ATLANTIC.value, 26, 260, Colors.YELLOW, 150, [22, 110, 330, 800, 975, 1150]),
            LocationKeys.VENTNOR: Property(LocationKeys.VENTNOR.value, 27, 260, Colors.YELLOW, 150, [22, 110, 330, 800, 975, 1150]),
            LocationKeys.WATER: Utility(LocationKeys.WATER.value, 28),
            LocationKeys.MARVIN: Property(LocationKeys.MARVIN.value, 29, 280, Colors.YELLOW, 150, [24, 120, 360, 850, 1025, 1200]),
            LocationKeys.GO_TO_JAIL: Location(LocationKeys.GO_TO_JAIL.value, 30, go_to_jail),
            LocationKeys.PACIFIC: Property(LocationKeys.PACIFIC.value, 31, 300, Colors.GREEN, 200, [26, 130, 390, 900, 1100, 1275]),
            LocationKeys.NORTH_CAROLINA: Property(LocationKeys.NORTH_CAROLINA.value, 32, 300, Colors.GREEN, 200, [26, 130, 390, 900, 1100, 1275]),
            LocationKeys.PENNSYLVANIA: Property(LocationKeys.PENNSYLVANIA.value, 34, 320, Colors.GREEN, 200, [28, 150, 450, 1000, 1200, 1400]),
            LocationKeys.SHORT_LINE: Railroad(LocationKeys.SHORT_LINE.value, 35),
            LocationKeys.PARK_PLACE: Property(LocationKeys.PARK_PLACE.value, 37, 350, Colors.DARKBLUE, 200, [35, 175, 500, 1100, 1300, 1500]),
            LocationKeys.LUXURY_TAX: Location(LocationKeys.LUXURY_TAX.value, 38, luxury_tax),
            LocationKeys.BOARDWALK: Property(LocationKeys.BOARDWALK.value, 39, 400, Colors.DARKBLUE, 200, [50, 200, 600, 1400, 1700, 2000]),
        }

    # list of each board space, in order. each value is a LocationKey enum, 
    # which can be used to access the actual location in the locations dict
    def init_spaces(self):
        return [
            LocationKeys.GO,
            LocationKeys.MEDITERRANEAN,
            LocationKeys.COMMUNITY_CHEST,
            LocationKeys.BALTIC,
            LocationKeys.INCOME_TAX,
            LocationKeys.READING_RR,
            LocationKeys.ORIENTAL,
            LocationKeys.CHANCE,
            LocationKeys.VERMONT,
            LocationKeys.CONNECTICUT,
            LocationKeys.VISITING_JAIL,
            LocationKeys.ST_CHARLES,
            LocationKeys.ELECTRIC,
            LocationKeys.STATES,
            LocationKeys.VIRGINIA,
            LocationKeys.PENNSYLVANIA_RR,
            LocationKeys.ST_JAMES,
            LocationKeys.COMMUNITY_CHEST,
            LocationKeys.TENNESSEE,
            LocationKeys.NEW_YORK,
            LocationKeys.FREE_PARKING,
            LocationKeys.KENTUCKY,
            LocationKeys.CHANCE,
            LocationKeys.INDIANA,
            LocationKeys.ILLINOIS,
            LocationKeys.BO_RR,
            LocationKeys.ATLANTIC,
            LocationKeys.VENTNOR,
            LocationKeys.WATER,
            LocationKeys.MARVIN,
            LocationKeys.GO_TO_JAIL,
            LocationKeys.PACIFIC,
            LocationKeys.NORTH_CAROLINA,
            LocationKeys.COMMUNITY_CHEST,
            LocationKeys.PENNSYLVANIA,
            LocationKeys.SHORT_LINE,
            LocationKeys.CHANCE,
            LocationKeys.PARK_PLACE,
            LocationKeys.LUXURY_TAX,
            LocationKeys.BOARDWALK
        ]

    def get_space(self, location_key):
        return self.locations[location_key].board_space

    # advance player to specified space (index). if passes go, collect 200
    def advance(self, player: Player, space, double_if_owned=False):
        if player.board_space >= space:
            print(f"Player {player.player_number} passes Go")
            if not settings.fast:
                time.sleep(0.5)
            player.add_money(200)
        self.land(player, space, double_if_owned)

    # send player directly to space index
    def land(self, player: Player, space, double_if_owned=False):
        player.board_space = space
        print(f"Player {player.player_number} lands on {self.locations[self.spaces[space]].name_colored}")
        if not settings.fast:
            time.sleep(0.5)
        auction = self.locations[self.spaces[space]].land(player, self, double_if_owned)
        if auction:
            self.perform_auction(self.locations[self.spaces[space]], player)
    
    def perform_auction(self, location, player):
        print(f"Performing auction for {location.name_colored}")
        if not settings.fast:
            time.sleep(0.5)
        # add players to bid queue
        current_player_i = player.player_number - 1
        bid_queue = []
        for _ in range(len(self.players)):
            current_player_i = (current_player_i + 1) % len(self.players)
            bid_queue.append(self.players[current_player_i])
            
        highest_bidder = None
        current_bid = 0
        while len(bid_queue) > 0:
            player = bid_queue.pop(0)
            if player == highest_bidder: # no one else made a bid; end
                break
            bid = player.decide_bid(location, current_bid)
            if bid < current_bid + 10: # must do at least $10 increments
                print(f"Player {player.player_number} drops out of the auction")
                if not settings.fast:
                    time.sleep(0.5)
                continue
            print(f"Player {player.player_number} bids ${bid}")
            if not settings.fast:
                time.sleep(0.5)
            highest_bidder = player
            current_bid = bid
            bid_queue.append(player)
        
        if current_bid == 0:
            return
        
        print(f"Player {highest_bidder.player_number} wins the auction")
        if not settings.fast:
            time.sleep(0.5)
        highest_bidder.charge(current_bid)
        highest_bidder.gain_real_estate(location)
        

    def send_to_jail(self, player: Player):
        # for the purposes of this simulation, jail is off the board
        print(f"Player {player.player_number} goes to jail")
        if not settings.fast:
            time.sleep(0.5)
        player.board_space = JAIL_BOARD_SPACE
        player.jail_counter = 3
    
    def get_out_of_jail(self, player: Player):
        print(f"Player {player.player_number} gets out of jail")
        if not settings.fast:
            time.sleep(0.5)
        player.board_space = VISITING_JAIL_BOARD_SPACE # puts them on board space 10
        player.jail_counter = 0


class Game():
    def __init__(self, players, trade_matrix):
        self.board = Board(players)
        self.trade_matrix = trade_matrix
        self.is_over = False    
        
    def play(self):
        doubles = 0
        curr_player_i = -1
        while not self.is_over:
            if doubles == 0 or current_player.jail_counter > 0:
                curr_player_i = (curr_player_i + 1) % len(self.board.players)
                current_player = self.board.players[curr_player_i]
                print(f"\nPlayer {current_player.player_number}'s turn")
                if not settings.fast:
                    time.sleep(0.5)
            
            command = input("Press enter to continue game, or type p to see the board state: ")
            if command == "p":
                self.print_game_state()
                input("Press enter to continue game:")
            
            die1, die2 = self.roll_dice()

            if current_player.jail_counter > 0:
                print(f"Player {current_player.player_number} is in jail")
                if not settings.fast:
                    time.sleep(0.5)
                if current_player.will_get_out_of_jail() or die1 == die2: # in this function player will handle themselves
                    self.board.get_out_of_jail(current_player)
                else:
                    if current_player.jail_counter == 1:
                        current_player.charge(50)
                        self.board.get_out_of_jail(current_player)
                    else:
                        print(f"\nDie roll: {die1, die2}")
                        if not settings.fast:
                            time.sleep(0.5)
                        current_player.jail_counter -= 1
                        print(f"Player {current_player.player_number} is in jail for {current_player.jail_counter} more turns\n")
                        if not settings.fast:
                            time.sleep(0.5)
                        continue
            else: # if player wasn't in jail, doubles allow player to move again
                if die1 == die2:
                    doubles += 1
                    if doubles >= 3:
                        print(f"Player {current_player.player_number} rolled doubles for the third time and got sent to jail.\n")
                        if not settings.fast:
                            time.sleep(0.5)
                        self.board.send_to_jail(current_player)
                        doubles = 0
                        continue
                else:
                    doubles = 0

            print(f"\nDie roll: {die1, die2}")
            if not settings.fast:
                time.sleep(0.5)
            next_space = (current_player.board_space + self.board.roll_total) % len(self.board.spaces)
            print(f"Next space: {self.board.locations[self.board.spaces[next_space]].name_colored}")
            if not settings.fast:
                time.sleep(0.5)
            self.board.advance(current_player, next_space)
            if current_player.money < 0:
                self.is_over = True

        print(f"Game over: Player {current_player.player_number} lost")
        if not settings.fast:
            time.sleep(0.5)
        print("Final Standings (total worth):")
        if not settings.fast:
            time.sleep(0.5)
        for player in self.board.players:
            print(f"Player {player.player_number} ({player.token}): ${player.calculate_total_worth()}")
            if not settings.fast:
                time.sleep(0.5)
        winner = self.board.players[0]
        for player in self.board.players:
            self.trade_matrix.print_player_state(player.player_number)
            if player.money > winner.money:
                winner = player
        print(f"\nPlayer {winner.player_number} wins!")
        if not settings.fast:
            time.sleep(0.5)
        

    def roll_dice(self):
        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        self.board.roll_total = die1 + die2
        return die1, die2

    def print_game_state(self):
        print("Board:")
        if not settings.fast:
            time.sleep(0.5)
        for i in range(len(self.board.spaces)):
            location = self.board.locations[self.board.spaces[i]]
            players = ""
            for player in self.board.players:
                if player.board_space == i:
                    players += f"{player.token} "
            print(f"{location.name_colored}: {players}")
        
        players_in_jail = ""
        for player in self.board.players:
            if player.jail_counter > 0:
                players_in_jail += f"{player.token} "
        print(f"Jail: {players_in_jail}")
        if not settings.fast:
            time.sleep(0.5)

        for player in self.board.players:
            self.trade_matrix.print_player_state(player.player_number)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('n', choices=[str(i) for i in range(1, 9)]) # num players
    parser.add_argument('h', choices=[str(i) for i in range(1, 9)]) # num human players
    parser.add_argument('-f', '--fast', help='Turn on fast printing', action="store_true")
    args = parser.parse_args()

    settings.init()
    settings.fast = args.fast

    print(settings.fast)

    tokens = set(["battleship", "boot", "cannon", "horse", "iron", "racecar", "dog", "thimble", "top hat", "wheelbarrow"])
    players = []
    num_players = int(args.n)
    num_humans = int(args.h)

    for i in range(num_humans):
        token = tokens.pop()
        print(f"Player {i+1}: {token} (human)")
        if not settings.fast:
            time.sleep(0.5)
        players.append(HumanPlayer(i+1, token))
    for i in range(num_humans, num_players):
        token = tokens.pop()
        print(f"Player {i+1}: {token} (ai)")
        if not settings.fast:
            time.sleep(0.5)
        players.append(AIPlayer(i+1, token))

    trade_matrix = TradeMatrix(players)
    for player in players:
        player.set_trade_matrix(trade_matrix)
    
    game = Game(players, trade_matrix)
    game.play()

    
