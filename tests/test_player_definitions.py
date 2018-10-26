import pytest
import DAG.player_definitions as pd

def test_set_player_property():
    players = pd.Players(1)
    assert len(players.get_players()) , 1

def test_payoff():
    players = pd.Players(2)
    RES = players.get_players()
    RES[0].set_const(3, 4, 5, 6)
    RES[1].set_const(30, 40, 50, 60)
    assert RES[0].beta, 4
    assert RES[1].beta, 40
    assert RES[0].abs_pay, 5
    assert RES[1].abs_pay, 50
    assert RES[0].rel_pay, 6
    assert RES[1].rel_pay, 60

def test_groups():
    players = pd.Players(2)
    RES = players.get_players()
    RES[0].set_group(1)

    assert RES[0].group == 1
    assert RES[1].group == 0
