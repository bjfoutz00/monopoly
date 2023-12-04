import random
import time
from enums import LocationKeys, DeckType


def chance0(player, board):
    board.advance(player, board.get_space(LocationKeys.BOARDWALK))
    return True

def chance1(player, board):
    board.advance(player, board.get_space(LocationKeys.GO))
    return True

def chance2(player, board):
    board.advance(player, board.get_space(LocationKeys.ILLINOIS))
    return True
    
def chance3(player, board):
    board.advance(player, board.get_space(LocationKeys.ST_CHARLES))
    return True

def chance4(player, board): # quantity: 2
    if player.board_space < board.get_space(LocationKeys.READING_RR) \
            or player.board_space >= board.get_space(LocationKeys.SHORT_LINE):
        board.advance(player, board.get_space(LocationKeys.READING_RR), double_if_owned=True)
    
    elif player.board_space < board.get_space(LocationKeys.PENNSYLVANIA_RR):
        board.advance(player, board.get_space(LocationKeys.PENNSYLVANIA_RR), double_if_owned=True)
    
    elif player.board_space < board.get_space(LocationKeys.BO_RR):
        board.advance(player, board.get_space(LocationKeys.BO_RR), double_if_owned=True)
    
    elif player.board_space < board.get_space(LocationKeys.SHORT_LINE):
        board.advance(player, board.get_space(LocationKeys.SHORT_LINE), double_if_owned=True)
    return True
    
def chance5(player, board):
    if player.board_space < board.get_space(LocationKeys.ELECTRIC) \
            or player.board_space >= board.get_space(LocationKeys.WATER):
        board.advance(player, board.get_space(LocationKeys.ELECTRIC), double_if_owned=True)
    else:
        board.advance(player, board.get_space(LocationKeys.WATER), double_if_owned=True)
    return True

def chance6(player, board):
    player.add_money(50)
    return True
    
def chance7(player, board):
    print(f"player {player.player_number} draws a Get Out Of Jail Free Card")
    time.sleep(0.5)
    player.goojf_cards += 1
    return False
    
def chance8(player, board):
    print(f"player {player.player_number} moves back 3 spaces")
    time.sleep(0.5)
    board.land(player, player.board_space - 3)
    return True
    
def chance9(player, board):
    board.send_to_jail(player)
    return True
    
def chance10(player, board):
    house_cost = 25
    hotel_cost = 100
    print(f"player {player.player_number} must pay ${house_cost} for each house and ${hotel_cost} for each hotel")
    time.sleep(0.5)
    total = 0

    for property in player.properties.values():
        if property.can_develop:
            if property.num_houses == 5:
                total += hotel_cost
            else:
                total += property.num_houses * house_cost
    
    player.charge(total)
    return True
    
def chance11(player, board):
    player.charge(15)
    return True


def chance12(player, board):
    board.advance(player, board.get_space(LocationKeys.READING_RR))
    return True
    
def chance13(current_player, board):
    print(f"player {current_player.player_number} must give each player $50")
    time.sleep(0.5)
    amount = 50
    total = amount * (len(board.players) - 1)
    current_player.charge(total)
    for player in board.players:
        if current_player.player_number == player.player_number:
            continue
        player.add_money(amount)
    return True

def chance14(player, board):
    player.add_money(150)
    return True


def comm_chest0(player, board):
    board.advance(player, board.get_space(LocationKeys.GO))
    return True

def comm_chest1(player, board):
    player.add_money(200)
    return True
    
def comm_chest2(player, board): # quantity: 2
    player.charge(50)
    return True
    
def comm_chest6(player, board): # quantity: 3
    player.add_money(100)
    return True
    
def comm_chest7(player, board):
    player.add_money(20)
    return True
    
def comm_chest8(current_player, board):
    print(f"player {current_player.player_number} gains $10 from each player")
    time.sleep(0.5)
    amount = 10
    for player in board.players:
        if player.player_number == current_player.player_number:
            continue
        player.charge(amount)
    
    current_player.add_money(amount * (len(board.players) - 1))
    return True

def comm_chest10(player, board):
    player.charge(100)
    return True

def comm_chest11(player, board):
    player.add_money(25)
    return True

def comm_chest12(player, board):
    house_cost = 40
    hotel_cost = 115
    total = 0
    print(f"player {player.player_number} must pay ${house_cost} for each house and ${hotel_cost} for each hotel")
    time.sleep(0.5)

    for property in player.properties.values():
        if property.can_develop:
            if property.num_houses == 5:
                total += hotel_cost
            else:
                total += property.num_houses * house_cost
    player.charge(total)
    return True

def comm_chest13(player, board):
    player.add_money(10)
    return True


class Card():
    def __init__(self, effect):
        self.do_effect = effect
        

class Deck():
    def __init__(self, type: DeckType):
        self.cards = self.init_cards(type)

    def init_cards(self, type):
        cards = []
        if type == DeckType.CHANCE:
            cards = [
                Card(chance0),
                Card(chance1),
                Card(chance2),
                Card(chance3),
                Card(chance4),
                Card(chance4),
                Card(chance5),
                Card(chance6),
                Card(chance7),
                Card(chance8),
                Card(chance9),
                Card(chance10),
                Card(chance11),
                Card(chance12),
                Card(chance13),
                Card(chance14)
            ]
        elif type == DeckType.COMMUNITY_CHEST:
            cards = [
                Card(chance1),
                Card(comm_chest1),
                Card(comm_chest2),
                Card(comm_chest2),
                Card(chance6),
                Card(chance7),
                Card(chance9),
                Card(comm_chest6),
                Card(comm_chest6),
                Card(comm_chest6),
                Card(comm_chest7),
                Card(comm_chest8),
                Card(comm_chest10),
                Card(comm_chest11),
                Card(comm_chest12),
                Card(comm_chest13),
            ]

        random.shuffle(cards)
        return cards

    def draw(self, player, board):
        card = self.cards.pop(0)
        return_to_bottom = card.do_effect(player, board)
        if return_to_bottom:
            self.cards.append(card)