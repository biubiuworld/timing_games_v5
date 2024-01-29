from os import environ

SESSION_CONFIGS = [
    dict(
        name='timing_game',
        display_name="Timing Games",
        app_sequence=['timing_game'],
        num_demo_participants=3,
    ),
    # dict(
    #     name='pilot_part1',
    #     display_name="Timing Games p1",
    #     app_sequence=['pilot_part1'],
    #     num_demo_participants=3,
    # ),    
    # dict(
    #     name='pilot_part2',
    #     display_name="Timing Games p2",
    #     app_sequence=['pilot_part2'],
    #     num_demo_participants=3,
    # ), 
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=0.00, doc=""
)

ROOMS = [
    dict(
        name='TimingGames',
        display_name="TimingGames",
        participant_label_file='timing_game/_rooms/participant_label.txt',
    ),
]

PARTICIPANT_FIELDS = []
SESSION_FIELDS = ['current_strategies_copy', 'avg_payoff_history', 'highcharts_landscape_series', 'highcharts_series', 'highcharts_payoff_series', 'remaining_freeze_period_for_all', 'if_freeze_next', 'if_freeze_now', 'start_timestamp']

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'en'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = True

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """ """

SECRET_KEY = '2784632633957'

INSTALLED_APPS = ['otree']

DEBUG = False