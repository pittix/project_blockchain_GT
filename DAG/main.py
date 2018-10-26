import argparse, sys
def parser(commands):
    """Generate a parser and parse the arguments given to this script"""
    pars = argparse.ArgumentParser(description='Simulate cooperation with advantages and disadvantages')
    # pars.add_argument('num_sim', type=int, action='store')
    return pars.parse_args(commands)

def calc_payoff_NE(players):
    """Calculate the payoff of each node if they consider only the gain in the Nash Equilibrium case"""
    pass

def calc_payoff_coalition(players):
    pass

def calc_payoff_defeat(players):
    pass

def calc_payoff_TFT(players):
    pass

def calc_payoff_CORE(players):
    pass

def main_script(**args):

    pass

if __name__ == "__main__":
    RES = parser(sys.argv[0])
    main_script(**RES)
