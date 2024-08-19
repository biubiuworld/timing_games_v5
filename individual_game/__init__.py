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
    input_file = csv.DictReader(open("individual_game/configs/demo.csv"))
    parameter_list = []
    for row in input_file:
        parameter_list.append(row[str(parameter)])
    return parameter_list

class C(BaseConstants):
    NAME_IN_URL = 'individual_game'
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
    PRACTICE_ROUND_NUM = 0
    SELECT_LOW_BOUND = 12
    SELECT_HIGH_BOUND = 28
    NUM_OF_BOTS = read_csv('NUM_OF_BOTS')
    MOVE_PERCENT = read_csv('MOVE_PERCENT')
    TREMBLING = read_csv('TREMBLING')


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
    start_timestamp = models.LongStringField()
    str_strategies = models.LongStringField()
    peak_payoff_location = models.FloatField()


class Player(BasePlayer):
    player_id_index = models.IntegerField()
    player_strategy = models.FloatField(initial=0.0)
    str_strategies = models.LongStringField()
    peak_payoff_location = models.FloatField()
    start_timestamp = models.LongStringField()
    # player_average_strategy = models.FloatField()
    player_average_payoff = models.FloatField()
    player_cum_average_payoff = models.FloatField()
    group_average_payoffs = models.FloatField()
    group_cum_average_payoffs = models.FloatField()
    # payment_selected_round = models.IntegerField()
    payment_payoff = models.FloatField()
    payment_in_dollar = models.FloatField()
    total_payment = models.FloatField()
    # bug = models.IntegerField()
    move = models.BooleanField()
    remaining_freeze_period = models.IntegerField()
    if_freeze_next = models.IntegerField()
    if_freeze_now = models.IntegerField()
    player_previous_strategy = models.FloatField(initial=0.0)

class Adjustment(ExtraModel):
    group = models.Link(Group)
    player = models.Link(Player)
    player_id_index = models.IntegerField()
    strategy = models.FloatField()
    strategy_payoff = models.FloatField()
    multiplier_strategy_payoff = models.FloatField()
    seconds = models.FloatField(doc="Timestamp (seconds since beginning of trading)")
    move = models.BooleanField()
    remaining_freeze = models.IntegerField()
    if_freeze_next = models.BooleanField()
    if_freeze_now = models.BooleanField()


#Functions
def generate_initial_strategies(player, num_of_players):
    lam = float(C.LAMBDA[player.round_number-1])
    gam = float(C.GAMMA[player.round_number-1])
    rho = float(C.RHO[player.round_number-1])
    xmin = float(C.XMIN[player.round_number-1])
    xmax = float(C.XMAX[player.round_number-1])
    initialization = float(C.INITIALIZATION[player.round_number-1])
    game_type = str(C.GAME_TYPE[player.round_number-1])
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
    strategies = np.round(strategies,2)

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

     # find the best y and peak_payoff_location
    best_y_index = landscape_y.argmax()
    peak_payoff_location = landscape_x[best_y_index]

    return landscape_coordinate, multiplier_landscape_coordinate, peak_payoff_location


def transfer_array_to_str(array):
    arr = array
    str_array = ','.join(str(x) for x in arr)  
    return str_array


# def creating_session(subsession: Subsession):
#     print(subsession.round_number)
#     for player in subsession.get_players():
#         num_players = C.NUM_OF_BOTS + 1
#         strategies = generate_initial_strategies(player, num_players) # generate initial strategies
#         player.player_id_index = random.sample(list(range(num_players)),1)[0]
#         player.player_strategy = strategies[player.player_id_index]
#         player.str_strategies = transfer_array_to_str(strategies) # store strategies in string format 

#         bubble_coordinate_array, multiplier_bubble_coordinate_array = generate_bubble_coordinate(player, strategies)
#         landscape_coordinate_array, multiplier_landscape_coordinate_array, player.peak_payoff_location = generate_landscape_coordinate(player, strategies)
        
#         bubble_coordinate = bubble_coordinate_array.tolist() 
#         multiplier_bubble_coordinate = multiplier_bubble_coordinate_array.tolist()
#         landscape_coordinate = landscape_coordinate_array.tolist()
#         multiplier_landscape_coordinate = multiplier_landscape_coordinate_array.tolist()

#         strategies_payoffs = [i[1] for i in bubble_coordinate] #a list of payoff for each player
#         multiplier_strategies_payoffs = [i[1] for i in multiplier_bubble_coordinate] #a list of multiplied payoff for each player       

#         multiplier_array_strategies_payoffs = np.array(multiplier_strategies_payoffs) 
#         multiplier_avg_strategies_payoffs = multiplier_array_strategies_payoffs.mean() #multiplied group avg payoff in current round

#         avg_group_payoff_history = []
#         avg_group_payoff_history.append([0,multiplier_avg_strategies_payoffs]) #global store avg group payoff(multiplied)

#         #lanscape plot
#         highcharts_landscape_series = []
#         highcharts_landscape_series.append(multiplier_bubble_coordinate)
#         highcharts_landscape_series.append(multiplier_landscape_coordinate)


#         highcharts_series = []
#         highcharts_payoff_series = []
#         for player_index in range(num_players):
#             history = [[0,strategies[player_index]]] 
#             highcharts_series.append(history) #strategy over time plot
#             payoff_history = [[0, multiplier_strategies_payoffs[player_index]]]
#             highcharts_payoff_series.append(payoff_history) #multiplied payoff over time plot

#         player.participant.avg_group_payoff_history = avg_group_payoff_history
#         player.participant.highcharts_landscape_series = highcharts_landscape_series
#         player.participant.highcharts_series = highcharts_series
#         player.participant.highcharts_payoff_series = highcharts_payoff_series
#         player.remaining_freeze_period = 0
#         player.if_freeze_next = 0
#         player.if_freeze_now = 0
#         player.move=0
#         player.participant.if_freeze_next_all = [0]*(num_players)
#         player.player_previous_strategy = player.player_strategy

#         Adjustment.create(
#                 player=player,
#                 group=player.group,
#                 player_id_index=player.player_id_index, # add dat to export table
#                 strategy=player.player_strategy,
#                 strategy_payoff=strategies_payoffs[player.player_id_index],
#                 multiplier_strategy_payoff=multiplier_strategies_payoffs[player.player_id_index],
#                 seconds=0,
#                 move=0,
#                 remaining_freeze=0,
#                 if_freeze_next=0,
#                 if_freeze_now=0,
#             )


class Introduction(Page):
    @staticmethod
    def is_displayed(player):
        return (player.round_number == 1) or (player.round_number == C.PRACTICE_ROUND_NUM+1)

class WaitToStart(WaitPage):
    @staticmethod
    def after_all_players_arrive(group: Group):
        for player in group.get_players():
            #prepare for next round
            player.participant.avg_group_payoff_history = []
            player.participant.highcharts_landscape_series = []
            player.participant.highcharts_series = []
            player.participant.highcharts_payoff_series = []
            player.participant.remaining_freeze_period_for_all = []
            # player.participant.if_freeze_next = []
            # player.participant.if_freeze_now = []
            player.participant.if_freeze_next_all = []
            NUM_OF_BOTS = int(C.NUM_OF_BOTS[group.round_number-1])
            num_players = NUM_OF_BOTS + 1
            strategies = generate_initial_strategies(player, num_players) # generate initial strategies
            player.player_id_index = random.sample(list(range(num_players)),1)[0]
            player.player_strategy = strategies[player.player_id_index]
            player.str_strategies = transfer_array_to_str(strategies) # store strategies in string format 

            bubble_coordinate_array, multiplier_bubble_coordinate_array = generate_bubble_coordinate(player, strategies)
            landscape_coordinate_array, multiplier_landscape_coordinate_array, player.peak_payoff_location = generate_landscape_coordinate(player, strategies)
            
            bubble_coordinate = bubble_coordinate_array.tolist() 
            multiplier_bubble_coordinate = multiplier_bubble_coordinate_array.tolist()
            landscape_coordinate = landscape_coordinate_array.tolist()
            multiplier_landscape_coordinate = multiplier_landscape_coordinate_array.tolist()

            strategies_payoffs = [i[1] for i in bubble_coordinate] #a list of payoff for each player
            multiplier_strategies_payoffs = [i[1] for i in multiplier_bubble_coordinate] #a list of multiplied payoff for each player       

            multiplier_array_strategies_payoffs = np.array(multiplier_strategies_payoffs) 
            multiplier_avg_strategies_payoffs = multiplier_array_strategies_payoffs.mean() #multiplied group avg payoff in current round

            avg_group_payoff_history = []
            avg_group_payoff_history.append([0,multiplier_avg_strategies_payoffs]) #global store avg group payoff(multiplied)

            #lanscape plot
            highcharts_landscape_series = []
            highcharts_landscape_series.append(multiplier_bubble_coordinate)
            highcharts_landscape_series.append(multiplier_landscape_coordinate)


            highcharts_series = []
            highcharts_payoff_series = []
            for player_index in range(num_players):
                history = [[0,strategies[player_index]]] 
                highcharts_series.append(history) #strategy over time plot
                payoff_history = [[0, multiplier_strategies_payoffs[player_index]]]
                highcharts_payoff_series.append(payoff_history) #multiplied payoff over time plot

            player.participant.avg_group_payoff_history = avg_group_payoff_history
            player.participant.highcharts_landscape_series = highcharts_landscape_series
            player.participant.highcharts_series = highcharts_series
            player.participant.highcharts_payoff_series = highcharts_payoff_series
            player.remaining_freeze_period = 0
            player.if_freeze_next = 0
            player.if_freeze_now = 0
            player.move=0
            player.participant.if_freeze_next_all = [0]*(num_players)
            player.player_previous_strategy = player.player_strategy

            Adjustment.create(
                    player=player,
                    group=player.group,
                    player_id_index=player.player_id_index, # add dat to export table
                    strategy=player.player_strategy,
                    strategy_payoff=strategies_payoffs[player.player_id_index],
                    multiplier_strategy_payoff=multiplier_strategies_payoffs[player.player_id_index],
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
        NUM_OF_BOTS = int(C.NUM_OF_BOTS[player.round_number-1])
        num_players = NUM_OF_BOTS + 1
        participant = player.participant
        return dict(
            my_id=player.player_id_index + 1, 
            xmax=float(C.XMAX[player.round_number-1]), 
            xmin=float(C.XMIN[player.round_number-1]), 
            ymax=float(C.YMAX[player.round_number-1]), 
            ymin=float(C.YMIN[player.round_number-1]), 
            subperiod=float(C.SUBPERIOD[player.round_number-1]),
            highcharts_series=participant.highcharts_series, #strategy over time
            highcharts_landscape_series=participant.highcharts_landscape_series, #multiplied bubble and landscape
            highcharts_payoff_series=participant.highcharts_payoff_series, #multiplied payoff over time plot
            avg_payoff_history=participant.avg_group_payoff_history, #group avg payoff(multiplied)
            # if_freeze_for_all=[0]*num_players,
            )

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            xmax=float(C.XMAX[player.round_number-1]), 
            xmin=float(C.XMIN[player.round_number-1]),
            subperiod=float(C.SUBPERIOD[player.round_number-1]),
            freeze_period=int(C.FREEZE_PERIOD[player.round_number-1]), 
            num_of_bots=int(C.NUM_OF_BOTS[player.round_number-1]),
            move_percent=float(C.MOVE_PERCENT[player.round_number-1]), 
            trembling=round(float(C.TREMBLING[player.round_number-1])/2,2),
            round_number=player.round_number if player.round_number<C.PRACTICE_ROUND_NUM+1 else player.round_number-C.PRACTICE_ROUND_NUM,
            practice_round_num = C.PRACTICE_ROUND_NUM,
            )
    
    @staticmethod
    def get_timeout_seconds(player: Player):
        # return (group.start_timestamp + int(C.PERIOD_LENGTH[group.round_number-1])) - time.time()
        return int(C.PERIOD_LENGTH[player.round_number-1])

    @staticmethod
    def live_method(player: Player, data):
        NUM_OF_BOTS = int(C.NUM_OF_BOTS[player.round_number-1])
        MOVE_PERCENT = float(C.MOVE_PERCENT[player.round_number-1])
        TREMBLING = float(C.TREMBLING[player.round_number-1])
        num_players = NUM_OF_BOTS + 1
        # huamn player ids
        human_id_index = []
        human_id_index.append(player.player_id_index)
        # bots id index
        bots_id_index = list(set(range(num_players)) - set(human_id_index))
        # num of bots move
        num_move = round(NUM_OF_BOTS * MOVE_PERCENT)

        #case 1: initialize the page
        if data == {}: #at beginning, when receive none msg, reset the timestamp
            player.start_timestamp =str(round(time.time(), 1)) 


        elif 'strategy' in data:
            player.player_previous_strategy = player.player_strategy
            if (float(data['strategy']) <= float(C.XMAX[player.round_number-1])) & (float(data['strategy']) >= float(C.XMIN[player.round_number-1]))&(player.remaining_freeze_period == 0):
                player.player_strategy = float(data['strategy'])
            
            # convert str strategies to array
            previous_strategies = [round(float(x),2) for x in player.str_strategies.split(',')]
            previous_strategies = np.array(previous_strategies).copy()
            current_strategies = previous_strategies
            current_strategies[player.player_id_index] = player.player_strategy # update real human strategy
            
            selected_bots = random.sample(bots_id_index, num_move)
            for bot_idx in  selected_bots:
                current_strategies[bot_idx] = player.peak_payoff_location + random.random() * TREMBLING - TREMBLING/2
            if player.player_previous_strategy != player.player_strategy:
                player.move = 1
                player.remaining_freeze_period = int(C.FREEZE_PERIOD[player.round_number-1]) 
            elif player.player_previous_strategy == player.player_strategy:
                if player.remaining_freeze_period > 0:
                    player.remaining_freeze_period -= 1

            if player.remaining_freeze_period != 0:
                player.if_freeze_next = 1
            else:
                player.if_freeze_next = 0
            player.str_strategies = transfer_array_to_str(current_strategies)
            # session.current_strategies_copy = current_strategies #replace global strategies by current strategies

            bubble_coordinate_array, multiplier_bubble_coordinate_array = generate_bubble_coordinate(player, current_strategies)
            landscape_coordinate_array, multiplier_landscape_coordinate_array, player.peak_payoff_location = generate_landscape_coordinate(player, current_strategies)
            
            bubble_coordinate = bubble_coordinate_array.tolist() 
            multiplier_bubble_coordinate = multiplier_bubble_coordinate_array.tolist()
            landscape_coordinate = landscape_coordinate_array.tolist()
            multiplier_landscape_coordinate = multiplier_landscape_coordinate_array.tolist()

            strategies_payoffs = [i[1] for i in bubble_coordinate] #a list of payoff for each player
            multiplier_strategies_payoffs = [i[1] for i in multiplier_bubble_coordinate] #a list of multiplied payoff for each player

            now_seconds = round(time.time()- float(player.start_timestamp), 1)
            # print(now_seconds)

            multiplier_array_strategies_payoffs = np.array(multiplier_strategies_payoffs) 
            multiplier_avg_strategies_payoffs = round(multiplier_array_strategies_payoffs.mean(),3) #group avg payoff in current subperiod(multiplied)

            player.participant.avg_group_payoff_history.append([now_seconds,multiplier_avg_strategies_payoffs])#group avg over time (multiplied)

            Adjustment.create(
                player=player,
                group=player.group,
                player_id_index=player.player_id_index, # add dat to export table
                strategy=player.player_strategy,
                strategy_payoff=strategies_payoffs[player.player_id_index],
                multiplier_strategy_payoff=multiplier_strategies_payoffs[player.player_id_index],
                seconds=now_seconds,
                move=player.move,
                remaining_freeze=player.remaining_freeze_period,
                if_freeze_next=player.if_freeze_next,
                if_freeze_now=player.if_freeze_now,
            )
            player.if_freeze_now = player.if_freeze_next
            
            if_freeze_next_all = [0]*num_players
            if_freeze_next_all[player.player_id_index] = player.if_freeze_next
            player.participant.if_freeze_next_all = if_freeze_next_all
        
            highcharts_landscape_series = []
            highcharts_landscape_series.append(multiplier_bubble_coordinate)
            highcharts_landscape_series.append(multiplier_landscape_coordinate)
            
            
            # session.highcharts_series = [] #strategy over time
            player.participant.highcharts_landscape_series = highcharts_landscape_series
            for player_index in range(num_players):
                history = [now_seconds,current_strategies[player_index]]
                player.participant.highcharts_series[player_index].append(history)
                payoff_history = [now_seconds, multiplier_strategies_payoffs[player_index]]
                player.participant.highcharts_payoff_series[player_index].append(payoff_history)

                

        # print(dict(highcharts_series=highcharts_series, highcharts_payoff_series=highcharts_payoff_series))
        
            return {player.id_in_group: dict(highcharts_series=player.participant.highcharts_series, highcharts_landscape_series=player.participant.highcharts_landscape_series, highcharts_payoff_series=player.participant.highcharts_payoff_series, avg_payoff_history=player.participant.avg_group_payoff_history, if_freeze_for_all=player.participant.if_freeze_next_all )}

        elif 'slider' in data:
            single_coordinate = [x for x in player.participant.highcharts_landscape_series[1] if x[0] == float(data['slider'])]
            return{player.id_in_group: dict(single_coordinate=single_coordinate, highcharts_landscape_series=player.participant.highcharts_landscape_series, if_freeze_for_all=player.participant.if_freeze_next_all )}




# class ResultsWaitPage(WaitPage):

#     @staticmethod
#     def after_all_players_arrive(group: Group):
#         # group_strategies = []
#         group_payoffs = []
#         group_cum_payoff = []
#         period_length = int(C.PERIOD_LENGTH[group.round_number-1])
#         for p in group.get_players():
#             # player_strategy_history = np.array([adj.strategy for adj in Adjustment.filter(player=p) if adj.strategy_payoff is not None])
#             # p.player_average_strategy =player_strategy_history.mean()
#             player_payoff_history = np.array([adj.multiplier_strategy_payoff for adj in Adjustment.filter(player=p) if adj.strategy_payoff is not None])
#             p.player_average_payoff = round(player_payoff_history.mean(),3) #payoff in current round
#             player_cum_payoff = []
#             if group.round_number < C.PRACTICE_ROUND_NUM+1:
#                 for rd in p.in_all_rounds():
#                     player_cum_payoff.append(rd.player_average_payoff) #collect a list of avg payoff over rounds
#                 array_player_cum_payoff = np.array(player_cum_payoff)
#                 p.player_cum_average_payoff = round(array_player_cum_payoff.mean(),3)
#             elif group.round_number > C.PRACTICE_ROUND_NUM:
#                 for rd in p.in_all_rounds():
#                     player_cum_payoff.append(rd.player_average_payoff) #collect a list of avg payoff over rounds
#                 player_cum_payoff = player_cum_payoff[C.PRACTICE_ROUND_NUM:] #exclude practice round payoff
#                 array_player_cum_payoff = np.array(player_cum_payoff)
#                 p.player_cum_average_payoff = round(array_player_cum_payoff.mean(),3)               

#             #select payoff round in the final round
#             if p.round_number == C.NUM_ROUNDS:
#                 # print(player_cum_payoff)
#                 # p.payment_selected_round = random.randint(3, 6) #the selected payment round
#                 select_payoff = [val for val in player_cum_payoff if (val<C.SELECT_HIGH_BOUND)&(val>C.SELECT_LOW_BOUND)]
#                 if select_payoff == []:
#                     select_payoff = player_cum_payoff
#                 p.payment_payoff = random.choice(select_payoff)
#                 p.payment_in_dollar = round((p.payment_payoff*period_length-C.THRESHOLD)/C.EXCHANGE_RATE,2)
#                 p.total_payment = round(p.payment_in_dollar + C.SHOWUP, 2)

#             # group_strategies.append(p.player_average_strategy)
#             group_payoffs.append(p.player_average_payoff)
#             group_cum_payoff.append(p.player_cum_average_payoff)
#         # array_group_strategies = np.array(group_strategies)
#         array_group_payoffs = np.array(group_payoffs)
#         array_group_cum_payoff = np.array(group_cum_payoff)
#         # group.group_average_strategies = array_group_strategies.mean()
#         group.group_average_payoffs = round(array_group_payoffs.mean(),3)
#         group.group_cum_average_payoffs = round(array_group_cum_payoff.mean(),3)

       
  

class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        group_payoffs = []
        group_cum_payoff = []
        period_length = int(C.PERIOD_LENGTH[player.round_number-1])

        player_payoff_history = np.array([adj.multiplier_strategy_payoff for adj in Adjustment.filter(player=player) if adj.strategy_payoff is not None])
        player.player_average_payoff = round(player_payoff_history.mean(),3) #payoff in current round
        player_cum_payoff = []
        if player.round_number < C.PRACTICE_ROUND_NUM+1:
            for rd in player.in_all_rounds():
                player_cum_payoff.append(rd.player_average_payoff) #collect a list of avg payoff over rounds
            array_player_cum_payoff = np.array(player_cum_payoff)
            player.player_cum_average_payoff = round(array_player_cum_payoff.mean(),3)
        elif player.round_number > C.PRACTICE_ROUND_NUM:
            for rd in player.in_all_rounds():
                player_cum_payoff.append(rd.player_average_payoff) #collect a list of avg payoff over rounds
            player_cum_payoff = player_cum_payoff[C.PRACTICE_ROUND_NUM:] #exclude practice round payoff
            array_player_cum_payoff = np.array(player_cum_payoff)
            player.player_cum_average_payoff = round(array_player_cum_payoff.mean(),3)               

        #select payoff round in the final round
        if player.round_number == C.NUM_ROUNDS:
            # print(player_cum_payoff)
            # p.payment_selected_round = random.randint(3, 6) #the selected payment round
            select_payoff = [val for val in player_cum_payoff if (val<C.SELECT_HIGH_BOUND)&(val>C.SELECT_LOW_BOUND)]
            if select_payoff == []:
                select_payoff = player_cum_payoff
            player.payment_payoff = random.choice(select_payoff)
            player.payment_in_dollar = round((player.payment_payoff*period_length-C.THRESHOLD)/C.EXCHANGE_RATE,2)
            player.total_payment = round(player.payment_in_dollar + C.SHOWUP, 2)

        # group_strategies.append(p.player_average_strategy)
        group_cum_payoff = [x[1] for x in player.participant.avg_group_payoff_history]

        array_group_cum_payoff = np.array(group_cum_payoff)
        # group.group_average_strategies = array_group_strategies.mean()
        player.group_average_payoffs = round(array_group_cum_payoff.mean(),3)
        player.group_cum_average_payoffs = round(array_group_cum_payoff.mean(),3)

        # #prepare for next round
        # player.participant.avg_group_payoff_history = []
        # player.participant.highcharts_landscape_series = []
        # player.participant.highcharts_series = []
        # player.participant.highcharts_payoff_series = []
        # player.participant.remaining_freeze_period_for_all = []
        # # player.participant.if_freeze_next = []
        # # player.participant.if_freeze_now = []
        # player.participant.if_freeze_next_all = []
        return dict(
            in_all_rounds=player.in_all_rounds(),
            player_average_payoff=round(player.player_average_payoff, 2),
            player_cum_average_payoff=round(player.player_cum_average_payoff, 2),
            group_average_payoffs=round(player.group_average_payoffs, 2),
            group_cum_average_payoffs=round(player.group_cum_average_payoffs, 2),
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


page_sequence = [Introduction, WaitToStart, MyPage, Results, Payment]


def custom_export(players):
    # Export an ExtraModel called "Trial"

    yield ['session','subperiod', 'period_length', 'xmax','xmin','ymax','ymin','lambda','gamma','rho','freeze_period','num_of_bots', 'move_percent', 'trembling', 'multiplier','initialization_code','game_type', 'participant','participant_label', 'round_number', 'id_in_group', 'player_id_index','seconds', 'strategy', 'payoff','multiplied_payoff', 'move', 'remaining_freeze_period', 'if_freeze_next', 'if_freeze_now']

    # 'filter' without any args returns everything
    adjustments = Adjustment.filter()
    for adj in adjustments:
        player = adj.player
        participant = player.participant
        session = player.session
        yield [session.code, float(C.SUBPERIOD[player.round_number-1]), int(C.PERIOD_LENGTH[player.round_number-1]), 
               float(C.XMAX[player.round_number-1]), float(C.XMIN[player.round_number-1]), float(C.YMAX[player.round_number-1]), float(C.YMIN[player.round_number-1]), 
               float(C.LAMBDA[player.round_number-1]), float(C.GAMMA[player.round_number-1]), float(C.RHO[player.round_number-1]),int(C.FREEZE_PERIOD[player.round_number-1]), 
               int(C.NUM_OF_BOTS[player.round_number-1]),float(C.MOVE_PERCENT[player.round_number-1]), float(C.TREMBLING[player.round_number-1]),
               float(C.MULTIPLIER[player.round_number-1]), int(C.INITIALIZATION[player.round_number-1]), str(C.GAME_TYPE[player.round_number-1]),
               participant.code, participant.label, player.round_number, player.id_in_group,player.player_id_index, adj.seconds, adj.strategy, adj.strategy_payoff, adj.multiplier_strategy_payoff, adj.move, adj.remaining_freeze, adj.if_freeze_next, adj.if_freeze_now]
  
