from otree.api import *
import time
import random
import numpy as np
import time
import math

doc = """
Timing Games
move: move if strategy changes since last time
remaining_freeze: freeze in the following n subperiods
if_freeze_now: whether is freezed in current subperiod



"""

import csv
def read_csv(parameter):
    input_file = csv.DictReader(open("timing_game/configs/demo.csv"))
    parameter_list = []
    for row in input_file:
        parameter_list.append(row[str(parameter)])
    return parameter_list

class C(BaseConstants):
    NAME_IN_URL = 'timing_game'
    PLAYERS_PER_GROUP = None
    XMAX = read_csv('XMAX')
    XMIN = read_csv('XMIN')
    YMAX = read_csv('YMAX')
    YMIN = read_csv('YMIN')
    LAMBDA = read_csv('LAMBDA')
    RHO = read_csv('RHO')
    GAMMA = read_csv('GAMMA')
    DECIMALS = 2
    SUBPERIOD = read_csv('SUBPERIOD')
    PERIOD_LENGTH = read_csv('PERIOD_LENGTH')
    NUM_ROUNDS = len(SUBPERIOD)
    FREEZE_PERIOD = read_csv('FREEZE_PERIOD')
    MULTIPLIER = read_csv('MULTIPLIER')
    INITIALIZATION = read_csv('INITIALIZATION')
    GAME_TYPE = read_csv('GAME_TYPE')
    LOWER_BOUND = read_csv('LOWER_BOUND')
    EXCHANGE_RATE = 180
    SHOWUP = 7
    THRESHOLD =500
    PRACTICE_ROUND_NUM = 2
    SELECT_LOW_BOUND = 12
    SELECT_HIGH_BOUND = 28

class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    # start_timestamp = models.FloatField()
    num_messages = models.IntegerField()
    messages_roundzero = models.IntegerField()
    num_players = models.IntegerField(initial=0)
    # group_average_strategies = models.FloatField()
    group_average_payoffs = models.FloatField()
    group_cum_average_payoffs = models.FloatField()
    


class Player(BasePlayer):
    player_strategy = models.FloatField(initial=0.0)
    # player_average_strategy = models.FloatField()
    player_average_payoff = models.FloatField()
    player_cum_average_payoff = models.FloatField()
    # payment_selected_round = models.IntegerField()
    payment_payoff = models.FloatField()
    payment_in_dollar = models.FloatField()
    total_payment = models.FloatField()
    # bug = models.IntegerField()


class Adjustment(ExtraModel):
    group = models.Link(Group)
    player = models.Link(Player)
    strategy = models.FloatField()
    strategy_payoff = models.FloatField()
    multiplier_strategy_payoff = models.FloatField()
    seconds = models.FloatField(doc="Timestamp (seconds since beginning of trading)")
    move = models.BooleanField()
    remaining_freeze = models.IntegerField()
    if_freeze_next = models.BooleanField()
    if_freeze_now = models.BooleanField()


#Functions
def generate_initial_strategies(group, num_of_players):
    lam = float(C.LAMBDA[group.round_number-1])
    gam = float(C.GAMMA[group.round_number-1])
    rho = float(C.RHO[group.round_number-1])
    xmin = float(C.XMIN[group.round_number-1])
    xmax = float(C.XMAX[group.round_number-1])
    initialization = float(C.INITIALIZATION[group.round_number-1])
    game_type = str(C.GAME_TYPE[group.round_number-1])
    strategies = []

    if initialization == 0:
        for i in range(num_of_players):
            strategies.append(round(random.random() * (xmax - xmin) + xmin, 2))

    elif initialization == 1: #NE initialization
        if game_type == 'fear':
            cdfmin = max(0, round((lam - math.sqrt(1+lam**2) * math.sqrt(1-(16*(1+rho)*(gam-1))/((gam +3*rho)*(3*gam +rho)))),2))
            cdfmax = lam
            cdfx = np.round(np.arange(cdfmin, cdfmax, 0.01), 2)
            cdfy = gam - rho + np.sqrt((gam + rho) ** 2 - 4 * ((1 + rho) * (gam - 1) * (1 + lam ** 2))/(1 + 2 * lam * cdfx - cdfx ** 2))
            y_ind = 0
            cdfy = cdfy/2
            for i in range(num_of_players):
            # y_ind is the index in the cdf to compare to
            # we increment it until it is greater than or equal to the percentage of players set so far
                if (i+1)/num_of_players <= cdfy[y_ind]:
                    strategies.append(cdfx[y_ind])
                else:
                    while (y_ind < len(cdfy) - 1) and ((i+1)/num_of_players > cdfy[y_ind]):
                        y_ind = y_ind + 1
                # there are some rounding issues when we reach the end of the cdf
                # if we reach the end (for the last few players), just use the last value
                    if y_ind >= len(cdfy):
                        strategies.append(cdfx[len(cdfy)])
                    else:
                        strategies.append(cdfx[y_ind])


        elif game_type == 'greed':
            cdfmin = lam
            cdfmax = lam + math.sqrt(1+lam**2)/(math.sqrt(1+16*rho*gam/((3*gam-3*rho-2)*(gam-rho+2))))
            cdfx = np.round(np.arange(cdfmin, cdfmax, 0.01), 2)
            cdfy = gam - rho - np.sqrt((gam + rho) ** 2 - 4 * gam * rho * (1 + lam ** 2) / (1 + 2 * lam * cdfx - cdfx ** 2))
            y_ind = len(cdfy) - 1
            cdfy = cdfy / 2            

            i = num_of_players
            while i > 0:
                # y_ind is the index in the cdf to compare to
                # we decrement it until it is less than or equal to the percentage of players set so far
                if (i-1)/num_of_players >= cdfy[y_ind]:
                    strategies.append(cdfx[y_ind])
                else:
                    while y_ind > 0 and (i-1)/num_of_players < cdfy[y_ind]:
                        y_ind = y_ind - 1
                    # there are some rounding issues when we reach the end of the cdf
                    # if we reach the end (for the last few players), just use the last value
                    if y_ind == 0:
                        strategies.append(cdfx[0])
                    else:
                        strategies.append(cdfx[y_ind])
                i = i - 1

    elif initialization > 1:
        for i in range(num_of_players):
                strategies.append(round(lam+(random.random() * 0.2 - 0.2/2), 2))
                
    #randomize the order of strategies
    random.shuffle(strategies)

    return strategies    


def generate_bubble_coordinate(player, current_strategies):
    current_positions = []
    current_ties = []
    lam = float(C.LAMBDA[player.round_number-1])
    gam = float(C.GAMMA[player.round_number-1])
    rho = float(C.RHO[player.round_number-1])
    multiplier = float(C.MULTIPLIER[player.round_number-1])
    game_type = str(C.GAME_TYPE[player.round_number-1])
    lower_bound = float(C.LOWER_BOUND[player.round_number-1])

    for strat in current_strategies:
        below_strat = [i for i in current_strategies if i < strat]
        if game_type == 'fear':
            pos = len(below_strat) + 1
        elif game_type == 'greed':
            pos = len(below_strat) 
        else:
            pos = len(below_strat) + 0.5
        current_positions.append(pos)

        equal_strat = [i for i in current_strategies if i == strat]
        tie = len(equal_strat)
        current_ties.append(tie)
    current_positions = np.array(current_positions)
    current_ties = np.array(current_ties)
    current_strategies = np.array(current_strategies)
    vy = []
    ux = 1 + (2 * lam * current_strategies) - (current_strategies ** 2)
    for i in range(len(current_strategies)):
        if current_ties[i] == 0:
            vy.append((1 - (current_positions[i]/len(current_strategies))/gam) * (1 + (current_positions[i]/len(current_strategies))/rho))
        else:
            total = 0
            for j in range(current_ties[i]):
                total += (1 - ((current_positions[i]+j)/len(current_strategies))/gam) * (1 + ((current_positions[i]+j)/len(current_strategies))/rho)
            total = total/current_ties[i]
            vy.append(total)
    vy = np.array(vy)
    current_bubble_payoff = np.round(ux * vy, decimals=3)
    multiplier_bubble_payoff = np.round(multiplier*ux * vy - lower_bound, decimals=3)
    
    bubble_coordinate = np.vstack((current_strategies, current_bubble_payoff)).T
    multiplier_bubble_coordinate = np.vstack((current_strategies, multiplier_bubble_payoff)).T

    return bubble_coordinate, multiplier_bubble_coordinate


def generate_landscape_coordinate(player, current_strategies):
    #calculate landscape: landscape_x, landscape_y, landscape_coordinate
    lam = float(C.LAMBDA[player.round_number-1])
    gam = float(C.GAMMA[player.round_number-1])
    rho = float(C.RHO[player.round_number-1])
    xmin = float(C.XMIN[player.round_number-1])
    xmax = float(C.XMAX[player.round_number-1])
    multiplier = float(C.MULTIPLIER[player.round_number-1])
    lower_bound = float(C.LOWER_BOUND[player.round_number-1])
    landscape_x =  np.arange(xmin, xmax, 1/(10**C.DECIMALS))
    landscape_x = np.round(landscape_x, C.DECIMALS)
    landscape_positions = []
    landscape_ties = []
    game_type = str(C.GAME_TYPE[player.round_number-1])
    for strat in landscape_x:
        below_strat = [i for i in current_strategies if i < strat]
        if game_type == 'fear':
            pos = len(below_strat) + 1
        elif game_type == 'greed':
            pos = len(below_strat) 
        else:
            pos = len(below_strat) + 0.5
        landscape_positions.append(pos)

        equal_strat = [i for i in current_strategies if i == strat]
        tie = len(equal_strat)
        landscape_ties.append(tie)
    landscape_positions = np.array(landscape_positions)
    landscape_ties = np.array(landscape_ties)

    vy = []
    ux = 1 + (2 * lam * landscape_x) - (landscape_x ** 2)
    for i in range(len(landscape_x)):
        if landscape_ties[i] < 2:
            vy.append((1 - (landscape_positions[i]/len(current_strategies))/gam) * (1 + (landscape_positions[i]/len(current_strategies))/rho))
        else:
            total = 0
            for j in range(landscape_ties[i]):
                total += (1 - ((landscape_positions[i]+j)/len(current_strategies))/gam) * (1 + ((landscape_positions[i]+j)/len(current_strategies))/rho)
            total = total/landscape_ties[i]
            vy.append(total)
    vy = np.array(vy)
    landscape_y = np.round(ux * vy,3)
    multiplier_landscape_y = np.round(multiplier*ux*vy - lower_bound, 3)
    landscape_coordinate = np.vstack((landscape_x, landscape_y)).T
    multiplier_landscape_coordinate = np.vstack((landscape_x, multiplier_landscape_y)).T
    return landscape_coordinate, multiplier_landscape_coordinate
    
class Introduction(Page):
    @staticmethod
    def is_displayed(player):
        return (player.round_number == 1) or (player.round_number == C.PRACTICE_ROUND_NUM+1)


class WaitToStart(WaitPage):
    @staticmethod
    def after_all_players_arrive(group: Group):
        # group.start_timestamp = int(time.time())
        session = group.session #use session to store global group data
        # print(group.id_in_subsession)

        session.avg_payoff_history = []
        session.start_timestamp = str(round(time.time(), 1)) 
        # group.start_timestamp = round(int(time.time()*2)/2, 1)
        # group.start_timestamp = round(time.time()- 1705600000, 1) 
        group.num_messages = 0
        group.messages_roundzero = 0
        xmax = float(C.XMAX[group.round_number-1])
        xmin = float(C.XMIN[group.round_number-1])
        
        initial_id_strategies = [] #collect initial id and strategies
        # assign initial strategies
        for p in group.get_players():
            # p.player_strategy = round(random.random() * (xmax - xmin) + xmin, C.DECIMALS)
            group.num_players += 1
            # initial_id_strategies.append([p.id_in_group, p.player_strategy])
        strategies = generate_initial_strategies(group, group.num_players)
        for p in group.get_players():
            p.player_strategy = strategies[p.id_in_group-1]
            initial_id_strategies.append([p.id_in_group, p.player_strategy])
        initial_id_strategies.sort(key=lambda x: x[0]) #make sure the the order starts from player 1
        initial_strategies = [i[1] for i in initial_id_strategies] #a list of strategies

        session.current_strategies_copy = initial_strategies #store initial strategies to use in the live page
        generate_bubble_coordinate_result = generate_bubble_coordinate(group, initial_strategies)
        generate_landscape_coordinate_result = generate_landscape_coordinate(group, initial_strategies)
        bubble_coordinate = generate_bubble_coordinate_result[0].tolist() 
        # print(bubble_coordinate)
        landscape_coordinate = generate_landscape_coordinate_result[0].tolist()
        strategies_payoffs = [i[1] for i in bubble_coordinate] #a list of payoff for each player

        multiplier_bubble_coordinate = generate_bubble_coordinate_result[1].tolist() 
        # print(multiplier_bubble_coordinate)
        multiplier_landscape_coordinate = generate_landscape_coordinate_result[1].tolist()
        multiplier_strategies_payoffs = [i[1] for i in multiplier_bubble_coordinate] #a list of multiplied payoff for each player

        multiplier_array_strategies_payoffs = np.array(multiplier_strategies_payoffs) 
        multiplier_avg_strategies_payoffs = multiplier_array_strategies_payoffs.mean() #multiplied group avg payoff in current round
        session.avg_payoff_history.append([0,multiplier_avg_strategies_payoffs]) #global store avg group payoff(multiplied)

        #lanscape plot
        session.highcharts_landscape_series = []
        session.highcharts_landscape_series.append(multiplier_bubble_coordinate)
        session.highcharts_landscape_series.append(multiplier_landscape_coordinate)

        session.highcharts_series = []
        session.highcharts_payoff_series = []
        session.remaining_freeze_period_for_all = [0] * group.num_players
        session.if_freeze_next = [0]* group.num_players
        session.if_freeze_now = [0] * group.num_players
        for p in group.get_players():
            history = [[0,p.player_strategy]] 
            session.highcharts_series.append(history) #strategy over time plot
            payoff_history = [[0, multiplier_strategies_payoffs[p.id_in_group-1]]]
            session.highcharts_payoff_series.append(payoff_history) #multiplied payoff over time plot
            Adjustment.create(
                    player=p,
                    group=group,
                    strategy=p.player_strategy,
                    strategy_payoff=strategies_payoffs[p.id_in_group-1],
                    multiplier_strategy_payoff=multiplier_strategies_payoffs[p.id_in_group-1],
                    seconds=0,
                    move=0,
                    remaining_freeze=0,
                    if_freeze_next=0,
                    if_freeze_now=0,
                )


# PAGES
class MyPage(Page):
    # timeout_seconds = C.PERIOD_LENGTH #suggest to add two or three more seconds if you have many subjects
    
    @staticmethod
    def js_vars(player: Player): #Passing data from Python to JavaScript
        session = player.group.session
        num_players = player.group.num_players
        return dict(
            my_id=player.id_in_group, 
            xmax=float(C.XMAX[player.round_number-1]), 
            xmin=float(C.XMIN[player.round_number-1]), 
            ymax=float(C.YMAX[player.round_number-1]), 
            ymin=float(C.YMIN[player.round_number-1]), 
            subperiod=float(C.SUBPERIOD[player.round_number-1]),
            highcharts_series=session.highcharts_series, #strategy over time
            highcharts_landscape_series=session.highcharts_landscape_series, #multiplied bubble and landscape
            highcharts_payoff_series=session.highcharts_payoff_series, #multiplied payoff over time plot
            avg_payoff_history=session.avg_payoff_history, #group avg payoff(multiplied)
            # if_freeze_for_all=[0]*num_players,
            )

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            xmax=float(C.XMAX[player.round_number-1]), 
            xmin=float(C.XMIN[player.round_number-1]),
            subperiod=float(C.SUBPERIOD[player.round_number-1]),
            round_number=player.round_number if player.round_number<C.PRACTICE_ROUND_NUM+1 else player.round_number-C.PRACTICE_ROUND_NUM,
            practice_round_num = C.PRACTICE_ROUND_NUM,
            )
    
    @staticmethod
    def get_timeout_seconds(player: Player):
        group = player.group
        # return (group.start_timestamp + int(C.PERIOD_LENGTH[group.round_number-1])) - time.time()
        return int(C.PERIOD_LENGTH[group.round_number-1])

    @staticmethod
    def live_method(player: Player, data):

        group = player.group
        session = player.group.session

        num_players = group.num_players
        
        
        #case 1: initialize the page
        # if data == {}: #at beginning, when receive none msg, reset the timestamp
            
        #     group.messages_roundzero += 1
        #     if group.messages_roundzero ==1:
        #         session.start_timestamp =str(round(time.time(), 1)) 



        
        if 'strategy' in data:
            if (float(data['strategy']) <= float(C.XMAX[player.round_number-1])) & (float(data['strategy']) >= float(C.XMIN[player.round_number-1]))&(session.remaining_freeze_period_for_all[player.id_in_group-1] == 0):
                player.player_strategy = float(data['strategy'])
            
            group.num_messages += 1
            if group.num_messages % num_players == 0:   
                group.num_messages = 0
                current_id_strategies = []
                for p in group.get_players():
                    current_id_strategies.append([p.id_in_group, p.player_strategy])
                current_id_strategies.sort(key=lambda x: x[0]) #ensure start with player 1
                current_strategies = [i[1] for i in current_id_strategies]
                move_for_all = [0]*num_players
                
                for m in range(num_players):
                    if session.current_strategies_copy[m] != current_strategies[m]:
                        move_for_all[m] = 1 #if strategy changes, move should be 1
                        session.remaining_freeze_period_for_all[m] = int(C.FREEZE_PERIOD[player.round_number-1]) #Once move this time, remaining freeze for n subperiod
                    elif session.current_strategies_copy[m] == current_strategies[m]: #however, if no change in strategy, evaluate whether due to freeze or self-freeze
                        if session.remaining_freeze_period_for_all[m] > 0:
                            session.remaining_freeze_period_for_all[m] -= 1   
                     
                    if session.remaining_freeze_period_for_all[m] != 0:
                        session.if_freeze_next[m] = 1
                    else:
                        session.if_freeze_next[m] = 0
                if_freeze_next_copy = session.if_freeze_next.copy()
                
                # print('move_for_all', move_for_all)
                # print('if_freeze_Next', session.if_freeze_next)
                session.current_strategies_copy = current_strategies #replace global strategies by current strategies
              

                #generate series for bubble and landscape
                generate_bubble_coordinate_result = generate_bubble_coordinate(player, current_strategies)
                generate_landscape_coordinate_result = generate_landscape_coordinate(player, current_strategies)
                bubble_coordinate = generate_bubble_coordinate_result[0].tolist()
                landscape_coordinate = generate_landscape_coordinate_result[0].tolist()
                strategies_payoffs = [i[1] for i in bubble_coordinate]

                multiplier_bubble_coordinate = generate_bubble_coordinate_result[1].tolist()
                multiplier_landscape_coordinate = generate_landscape_coordinate_result[1].tolist()
                multiplier_strategies_payoffs = [i[1] for i in multiplier_bubble_coordinate]

                now_seconds = round(time.time()- float(session.start_timestamp), 1)
                # print(now_seconds)

                multiplier_array_strategies_payoffs = np.array(multiplier_strategies_payoffs) 
                multiplier_avg_strategies_payoffs = round(multiplier_array_strategies_payoffs.mean(),3) #group avg payoff in current subperiod(multiplied)
                session.avg_payoff_history.append([now_seconds,multiplier_avg_strategies_payoffs])#group avg over time (multiplied)
                # print(avg_payoff_history)
                # print('strategy', current_strategies)
                # print('move', move_for_all)
                # print('remaining_freeze', session.remaining_freeze_period_for_all)
                # print('if_freeze_Next', session.if_freeze_next)
                # print('if_freeze_now', session.if_freeze_now)
                for p in group.get_players():
                    Adjustment.create(
                        player=p,
                        group=group,
                        # strategy=[adj.strategy for adj in Adjustment.filter(player=p, group=group, seconds=now_seconds)][-1],
                        strategy=current_strategies[p.id_in_group-1],
                        strategy_payoff=strategies_payoffs[p.id_in_group-1],
                        multiplier_strategy_payoff=multiplier_strategies_payoffs[p.id_in_group-1],
                        seconds=now_seconds,
                        move=move_for_all[p.id_in_group-1],
                        remaining_freeze=session.remaining_freeze_period_for_all[p.id_in_group-1],
                        if_freeze_next=session.if_freeze_next[p.id_in_group-1],
                        if_freeze_now=session.if_freeze_now[p.id_in_group-1],
                    )
            
                session.highcharts_landscape_series = []
                # bubble_coordinate_series = dict(data=bubble_coordinate, type='scatter', name='Player {}'.format(p.id_in_group))
                session.highcharts_landscape_series.append(multiplier_bubble_coordinate)
                # landscape_coordinate_series = dict(data=landscape_coordinate, type='line', name='Landscape')
                session.highcharts_landscape_series.append(multiplier_landscape_coordinate)
                session.if_freeze_now = if_freeze_next_copy
                
                # session.highcharts_series = [] #strategy over time
                for p in group.get_players():
                    # history = [[adj.seconds, adj.strategy] for adj in Adjustment.filter(player=p) if adj.strategy_payoff is not None]
                    history = [now_seconds,p.player_strategy]
                    session.highcharts_series[p.id_in_group-1].append(history)

                #calculate payoff over time
                # session.highcharts_payoff_series = []
                for p in group.get_players():
                    # payoff_history = [[adj.seconds, adj.strategy_payoff] for adj in Adjustment.filter(player=p) if adj.strategy_payoff is not None]
                    payoff_history = [now_seconds, multiplier_strategies_payoffs[p.id_in_group-1]]
                    session.highcharts_payoff_series[p.id_in_group-1].append(payoff_history)

                    

            # print(dict(highcharts_series=highcharts_series, highcharts_payoff_series=highcharts_payoff_series))
            
                return {0: dict(highcharts_series=session.highcharts_series, highcharts_landscape_series=session.highcharts_landscape_series, highcharts_payoff_series=session.highcharts_payoff_series, avg_payoff_history=session.avg_payoff_history, if_freeze_for_all=session.if_freeze_next)}

        elif 'slider' in data:
            single_coordinate = [x for x in session.highcharts_landscape_series[1] if x[0] == float(data['slider'])]
            return{player.id_in_group: dict(single_coordinate=single_coordinate, highcharts_landscape_series=session.highcharts_landscape_series, if_freeze_for_all=session.if_freeze_next)}




class ResultsWaitPage(WaitPage):

    @staticmethod
    def after_all_players_arrive(group: Group):
        # group_strategies = []
        group_payoffs = []
        group_cum_payoff = []
        period_length = int(C.PERIOD_LENGTH[group.round_number-1])
        for p in group.get_players():
            # player_strategy_history = np.array([adj.strategy for adj in Adjustment.filter(player=p) if adj.strategy_payoff is not None])
            # p.player_average_strategy =player_strategy_history.mean()
            player_payoff_history = np.array([adj.multiplier_strategy_payoff for adj in Adjustment.filter(player=p) if adj.strategy_payoff is not None])
            p.player_average_payoff = round(player_payoff_history.mean(),3) #payoff in current round
            player_cum_payoff = []
            if group.round_number < C.PRACTICE_ROUND_NUM+1:
                for rd in p.in_all_rounds():
                    player_cum_payoff.append(rd.player_average_payoff) #collect a list of avg payoff over rounds
                array_player_cum_payoff = np.array(player_cum_payoff)
                p.player_cum_average_payoff = round(array_player_cum_payoff.mean(),3)
            elif group.round_number > C.PRACTICE_ROUND_NUM:
                for rd in p.in_all_rounds():
                    player_cum_payoff.append(rd.player_average_payoff) #collect a list of avg payoff over rounds
                player_cum_payoff = player_cum_payoff[C.PRACTICE_ROUND_NUM:] #exclude practice round payoff
                array_player_cum_payoff = np.array(player_cum_payoff)
                p.player_cum_average_payoff = round(array_player_cum_payoff.mean(),3)               

#select payoff round in the final round
            if p.round_number == C.NUM_ROUNDS:
                # print(player_cum_payoff)
                # p.payment_selected_round = random.randint(3, 6) #the selected payment round
                select_payoff = [val for val in player_cum_payoff if (val<C.SELECT_HIGH_BOUND)&(val>C.SELECT_LOW_BOUND)]
                if select_payoff == []:
                    select_payoff = player_cum_payoff
                p.payment_payoff = random.choice(select_payoff)
                p.payment_in_dollar = round((p.payment_payoff*period_length-C.THRESHOLD)/C.EXCHANGE_RATE,2)
                p.total_payment = round(p.payment_in_dollar + C.SHOWUP, 2)

            # group_strategies.append(p.player_average_strategy)
            group_payoffs.append(p.player_average_payoff)
            group_cum_payoff.append(p.player_cum_average_payoff)
        # array_group_strategies = np.array(group_strategies)
        array_group_payoffs = np.array(group_payoffs)
        array_group_cum_payoff = np.array(group_cum_payoff)
        # group.group_average_strategies = array_group_strategies.mean()
        group.group_average_payoffs = round(array_group_payoffs.mean(),3)
        group.group_cum_average_payoffs = round(array_group_cum_payoff.mean(),3)

       
  

class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        group = player.group
        return dict(
            in_all_rounds=player.in_all_rounds(),
            player_average_payoff=round(player.player_average_payoff, 2),
            player_cum_average_payoff=round(player.player_cum_average_payoff, 2),
            group_average_payoffs=round(group.group_average_payoffs, 2),
            group_cum_average_payoffs=round(group.group_cum_average_payoffs, 2),
            )
    

    
class Payment(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS
    
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            # payment_selected_round=player.in_round(C.NUM_ROUNDS).payment_selected_round,
            period_length = int(C.PERIOD_LENGTH[player.round_number-1]),
            payment_payoff=round(player.in_round(C.NUM_ROUNDS).payment_payoff, 2),
            payment_in_dollar=round(player.in_round(C.NUM_ROUNDS).payment_in_dollar, 2),
            threshold=C.THRESHOLD,
            show_up = C.SHOWUP,
            exchange_rate = C.EXCHANGE_RATE,
            total_payment = round(player.in_round(C.NUM_ROUNDS).total_payment,2),
            )


page_sequence = [Introduction, WaitToStart, MyPage, ResultsWaitPage, Results, Payment]


def custom_export(players):
    # Export an ExtraModel called "Trial"

    yield ['session','subperiod', 'period_length', 'xmax','xmin','ymax','ymin','lambda','gamma','rho','freeze_period', 'multiplier','initialization_code','game_type', 'participant','participant_label', 'round_number', 'id_in_group', 'seconds', 'strategy', 'payoff','multiplied_payoff', 'move', 'remaining_freeze_period', 'if_freeze_next', 'if_freeze_now']

    # 'filter' without any args returns everything
    adjustments = Adjustment.filter()
    for adj in adjustments:
        player = adj.player
        participant = player.participant
        session = player.session
        yield [session.code, float(C.SUBPERIOD[player.round_number-1]), int(C.PERIOD_LENGTH[player.round_number-1]), 
               float(C.XMAX[player.round_number-1]), float(C.XMIN[player.round_number-1]), float(C.YMAX[player.round_number-1]), float(C.YMIN[player.round_number-1]), 
               float(C.LAMBDA[player.round_number-1]), float(C.GAMMA[player.round_number-1]), float(C.RHO[player.round_number-1]),int(C.FREEZE_PERIOD[player.round_number-1]), float(C.MULTIPLIER[player.round_number-1]), int(C.INITIALIZATION[player.round_number-1]), str(C.GAME_TYPE[player.round_number-1]),
               participant.code, participant.label, player.round_number, player.id_in_group, adj.seconds, adj.strategy, adj.strategy_payoff, adj.multiplier_strategy_payoff, adj.move, adj.remaining_freeze, adj.if_freeze_next, adj.if_freeze_now]
  
