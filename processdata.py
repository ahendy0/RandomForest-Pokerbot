from deuces import Card, Evaluator
from datastruct import *
import cPickle
import enum
import math



class GameState:
    def __init__(self,stacksize, num_called, num_to_call, bet,hand_eval, potsize, card_info, decision):
        self.stacksize = stacksize  #stacksize relative to others in the hand. on some scale 1-5? 1-10? spread of total money on table?
        self.num_called = num_called #number of players already called the bet to you
        self.num_to_call = num_to_call #number of players to call the bet after you. num_called + num_to_call + 1 should equal the amount of players in hand
        self.bet = bet #this is the bet amount to you. the bet should be relative to your stacksize on some scale
        self.hand_eval = hand_eval #the evaluation of your hand by deuces
        self.card_info = card_info #the state of the cards. prob follow same format as datastruct. Predeal should be ignored  PREDEAL = 0 PREFLOP = 1 FLOP = 2 TURN = 3 RIVER = 4 
        self.potsize = potsize  #the size of the current pot. relative to the table? relative to your stacksize?
        self.decision = decision # the y value basically, the decision they made based on all of this info
        
        self.debug = None
        
    def __str__(self):
        return "stack size: " + str(self.stacksize) + "\nnum called: " + str(self.num_called) + "\nnum to call: " + str(self.num_to_call) + "\nbet: " + str(self.bet) + "\nhand eval: " + str(self.hand_eval) + "\ncard info: " + str(self.card_info) + "\npotsize: " + str(self.potsize) + "\nDECISION: " + str(self.decision)
     
    
    
def process(handlist, top_player_names):
    gamestates = []
    evaluator = Evaluator()
    for hand in handlist:
        for player in hand.players:
            if player != None:     
                if player.name in top_player_names:
                    infostate = ActionInfo.PREDEAL
                    runningstack = player.origstack
                    num_called = 0
                    folded = 0
                    num_to_call = len(hand.players) - 1
                    bet = 0
                    potsize = 0   
                    commited = 0             
                    for action in hand.actions:
                        potsize += action.amount
                        #STATE
                        if action.info != infostate:
                            commited = 0
                            bet = 0
                            num_called = 0
                            num_to_call = len(hand.players) - 1 - folded
                            infostate = action.info 
                        name = ''
                        if action.player != None:
                            name = action.player.name
                        if player.name == name and player.hand != None:
                            if action.type in [ActionType.FOLD, ActionType.BET, ActionType.CALL, ActionType.CHECK, ActionType.ALLIN]:
                                runningstack -= action.amount
                                potsize += action.amount
                                commited += action.amount
                                # get hand eval from deuces
                                cards = parse_cards(player.hand)
                                board = hand.board
                                if board != None:
                                    board = parse_cards(str(hand.board))
                                knowncards = known_cards(board, action.info)
                                hand_eval = evaluator.evaluate(knowncards, cards)
                                #create gamestate
                                n_stacksize = normalize_stackandpot(runningstack, hand.showdown.bb * 100)
                                n_potsize = normalize_stackandpot(potsize, hand.showdown.bb * 100)
                                n_bet = normalize_bet(bet, runningstack)
                                gs = GameState(n_stacksize, num_called, num_to_call, n_bet, hand_eval, n_potsize, action.info, action.type)
                                gamestates.append(gs)
                                # we also need to consider the action taken by user, in gamestate? or different
                            elif action.type == ActionType.ANTE:
                                runningstack -= action.amount
                                potsize += action.amount
                            elif action.type == ActionType.POST:
                                runningstack -= action.amount
                                potsize += action.amount
                                commited += action.amount
                                bet = 0
                        else:
                           if action.type == ActionType.ANTE:
                               potsize += action.amount
                           if action.type == ActionType.POST:
                               potsize += action.amount
                               bet = action.amount - commited
                           if action.type in [ActionType.BET, ActionType.RAISE, ActionType.ALLIN]:
                               bet = action.amount - commited
                               num_called = 0
                               num_to_call = len(hand.players) - 1 - folded
                           if action.type in [ActionType.CALL, ActionType.CHECK]:
                               num_called += 1
                               num_to_call -= 1
                           if action.type == ActionType.FOLD:
                               folded += 1
                    
                          
        
    return gamestates
                
def known_cards( board, info):
    if info == ActionInfo.FLOP:
        return board[0:3]
    elif info == ActionInfo.TURN:
        return board [0:4]
    elif info == ActionInfo.RIVER:
        return board
    else:
        return []
                     
        
def hands_in_list(tablelist):
    numhands = 0
    for table in tablelist:
        numhands += table.numhands()
    return numhands

     
def count_known_cards(tablelist):
    i = 0
    for table in tablelist:
        for hand in table.hands:
            for winner in hand.winners:
                if winner.hand != None:
                    i+= 1
                    
    return i

def find_top_players(tablelist, netthresh, handsthresh):
    #[net, amount of hands]
    playerlist = {}
    for table in tablelist:
        for hand in table.hands:
            for player in hand.players:
                if player.name in playerlist:
                    playerlist[player.name][0] += player.net()/table.bb
                    if hand.has_known_hands():
                        playerlist[player.name][1] += 1
                else:
                    playerlist[player.name] = [player.net()/table.bb, 0]
                    
    list =  sorted(playerlist.items(), key=lambda value: value[1][0], reverse=True)
    return filter(lambda x: x[1][0] > netthresh and x[1][1] > handsthresh , list)


def find_top_players_ratio(tablelist, netthresh, handsthresh):
    #[net, amount of hands]
    playerlist = {}
    for table in tablelist:
        for hand in table.hands:
            for player in hand.players:
                if player.name in playerlist:
                    playerlist[player.name][0] += player.net()/table.bb
                    if hand.has_known_hands():
                        playerlist[player.name][1] += 1
                else:
                    playerlist[player.name] = [player.net()/table.bb, 0]
    # net/hands played
    list = sorted(playerlist.items(), key=lambda value: safe_weighted_division(value[1][0], value[1][1]), reverse=True)
    return filter(lambda x: safe_weighted_division(x[1][0], x[1][1]) > netthresh and x[1][1] > handsthresh, list)
    
   
    

def safe_weighted_division(net, hands):
    try:
        return net / hands
    except ZeroDivisionError:
        return 0

def get_good_hands(tablelist, playerlist):
    hands = []
    for table in tablelist:
        for hand in table.hands:
            added = False
            for player in hand.players:
                if player.name in playerlist:
                    if hand.has_known_hands() and not added:
                        hand.showdown = table
                        added = True
                        hands.append(hand)
    return hands            
    
def parse_cards(cardstr):
    #have to replace 10 with T for deuces
    cardstr = cardstr.replace('10', 'T')
    cardlist = cardstr.split(' ')
    hand = []
    for card in cardlist:
        dcard = Card.new(card)
        hand.append(dcard)
    return hand
    
def normalize_stackandpot(stack, buyin):
    ratio = stack/float(buyin)
    if ratio < 1/5.0:
        return normalize.SMALL
    if ratio < 1/2.0:
        return normalize.SMALLMID
    if ratio < 1:
        return normalize.MID
    if ratio < 3:
        return normalize.MIDLARGE
    if ratio < 5:
        return normalize.LARGE
        
class normalize(Enum):
    SMALL = 1
    SMALLMID = 2
    MID = 3
    MIDLARGE = 4
    LARGE = 5
    
    
# returns percentage of bet to stack size, rounded up to nearest 10
# ex: bet = 20, stack = 500, bet is 4% of stack, return 10
def normalize_bet(bet, stack):
    if stack == 0:
        return 100
    return roundup((bet/float(stack))*100)
    
def roundup(x):
    return int(math.ceil(x / 10.0)) * 10

if __name__ == "__main__":
    filename = './ABSdata/ABSdata_1.pkl'
    print "Opening", filename, "this may take a minute"
    pfile = open(filename, 'rb')
    tablelist = cPickle.load(pfile)
    
    """find the number of hands in tablelist"""
    # print "There is", hands_in_list(tablelist), "hands in this file."
    
    
    print count_known_cards(tablelist)
    top_players = find_top_players(tablelist, 200, 100) # first is profit threshold , number of cards threshold
    # table, minhands to be considered, number of players to return
    top_ratio_players = find_top_players_ratio(tablelist, 0.75,  100) # first is ratio threshold, number of cards threshold
    
    top_names = [i[0] for i in top_players]
    
    # change player list to top_player_names, if we use output from top_players instead
    good_hands = get_good_hands(tablelist, top_names)
    print "number of hands we will use:", len(good_hands)
    
 
    
    gamestates = process(good_hands, top_names)
    for x in xrange(0, 20):
        print gamestates[x]
        print "------", x
    print len(gamestates)
    
    
    
    
    
    