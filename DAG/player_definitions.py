# Players.

#reminder/OT: ERC=Equity, Reciprocity, Competition
import logging as log
import numpy as np
log.basicConfig(filename = 'test.log', level = log.DEBUG)
log.Formatter('%(name)s - %(levelname)s - %(message)s')
#function code area
def u_func(y_i):
    """This must be a differentiable, strictly increasing and concave function"""
    return y_i
def r_func(sigma_i):
    """This must be a differentiable and concave function with the maximum in sigma_i=1/num_players"""
    return sigma_i
def b_func(k, num_players):
    """ Cost and payoff function"""
    pass

def c_func(k,num_players):
    """ Cost function in case of cooperation"""
    pass

#object area
# class Payoff:
#     """ Define the payoffs for"""
#     __name__ = "Payoff"
#     def __init(self):
#         self.alfa = None
#         self.beta = None
#
#     def set_glob_constants(self, alfa, beta):
#         """ If the payoff constant is common to all nodes, here it can be defined and it will be applied to everyone"""
#         self.alfa = alfa
#         self.beta = beta
#
#     def unset_constants(self):
#         alfa=None
#         beta=None
#         sigma=None


class _Player:
    __name__ = "Player"
    def __init__(self, al=None, be=None, abs_p=None, rel_p=None):
        self.alfa = al
        self.beta = be
        self.current_payoff = 0
        self.abs_pay = abs_p
        self.rel_pay = rel_p
        self.group = 0
        if al is None or be is None or abs_p is None or rel_p is None:
            log.warning("player has not been initialized with all his payoff constants")

    def set_const(self, al, be, sigma, y):
        if al is None or be is None or sigma is None or y is None:
            raise ValueError("At least one of the constants provided for payoff was none: alfa=%f, beta=%f, sigma=%f, y=%f" %(al, be, sigma, y))
        else:
            self.alfa = al
            self.beta = be
            self.rel_pay = sigma
            self.abs_pay = y
    def set_group(self, gr_num):
        """ Set the node to a group, like he belongs to a network of nodes"""
        self.group = gr_num


class Players():
    """ It contains the players and the functions to evalute their payoffs"""

    def __init__(self, players=100): #, position_type):
        #init number of players
        self.players = []
        self.num_players = players
        for p in range(self.num_players):
            self.players.append(_Player())
        #init payoff object for payoff calculations
        # if pay is None:
        #     raise ValueError("pay variable must be initialized as an object of Payoff class.")
        # elif not type(pay).__name__ == "Payoff":
        #     raise ValueError("pay variable must be initialized as an object of Payoff class. A %s object was provided" % type(pay).__name__ )
        # else:
        #     self.payoff = pay

    def calc_payoffs(self):
        """ Calculate the payoff at each iteration for each player"""
        # payoff.calc
        for play in self.players:
            play.current_payoff = play.alfa * u_func(play.abs_pay) + play.beta*r_func(play.rel_pay)

    def get_players(self):
        """ Return an array with all the players properties"""
        return self.players

    def set_player_property(self, play_n, alpha, beta, relative_payoff, absolute_payoff):
        """For the player number play_n, specifies its values (alpha, beta, relative_payoff, absolute_payoff ) in a dictionary"""
        self.players[play_n].set_const(alpha, beta, relative_payoff, absolute_payoff)
