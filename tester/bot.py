from messages import Action
from processdata import ActionInfo
class Bot(object):
    def __init__(self, id, credits, big_blind_amount, small_blind_amount, *args, **kwargs):
        self.id = id
        self.initial_credits = credits
        self.big_blind_amount = big_blind_amount
        self.small_blind_amount = small_blind_amount
        self.event_queue = []
        self.hole = None
        self.board = []
        self.active_player_count = 0
        self.bet_to_player = 0
        self.potsize = 0
        self.raisecount = 0
        self.num_to_call = self.active_player_count - 1
        self.num_called = 0
        self.info = None

        self.credits_table = {}

    def parse_events(self):
        for event in self.event_queue:
            if event.type == 'deal':
                self.num_to_call = self.active_player_count - 1
                self.num_called = 0
                self.board = [] #reset board
                self.raisecount = 0
                self.hole = event.cards
                self.info = ActionInfo.PREFLOP
            elif event.type == 'flop':
                self.board += event.cards
                self.info = ActionInfo.FLOP
            elif event.type == 'turn':
                self.board += [(event.card[0], event.card[1])] #make tuple
                self.info = ActionInfo.TURN
            elif event.type == 'river':
                self.board += [(event.card[0], event.card[1])] #make tuple
                self.info = ActionInfo.RIVER
            elif event.type == 'action':
                if event.action.type == 'raise' and event.player_id != self.id:
                    self.raisecount += 1
                    self.num_to_call = self.active_player_count - 1
                    self.num_called = 1
                    num_to_call = self.active_player_count - 1
                elif event.action.type in ['call', 'check'] and event.player_id != self.id:
                    self.num_to_call -= 1
                    self.num_called += 1


        
    def get_name(self):
        if hasattr(self, 'name'):
            return self.name
        else:
            return self.__class__.__name__

    def get_credits_count(self):
        return self.credits_table[self]
        
    def log(self, message):
        print '%s(%d): %s' % (self.get_name(), self.id, message)
        
    def action(self, type, amount=None):
        action = Action(type=type)
        if amount is not None:
            action.amount = amount
        return action
    
    def turn(self):
        raise NotImplementedError
        
    def __repr__(self):
        return "<%s player_id=%d>" % (self.get_name(), self.id)