from otree.api import *
import time
import random
import numpy as np
import time

doc = """
Timing Games"""


class C(BaseConstants):
    NAME_IN_URL = 'timing_game'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    XMAX = 15
    XMIN = 5
    YMAX = 120
    YMIN = 0
    LAMBDA = 10
    RHO = 5
    GAMMA = 2
    DECIMALS = 2
    SUBPERIOD = 6


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    start_timestamp = models.IntegerField()
    num_messages = models.IntegerField()
    messages_roundzero = models.IntegerField()
    num_players = models.IntegerField(initial=0)


class Player(BasePlayer):
    player_strategy = models.FloatField(initial=0.0)


class Adjustment(ExtraModel):
    group = models.Link(Group)
    player = models.Link(Player)
    strategy = models.FloatField()
    strategy_payoff = models.FloatField()
    seconds = models.IntegerField(doc="Timestamp (seconds since beginning of trading)")
    # move = models.BooleanField()



#Definition
def generate_bubble_coordinate(current_strategies):
    current_positions = []
    current_ties = []
    for strat in current_strategies:
        below_strat = [i for i in current_strategies if i < strat]
        pos = len(below_strat) + 0.5
        current_positions.append(pos)

        equal_strat = [i for i in current_strategies if i == strat]
        tie = len(equal_strat)
        current_ties.append(tie)
    current_positions = np.array(current_positions)
    current_ties = np.array(current_ties)
    current_strategies = np.array(current_strategies)
    vy = []
    ux = 1 + (2 * C.LAMBDA * current_strategies) - (current_strategies ** 2)
    for i in range(len(current_strategies)):
        if current_ties[i] == 0:
            vy.append((1 - (current_positions[i]/len(current_strategies))/C.GAMMA) * (1 + (current_positions[i]/len(current_strategies))/C.RHO))
        else:
            total = 0
            for j in range(current_ties[i]):
                total += (1 - ((current_positions[i]+j)/len(current_strategies))/C.GAMMA) * (1 + ((current_positions[i]+j)/len(current_strategies))/C.RHO)
            total = total/current_ties[i]
            vy.append(total)
    vy = np.array(vy)
    current_bubble_payoff = ux * vy
    
    bubble_coordinate = np.vstack((current_strategies, current_bubble_payoff)).T

    return bubble_coordinate


def generate_landscape_coordinate(current_strategies):
    #calculate landscape: landscape_x, landscape_y, landscape_coordinate
    landscape_x =  np.arange(C.XMIN, C.XMAX, 1/(10**C.DECIMALS))
    landscape_x = np.round(landscape_x, C.DECIMALS)
    landscape_positions = []
    landscape_ties = []
    for strat in landscape_x:
        below_strat = [i for i in current_strategies if i < strat]
        pos = len(below_strat) + 0.5
        landscape_positions.append(pos)

        equal_strat = [i for i in current_strategies if i == strat]
        tie = len(equal_strat)
        landscape_ties.append(tie)
    landscape_positions = np.array(landscape_positions)
    landscape_ties = np.array(landscape_ties)

    vy = []
    ux = 1 + (2 * C.LAMBDA * landscape_x) - (landscape_x ** 2)
    for i in range(len(landscape_x)):
        if landscape_ties[i] < 2:
            vy.append((1 - (landscape_positions[i]/len(current_strategies))/C.GAMMA) * (1 + (landscape_positions[i]/len(current_strategies))/C.RHO))
        else:
            total = 0
            for j in range(landscape_ties[i]):
                total += (1 - ((landscape_positions[i]+j)/len(current_strategies))/C.GAMMA) * (1 + ((landscape_positions[i]+j)/len(current_strategies))/C.RHO)
            total = total/landscape_ties[i]
            vy.append(total)
    vy = np.array(vy)
    landscape_y = ux * vy
    landscape_coordinate = np.vstack((landscape_x, landscape_y)).T
    
    return landscape_coordinate
    



class WaitToStart(WaitPage):
    @staticmethod
    def after_all_players_arrive(group: Group):
        group.start_timestamp = int(time.time())
        group.num_messages = 0
        group.messages_roundzero = 0

        # current_id_strategies = []             
        for p in group.get_players():
            p.player_strategy = round(random.random() * (C.XMAX - C.XMIN) + C.XMIN, C.DECIMALS)
            group.num_players += 1
        #     current_id_strategies.append([p.id_in_group, p.player_strategy])
        # current_id_strategies.sort(key=lambda x: x[0])
            # Adjustment.create(
            #     player=p,
            #     group=group,
            #     strategy=p.player_strategy,
            #     seconds=0,
            # )
        # current_id_strategies = [[adj.player.id_in_group, adj.strategy] for adj in Adjustment.filter(group=group,seconds=0)]
        #generate initial current strategies and bubble coordinate
        # current_strategies =  [round(adj.strategy,2) for adj in Adjustment.filter(group=group,seconds=0)] #make players' strategies as an array
        # current_strategies = [i[1] for i in current_id_strategies]
        # bubble_coordinate = generate_bubble_coordinate(current_strategies).tolist()
        # strategies_payoffs = [i[1] for i in bubble_coordinate]
        # for p in group.get_players():
        #     Adjustment.create(
        #         player=p,
        #         group=group,
        #         strategy=current_strategies[p.id_in_group-1],
        #         strategy_payoff=strategies_payoffs[p.id_in_group-1],
        #         seconds=0,
        #     )
        # print(Adjustment.filter(group=group))
        # print(bubble_coordinate)
        # landscape_coordinate = generate_landscape_coordinate(current_strategies).tolist()
        # print(landscape_coordinate)

        

# PAGES
class MyPage(Page):
    timeout_seconds = 1 * 60 #suggest to add two or three more seconds if you have many subjects

    @staticmethod
    def js_vars(player: Player): #Passing data from Python to JavaScript
        return dict(my_id=player.id_in_group, xmax=C.XMAX, xmin=C.XMIN, ymax=C.YMAX, ymin=C.YMIN, subperiod=C.SUBPERIOD)

    @staticmethod
    def vars_for_template(player: Player):

        return dict(
            xmax=C.XMAX, 
            xmin=C.XMIN,
            subperiod=C.SUBPERIOD,


            )

    @staticmethod
    def live_method(player: Player, data):
        group = player.group
        # group.num_messages += 1
        num_players = group.num_players
        print(group.get_players)

        print('data {}'.format(data)) #format is {'strategy': '13.1'}
        # print(group.num_messages) 
        if data == {}: #at beginning, when receive none msg, reset the timestamp
            # print('yes')
            group.messages_roundzero += 1
            group.start_timestamp =int(time.time())    
        now_seconds = int(time.time() - group.start_timestamp)
        #record the player who made the change
        # print(now_seconds)
    
        if 'strategy' in data:
            player.player_strategy = float(data['strategy'])
            group.num_messages += 1
            print(group.num_messages)
        # if 'strategy' in data:
        #     strategy = data['strategy']
        #     Adjustment.create(
        #         player=player,
        #         group=group,
        #         strategy=strategy,
        #         seconds=now_seconds,
        #     )
            
            # # record the other players' strategies at the same time
            # for other_player in player.get_others_in_group():
            #     current_strategy = [adj.strategy for adj in Adjustment.filter(player=other_player, group=other_player.group)][-1]
            #     Adjustment.create(
            #         player=other_player,
            #         group=group,
            #         strategy=current_strategy,
            #         seconds=now_seconds,
            #     )
        if (('strategy' in data) and (group.num_messages % num_players == 0)) or ((data == {}) and (group.messages_roundzero == num_players)):    
            print(group.num_messages)
            print('second {}'.format(now_seconds))
        # if now_seconds % C.SUBPERIOD == 0:    
            global landscape_coordinate
            global highcharts_landscape_series
            # print('yes')
            current_id_strategies = []
            for p in group.get_players():
                current_id_strategies.append([p.id_in_group, p.player_strategy])
            # current_id_strategies = [[adj.player.id_in_group, adj.strategy] for adj in Adjustment.filter(group=group, seconds=now_seconds)] 
            current_id_strategies.sort(key=lambda x: x[0]) #ensure start with player 1
            current_strategies = [i[1] for i in current_id_strategies]
            # print(current_id_strategies)

            #generate series for bubble and landscape
            bubble_coordinate = generate_bubble_coordinate(current_strategies).tolist()
            landscape_coordinate = generate_landscape_coordinate(current_strategies).tolist()
            strategies_payoffs = [i[1] for i in bubble_coordinate]
            for p in group.get_players():
                Adjustment.create(
                    player=p,
                    group=group,
                    # strategy=[adj.strategy for adj in Adjustment.filter(player=p, group=group, seconds=now_seconds)][-1],
                    strategy=current_strategies[p.id_in_group-1],
                    strategy_payoff=strategies_payoffs[p.id_in_group-1],
                    seconds=now_seconds,
                )
        
            highcharts_landscape_series = []
            # bubble_coordinate_series = dict(data=bubble_coordinate, type='scatter', name='Player {}'.format(p.id_in_group))
            highcharts_landscape_series.append(bubble_coordinate)
            # landscape_coordinate_series = dict(data=landscape_coordinate, type='line', name='Landscape')
            highcharts_landscape_series.append(landscape_coordinate)
            
            
            highcharts_series = []
            for p in group.get_players():
                history = [[adj.seconds, adj.strategy] for adj in Adjustment.filter(player=p) if adj.strategy_payoff is not None]

                # this is optional. it allows the line
                # to go all the way to the right of the graph
                # last_strategy = history[-1][1]
                # history.append([now_seconds, last_strategy])

                series = dict(data=history, type='line', name='Player {}'.format(p.id_in_group))
                highcharts_series.append(series)
                # highcharts_series.append(history)

            #calculate payoff over time
            highcharts_payoff_series = []
            for p in group.get_players():
                payoff_history = [[adj.seconds, adj.strategy_payoff] for adj in Adjustment.filter(player=p) if adj.strategy_payoff is not None]
                payoff_series = dict(data=payoff_history, type='area', name='Player {}'.format(p.id_in_group))
                highcharts_payoff_series.append(payoff_series)

        # print(dict(highcharts_series=highcharts_series, highcharts_payoff_series=highcharts_payoff_series))
        
            return {0: dict(highcharts_series=highcharts_series, highcharts_landscape_series=highcharts_landscape_series, highcharts_payoff_series=highcharts_payoff_series)}

        if 'slider' in data:
            single_coordinate = [x for x in landscape_coordinate if x[0] == float(data['slider'])]
            return{player.id_in_group: dict(single_coordinate=single_coordinate, highcharts_landscape_series=highcharts_landscape_series)}




class ResultsWaitPage(WaitPage):
    @staticmethod
    def after_all_players_arrive(group: Group):
        # to be filled in.
        # you should calculate some results here. maybe aggregate all the Adjustments,
        # take their weighted average, etc.
        adjustments = Adjustment.filter(group=group)
        print(adjustments)
        for p in group.get_players():
            adjustments_individual = Adjustment.filter(player=p)
            print(adjustments_individual)
        pass


class Results(Page):
    pass


page_sequence = [WaitToStart, MyPage, ResultsWaitPage, Results]


def custom_export(players):
    # Export an ExtraModel called "Trial"

    yield ['session', 'participant', 'round_number', 'id_in_group', 'seconds', 'strategy', 'payoff', ]

    # 'filter' without any args returns everything
    adjustments = Adjustment.filter()
    for adj in adjustments:
        player = adj.player
        participant = player.participant
        session = player.session
        yield [session.code, participant.code, player.round_number, player.id_in_group, adj.seconds, adj.strategy, adj.strategy_payoff, ]