
VillainActionColor = "#ff0000" #red
HeroActionColor = "#00ff00" #green
FilterColor = "#88ffff00" #yellow
KOColor = "#bb000000" #black

markerTypes = {
    'block': ("Block", "block"),
    'stop': ("Stop", "stop"),
    'counter': ("Counter", "counter"),
    'Culture': ("Culture", "cul"),
    'Science': ("Science", "sci"),
    'Ingenuity': ("Ingenuity", "ing"),
    'Combat': ("Combat", "com"),
    'skill': ("Skill", "skill"),
    'diff': ("Difficulty", "diff")
    }

phaseDict = {
    0: ['pre.1load', 1],
    1: ['pre.2load', 2],
    2: ['pre.reg', 3],
    3: ['pre.vic', 4],
    4: ['pre.1mul', 5],
    5: ['pre.2mul', 6],
    6: ['pow.main', 7],
    7: ['mis.start', 8],
    8: ['mis.main', 9],
    9: ['mis.res', 10],
    10: ['mis.sucfail', 11],
    11: ['mis.adv', 12],
    12: ['mis.gly', 13],
    13: ['mis.end', 14],
    14: ['deb.start', 15],
    15: ['deb.ref', 16],
    16: ['deb.end', 0],
    17: ['endgame', 0]
    }

skillDict = {1: "Culture", 2: "Science", 3: "Combat", 4: "Ingenuity", 5: "all", 6: "Difficulty", "Culture": 1, "Science": 2, "Combat": 3, "Ingenuity": 4, "all": 5, "Difficulty": 6}
heroTypes = ["Support Character", "Team Character", "Gear", "Event", "Mission"]
villainTypes = ["Obstacle", "Adversary"]

#globalvar cards = {
#                "#": indexInt
#                'm':{mission skill boosts}
#                't':{turn skill boosts}
#                's':'status'
#                'g':[earned glyphs]
#                'b':[blocked cards]
#                'p':/True if it was previously assigned/
#                'rf':/True to remove failure text/
#                '!':(/True to enable activation of ! triggers/, Source, Duration)
#                'sel': selected cards
#                }

#queue = ( card, trigger, action, count, priority, skippable, source )
#gameStats = {
#               'fm':[failed missions]
#               'sm':[successful missions]
#               'nr': No Revive
#               'nnm': No Next Mission
#               'nmd': Next Mission Difficulty
#                }
#globalvar activemission = [mission type status]

storedTurnPlayer = 1
storedMission = None
storedVictory = 0
storedOppVictory = 0
storedCards = {}
storedGameStats = { 'fm': [], 'sm': []}
storedQueue = []
storedPriority = 0
storedPower = 0

scriptsDict = {
#### Game-based scripts
    'game': {
        'glyph': [
            ('glyph', {
                'target': {
                    'special': "queue"
                    }
                })
            ],
        'playCard': [
            ('playCard', {
                'target': {
                    'special': "queue",
                    'group': 'me.Team'
                    }
                })
            ],
        'revive': [
            ('revive', {
                'target': {
                    'special': "queue"
                    }
                })
            ],
        'assignCard': [
            ('statusChange', {
                'target': {
                    'special': "queue"
                    },
                'action': 'assign'
                })
            ],
        'stopCard': [
            ('statusChange', {
                'target': {
                    'special': "queue"
                    },
                'action': 'stop'
                })
            ],
        'failMiss': [
            ('statusChange', {
                'target': {
                    'special': "queue"
                    },
                'action': 'missionBottom',
                'count': "0"
                })
            ],
        'nextPhase': [
            ('phaseChange', {
                'phase': 'phaseDict[storedPhase][1]'
                })
            ],
        'setupStop': [
            ('setupStop', {})
            ],
        'discardTo8': [
            ('moveCard', {
                'target': {
                    'group': "me.hand"
                    },
                'to': ('me.Discard', 0),
                'count': "len(me.hand) - 8"
                }),
            ],
        'drawTo8': [
            ('fillHand', {
                'value': '8'
                })
            ]
        },
#### Card-specific scripts
    ## Merrin, Orbanian Urrone
    'cec32155-7eb9-4001-a923-1bf3b4ca0150': {
        'onAssign': [
            ('tagSet', {
                'target': {
                    'special': "self"
                    },
                'tag': '!',
                'value': 'True',
                'ignoreSource': True
                })
            ],
        'onMissionEnd': [
            ('statusChange', {
                'target': {
                    'special': "self"
                    },
                'condition': {
                    'custom': "storedCards[card._id].get('!', [False])[0]"
                    },
                'action': 'destroy'
                })
            ]
        },
    ## Brainwashing
    '2aebfd9e-d838-4542-846b-6861f2d6d369': {
        'onPlay': [
            ('statusChange', {
                'target': {
                    'type': ['Support Character']
                    },
                'player': 'villain',
                'action': 'block',
                'count': "1"
                }),
            ('statusChange', {
                'action': 'store',
                'target': {
                    'type': ['Support Character']
                    },
                'player': 'villain',
                'count': "1"
                })
            ],
        'onFailure': [
            ('statusChange', {
                'target': {
                    'special': "stored" 
                    },
                'action': 'destroy'
                })
            ]
        },
    ## Team Compromised
    'cbdd5fa9-138e-4e3e-ab51-552d1e3e675b': {
        'onPlay': [
            ('statusChange', {
                'target': {
                    'type': ['Team Character'],
                    'status': ['r']
                    },
                'action': 'block',
                'player': 'hero',
                'count': "1"
                })
            ]
        },
    ## Antarctic Rescue
    'aa340201-0599-4884-99aa-ecdf8b2abc53': {
        'onPlayMission': [
            ('statusChange', {
                'target': {
                    'type': ['Team Character'],
                    'status': ['s','a','r']
                    },
                'action': 'block',
                'player': 'villain',
                'count': "1"
                })
            ]
        },
    ## Sense of Adventure
    '745bea32-98ed-49ac-9120-52965ab2716c': {
        'onPlay': [
            ('statusChange', {
                'target': {
                    'type': ['Team Character', 'Support Character'],
                    'status': ['s','a','r']
                    },
                'action': 'ready',
                'player': 'hero',
                'count': "1"
                })
            ]
        },
    ## Jack O'Neil, SG-1 Commander
    '4901fb59-e7cc-47d4-8f3a-4f1f2e93f78d': {
        'onPlayMission': [
            ('powerChange', {
                'trigger': {
                    'glyph': "[['G','L']]"
                    },
                'player': 'hero',
                'value': '1'
                })
            ]
        },
    ## Harold Maybourne, Ally of Opportunity
    'c5358e72-16ac-450e-a2b8-923d4964f52c': {
        'onGetAbility1Cost': [
            ('statusChange', {
                'target': {
                    'special': "self"
                    },
                'condition': {
                    'status': ['a','r'],
                    'glyph': "[['S']]"
                    },
                'action': 'stop'
                })
            ],
        'onAbility1': [
            ('skillChange', {
                'target': {
                    'type': ['Team Character'],
                    'ignoreSelf': True
                    },
                'skill': ['all'],
                'value': '1',
                'duration': "m",
                'count': 'all',
                'ignoreSource': True
                })
            ]
        },
    ## Pandemic Containment
    'db9b3230-07e2-400a-92b3-679ae3a7254d': {
        'onGetComplicationCost': [
            ('costChange', {
                'value': "-1"
                })
            ]
        },
    ## Retrieve Artifact
    'e72c8088-c0f6-4692-a060-4e989ccc5c26': {
        'onGetComplicationCost': [
            ('costChange', {
                'value': "1"
                })
            ]
        },
    ## Wormhole X-Treme!
    'be5853cf-047c-4392-9ef4-7e2c1d3fd267': {
        'onGetPlayCost': [
            ('costChange', {
                'trigger': {
                    'type': ["Obstacle"]
                    },
                'value': "1"
                })
            ]
        },
    ## Teal'c, Enemy of the Goa'uld
    '5943d410-e654-46a4-9bc7-44124d8ee891': {
        'onGetComplicationCost': [
            ('costChange', {
                'condition': {
                    'glyph': "[['O']]",
                    'status': ["a"]
                    },
                'value': "1"
                }),
            ('costChange', {
                'condition': {
                    'glyph': "[['P']]",
                    'status': ["a"]
                    },
                'value': "1"
                })
            ]
        },
    ## Transport Rings
    '57e5bbd8-c2f4-4333-8aad-9934807ba6bd': {
        'onGetAbility1Cost': [
            ('statusChange', {
                'target': {
                    'special': "self"
                    },
                'condition': {
                    'status': ['r']
                    },
                'action': 'stop',
                }),
            ('powerChange', {
                'player': 'hero',
                'value': '-3'
                })
            ],
        'onAbility1': [
            ('statusChange', {
                'target': {
                    'status': ['s','a','r'],
                    'type': ['Support Character', 'Team Character']
                    },
                'action': 'ready',
                'player': 'hero',
                'count': "1"
                })
            ]
        },
    ## Fall of Earth
    ## You can't play support characters.
    '00e1be97-291d-4e37-aea1-2c386a707f20': {
        'onPlayMission': [
            ('ruleSet', {
                'rule': 'cp',
                'value': '"Support Character"',
                'list': True
                })
            ]
        },
    ## Zat Gun  ##TODO: Use ChooseMode code
    'a853c2fe-bd32-44fb-9794-5213d00dfe22': {
        'onGetAbility1Cost': [
            ('statusChange', {
                'target': {
                    'special': "self"
                    },
                'condition': {
                    'status': ['r']
                    },
                'action': 'stop'
                }),
            ('powerChange', {
                'player': 'hero',
                'value': '-1'
                })
            ],
        'onAbility1': [
            ('skillChange', {
                'target': {
                    'type': ['Obstacle'],
                    'skill': 'Combat'
                    },
                'skill': ['all'],
                'value': '-1',
                'player': 'hero',
                'count': "1",
                'duration': "m",
                'ignoreSource': True
                })
            ],
        'onGetAbility2Cost': [
            ('statusChange', {
                'target': {
                    'special': "self"
                    },
                'condition': {
                    'status': ['r']
                    },
                'action': 'stop'
                }),
            ('powerChange', {
                'player': 'hero',
                'value': '-2'
                })
            ],
        'onAbility2': [
            ('tagSet', {
                'target': {
                    'status': ['a'],
                    'type': ['Obstacle'],
                    'skill': 'Combat'
                    },
                'player': 'hero',
                'count': "1",
                'tag': 'rf',
                'value': 'True',
                'ignoreSource': True
                })
            ],
        'onGetAbility3Cost': [
            ('statusChange', {
                'target': {
                    'special': "self"
                    },
                'condition': {
                    'status': ['r']
                    },
                'action': 'stop'
                }),
            ('powerChange', {
                'player': 'hero',
                'value': '-1'
                })
            ],
        'onAbility3': [
            ('statusChange', {
                'target': {
                    'type': ['Obstacle'],
                    'skill': 'Combat',
                    'status': ['a']
                    },
                'action': 'destroy',
                'player': 'hero',
                'count': "1"
                })
            ]
        },
    ## Naquadah Reactor
    '5abf19d6-b076-4cfb-bcaf-dc90c573d687': {
        'onPowerEnd': [
            ('powerChange', {
                'player': 'hero',
                'value': '1'
                })
            ],
        'onGetAbility1Cost': [
            ('statusChange', {
                'target': {
                    'special': "self"
                    },
                'condition': {
                    'status': ['r']
                    },
                'action': 'destroy',
                }),
            ('powerChange', {
                'player': 'hero',
                'value': '-6'
                })
            ],
        'onAbility1': [
            ('statusChange', {
                'target': {
                    'status': ['a'],
                    'type': ['Obstacle']
                    },
                'action': 'destroy',
                'player': 'hero',
                'count': "1"
                })
            ]
        },
    ## Osbourne, Antarctic Researcher
    '3c381256-8ecd-4a17-ae67-dbe4a7b5305a': {
        'onGetAbility1Cost': [
            ('statusChange', {
                'target': {
                    'special': "self"
                    },
                'condition': {
                    'status': ['a','r']
                    },
                'action': 'stop',
                'count': "1"
                })
            ],
        'onAbility1': [
            ('fillHand', {
                'player': 'hero',
                'value': 'len(me.hand) + 1'
                })
            ]
        },
    ## Top Minds
    '4e172aed-da95-4717-a2a3-55bdf3835dca': {
        'onGetPlayCost': [
            ('statusChange', {
                'target': {
                    'status': ["a","r"],
                    'type': ["Team Character", "Support Character"]
                    },
                'action': 'stop',
                'player': "hero",
                'count': "2"
                })
            ],
        'onPlay': [
            ('statusChange', {
                'target': {
                    'status': ["a"],
                    'type': ["Obstacle"]
                    },
                'action': 'destroy',
                'player': "hero",
                'count': "1"
                })
            ]
        },
    ## Samantha Carter, Problem Solver
    'ebb511ee-abe9-4b91-9cea-e0cb3794bc21': {
        'onGetAbility1Cost': [
            ('statusChange', {
                'target': {
                    'special': "self"
                    },
                'condition': {
                    'status': ['a','r'],
                    'glyph': "[['T']]"
                    },
                'action': 'stop',
                'count': "1"
                })
            ],
        'onAbility1': [
            ('statusChange', {
                'target': {
                    'status': ['a'],
                    'type': ['Obstacle']
                    },
                'action': 'complication',
                'player': 'hero',
                'count': "1"
                })
            ]
        },
    ## Cameron Mitchell, Eager Adventurer
    'da9a7837-a593-4269-acb6-d88449a0d07a': {
        'onGetStats': [
            ('skillChange', {
                'trigger': "self",
                'condition': {
                    'glyph': "[['O']]",
                    'custom': "storedCards[card._id]['s'] == 'a' and len(storedGameStats['sm']) == 0 and len(storedGameStats['fm']) == 0"
                    },
                'skill': 'all',
#                'value': "1 if storedCards[card._id]['s'] == 'a' and len(storedGameStats['sm']) == 0 and len(storedGameStats['fm']) == 0 else 0"
                'value': "1"
                })
            ]
        },
    ## Bra'tac, Jaffa Master
    'dc4e26e7-2860-4851-9a5f-e53da0edf853': {
        'onGetStats': [
            ('skillChange', {
                'trigger': {
                    'type': ["Support Character"],
                    'trait': "Jaffa"
                    },
                'condition': {
                    'glyph': "[['L'],['S']]",
                    'status': ["r"]
                    },
                'skill': 'all',
                'value': "1"
                }),
            ('skillChange', {
                'trigger': {
                    'type': ["Support Character"],
                    'trait': "Jaffa"
                    },
                'condition': {
                    'glyph': "[['G','P']]",
                    'status': ["r"]
                    },
                'skill': 'all',
                'value': "1"
                })
            ]
        },
    ## Vala Mal Doran, Probationary Member of the SG
    '67af6d35-4256-40e4-9b75-bff404d6a234': {
        'onGetStats': [
            ('skillChange', {
                'trigger': "self",
                'skill': 'all',
                'value': "1 if storedCards[card._id]['s'] == 'a' and Card(storedMission[0]).Glyph in [Card(g).Glyph for g in storedCards[card._id].get('g', [])] else 0"
                })
            ]
        },
    ## Balinsky, Insightful Archaeologist
    '0f8362dc-132b-4eb3-96ec-453afddd5638': {
        'onGetStats': [
            ('skillChange', {
                'trigger': "self",
                'skill': 'all',
                'value': "1 if len(storedCards[card._id].get('g', [])) > len([c for c in storedCards if 'Obstacle' in Card(c).Type and storedCards[c]['s'] == 'a']) else 0"
                })
            ]
        },
    ## Daniel Jackson, Trained Fighter
    '77d8c4e5-1911-40f1-a0e8-08f01cc8d082': {
        'onGetStats': [
            ('skillChange', {
                'trigger': "self",
                'condition': {
                    'glyph': "[['G']]"
                    },
                'skill': ['Combat'],
                'value': "2"
                }),
            ('skillChange', {
                'trigger': "self",
                'condition': {
                    'glyph': "[['T']]"
                    },
                'skill': ['Combat'],
                'value': "1"
                })
            ]
        },
    ## Cloaked Ashrak
    'ec8f6292-17e1-4ab8-8af3-6e60e6ab4de7': {
        'onFailure': [
            ('statusChange', {
                'target': {
                    'type': ['Support Character']
                    },
                'action': 'destroy',
                'player': 'enemy',
                'count': "1"
                })
            ]
        },
    ## Parasitic Insects
    '6783ab0b-9da4-4375-9580-14ffb6661cf5': {
        'onFailure': [
            ('statusChange', {
                'target': {
                    'status': ['s','a','r'],
                    'type': ['Team Character']
                    },
                'action': 'stop',
                'player': 'villain',
                'count': "1"
                })
            ]
        },
    ## Water-Based Life Forms
    'cde9da8d-f010-4ff4-858e-c0777b931ecc': {
        'onFailure': [
            ('chooseMode', {
                'message': "Choose a mode for Water-Based Life Forms:",
                'choices': [
                    "Stop a Team Character.",
                    "Destroy a Support Character."
                    ],
                'player': 'villain',
                'count': "1"
                })
            ],
        'onFailure1': [
            ('statusChange', {
                'target': {
                    'status': ['s','a','r'],
                    'type': ['Team Character']
                    },
                'action': 'stop',
                'player': 'villain',
                'count': "1"
                })
            ],
        'onFailure2': [
            ('statusChange', {
                'target': {
                    'type': ['Support Character']
                    },
                'action': 'destroy',
                'player': 'hero',
                'count': "1"
                })
            ]
        },
    ## Apophis, Threat to Earth
    '578658c0-5c09-4d63-a46f-5d7b7e5e8c64': {
        'onAssign': [
            ('chooseMode', {
                'message': "Choose a mode for Apophis:",
                'choices': [
                    "Stop two Characters.",
                    "Allow your opponent to stop a Character."
                    ],
                'player': 'hero',
                'count': "1"
                })
            ],
        'onAssign1': [
            ('statusChange', {
                'target': {
                    'status': ['a','r'],
                    'type': ['Team Character', 'Support Character']
                    },
                'action': 'stop',
                'player': 'hero',
                'count': "2"
                })
            ],
        'onAssign2': [
            ('statusChange', {
                'target': {
                    'status': ['s','a','r'],
                    'type': ['Team Character', 'Support Character']
                    },
                'action': 'stop',
                'player': 'villain',
                'count': "1"
                })
            ]
        },
        #[(triggers, "game", "glyph", 0, turnPlayer()._id, False, mission)]
    ## Malek, Outpost Commander
    'f0c981ea-5b6f-4a98-a043-0ee5e6f0fb2e': {
        'onPlay': [
            ('statusChange', {
                'target': {
                    'status': ['g']
                    },
                'attachTarget': ["Team Character", "Support Character"],
                'action': 'glyph',
                'player': 'hero',
                'count': "1",
                'skippable': True
                })
            ]
        },
    ## Loyal Sacrifice
    'ba2f1ef2-93e4-41f9-9a92-faa537293c88': {
        'onPlay': [
            ('statusChange', {
                'target': {
                    'status': ['s','a','r'],
                    'type': ['Support Character'],
                    'trait': ['Jaffa']
                    },
                'action': 'destroy',
                'player': 'hero',
                'count': "999",
                'saveCount': True,
                'skippable': True
                }),
            ('statusChange', {
                'target': {
                    'status': ['s','a','r'],
                    'type': ["Team Character"]
                    },
                'action': 'ready',
                'player': 'hero',
                'count': "storedGameStats.get('sc', 0)"
                }),
            ('delCount', {
                })
            ]
        },
    ## Uncover the Stargate
    '786035e2-fd01-44d3-8442-4e015f62fa9a': {
        'onGetAssignCost': [
            ('powerChange', {
                'trigger': {
                    'type': ['Support Character'],
                    'status': ['r']
                    },
                'player': 'hero',
                'value': "-2"
                })
            ]
        },
    ## Stall Enemy
    '90c99fe3-8c27-4b90-8c91-46508712d0c6': {
        'onGetAssignCost': [
            ('powerChange', {
                'trigger': {
                    'type': ['Adversary']
                    },
                'player': 'villain',
                'value': "-len([c for c in storedCards if storedCards[c]['s'] == 'a' and Card(c).Type in ['Team Character', 'Support Character']])"
                })
            ]
        },
    ## Tight Rein
    '7bc7ab47-5fb6-40c5-b46b-91caf0ee6db0': {
        'onGetAssignCost': [
            ('statusChange', {
                'target': {
                    'status': ['a','r'],
                    'type': ['Team Character', 'Support Character'],
                    'ignoreSelf': True
                    },
                'trigger': {
                    'type': ['Team Character', 'Support Character']
                    },
                'action': 'stop',
                'player': 'hero',
                'count': "1",
                'ignoreSource': True
                })
            ]
        },
    ## Defeat Ashrak
    'ca77df97-efc9-4db8-875a-1eadd08fb4a9': {
        'onAssign': [
            ('powerChange', {
                'trigger': {
                    'type': ['Team Character', 'Support Character'],
                    'glyph': "[['O'],['G'],['L'],['P'],['T'],['S']]"
                    },
                'player': 'villain',
                'value': '-1',
                })
            ]
        },
    ## Training Exercises
    '4edbb9ee-d752-4d0d-9a21-96463be4a125': {
        'onAssign': [
            ('powerChange', {
                'trigger': {
                    'type': ['Team Character', 'Support Character'],
                    'glyph': 'None'
                    },
                'player': 'villain',
                'value': '+1',
                })
            ]
        },
    ## Nicholas Ballard, Outcast Scholar
    ## Discard a card - Nicholas Ballard gets CUL +2 until the end of the current mission.
    'db2e0e15-0970-4302-a434-d37c410d10f9': {
        'onGetAbility1Cost': [
            ('moveCard', {
                'target': {
                    'group': "me.hand"
                    },
                'to': {
                    'group': 'me.Discard', 
                    'index': '0',
                    'min': '1',
                    'max': '1'
                    },
                'condition': {
                    'custom': "storedCards[card._id].get('!', (False, None))[0] == False"
                    },
                'player': 'hero'
                })
            ],
        'onAbility1': [
            ('skillChange', {
                'target': {
                    'special': "self"
                    },
                'skill': ['Culture'],
                'value': '2',
                'duration': "m",
                'ignoreSource': True
                }),
            ('tagSet', {
                'target': {
                    'special': "self"
                    },
                'tag': '!',
                'value': 'True',
                'ignoreSource': True
                })
            ],
        'onMissionEnd': [
            ('statusChange', {
                'target': {
                    'special': "self"
                    },
                'condition': {
                    'custom': "storedCards[card._id].get('!', [False])[0]"
                    },
                'action': 'destroy',
                })
            ]
        },
    ## Tolok, Jaffa Elder
    ## When you play Tolok, you may pay 2 power and discard a card.
    ## If you do, ready another Jaffa character.
    '20b010bf-9c8c-45dc-8ea6-7d2df55f80a5': {
        'onPlayCost': [
            ('powerChange', {
                'player': 'hero',
                'value': '-2'
                }),
            ('moveCard', {
                'target': {
                    'group': "me.hand"
                    },
                'to': {
                    'group': 'me.Discard',
                    'index': '0',
                    'min': '1',
                    'max': '1'
                    },
                'player': 'hero'
                }),
            ('confirm', {
                'message': "Tolok's ability: Pay 2 power and discard a card, to ready another Jaffa character?",
                })
            ],
        'onPlay': [
            ('statusChange', {
                'target': {
                    'type': ['Team Character', 'Support Character'],
                    'trait': 'Jaffa',
                    'status': ['s','a'],
                    'ignoreSelf': True
                    },
                'action': 'ready',
                'player': 'hero',
                'count': "1"
                })
            ]
        },
    ## Out of Your Depth
    ## Failure: You may take a SCI obstacle card from your discard pile into hand.
    'b95f875a-0f2a-416a-bdc9-6b7aac41ffa8': {
        'onFailure': [
            ('moveCard', {
                'target': {
                    'type': ['Obstacle'],
                    'skill': 'Science',
                    'group': 'me.Discard'
                    },
                'to': {
                    'group': 'me.hand',
                    'index': '-1',
                    'min': '1',
                    'max': '1'
                    },
                'player': 'villain',
                'skippable': True
                })
            ]
        },
    ## Conduct Repairs
    ## Success: You may take a gear card from your discard pile into hand.
    'b443d736-2f46-4176-94b4-6c18f57cdf84': {
        'onSuccess': [
            ('moveCard', {
                'target': {
                    'type': ['Gear'],
                    'group': 'me.Discard'
                    },
                'to': {
                    'group': 'me.hand',
                    'index': '-1',
                    'min': '1',
                    'max': '1'
                    },
                'player': 'hero',
                'skippable': True
                })
            ]
        },
    ## Research Advanced Races
    ## Success: You may look at the top card of your mission pile, then place it on the top or bottom of that pile.
    'b457732b-04e3-4d0e-afb7-68d3dc6b848c': {
        'onSuccess': [
            ('moveCard', {
                'target': {
                    'group': 'me.piles["Mission Pile"]',
                    'top': "1"
                    },
                'to': {
                    'group': 'me.piles["Mission Pile"]',
                    'index': '0',
                    'label': 'Top of Mission Pile'
                    },
                'altTo': {
                    'group': 'me.piles["Mission Pile"]',
                    'index': '-1',
                    'label': 'Bottom of Mission Pile'
                    },
                'player': 'hero',
                'skippable': True
                })
            ]
        },
    ## Attend Triad
    ## Success: You may take a character card from your discard pile into hand.
    '7cd9c3b2-a979-460a-ae6d-0fa1dbe1431b': {
        'onSuccess': [
            ('moveCard', {
                'target': {
                    'type': ['Support Character', 'Team Character'],
                    'group': 'me.Discard'
                    },
                'to': {
                    'group': 'me.hand',
                    'index': '-1',
                    'min': '1',
                    'max': '1'
                    },
                'player': 'hero',
                'skippable': True
                })
            ]
        },
    ## Prevent Invasion
    ## When you play this mission, your opponent may take an obstacle card from his discard pile into hand.
    'a4e3f614-51f0-4976-8ee5-ca96f3e0cf63': {
        'onPlayMission': [
            ('moveCard', {
                'target': {
                    'type': ['Obstacle'],
                    'group': 'me.Discard'
                    },
                'to': {
                    'group': 'me.hand',
                    'index': '-1',
                    'min': '1',
                    'max': '1'
                    },
                'player': 'villain',
                'skippable': True
                })
            ]
        },
    ## Receiving a Go
    ## Look at one card from the top of your mission pile for each ready SGC character.
    ## Place those cards in any order on the top and/or bottom of that pile.
    '7861d9aa-aafb-448c-8c4d-98e691d3f53a': {
        'onPlay': [
            ('moveCard', {
                'target': {
                    'group': 'me.piles["Mission Pile"]',
                    'top': "len([c for c in storedCards if cardActivity(Card(c)) != 'inactive' and storedCards[c]['s'] == 'r' and Card(c).Type in ['Support Character', 'Team Character'] and 'SGC' in Card(c).Traits])"
                    },
                'to': {
                    'group': 'me.piles["Mission Pile"]',
                    'index': '0',
                    'label': 'Top of Mission Pile'
                    },
                'altTo': {
                    'group': 'me.piles["Mission Pile"]',
                    'index': '-1',
                    'label': 'Bottom of Mission Pile'
                    },
                'player': 'hero'
                })
            ]
        },
    ## Establish Communications
    ## Each time you assign Jack O'Neill, you may discard any number of cards, 
    ## then refill your hand.
    'edee7ab2-f431-4c28-b808-d6fa1ed59cc2': {
        'onAssign': [
            ('moveCard', {
                'trigger': {
                    'cardName': "Jack O'Neill"
                    },
                'target': {
                    'group': "me.hand"
                    },
                'to': {
                    'group': 'me.Discard', 
                    'index': '0'
                    },
                'player': 'hero',
                'skippable': True
                }),
            ('fillHand', {
                'trigger': {
                    'cardName': "Jack O'Neill"
                    },
                'player': 'hero',
                'value': '8'
                })
            ]
        },
    ## Explore Genetics Lab
    ## Failure: Your opponent may discard a card, then refill his hand.
    '03ee4c09-1daa-43ed-a096-0b39cbbf1545': {
        'onFailure': [
            ('moveCard', {
                'target': {
                    'group': "me.hand"
                    },
                'to': {
                    'group': 'me.Discard',
                    'index': '0',
                    'max': '1'
                    },
                'player': 'villain',
                'skippable': True
                }),
            ('fillHand', {
                'player': 'villain',
                'value': '8'
                })
            ]
        },
    ## Galaran Memory Device
    ## Stop this gear, discard a card - 
    ## Take a hero card from your discard pile and shuffle that card into your deck.
    '4e5d26f3-522e-43b4-b560-012b81b27a01': {
        'onGetAbility1Cost': [
            ('statusChange', {
                'target': {
                    'special': "self"
                    },
                'condition': {
                    'status': ['r']
                    },
                'action': 'stop'
                }),
            ('moveCard', {
                'target': {
                    'group': "me.hand"
                    },
                'to': {
                    'group': 'me.Discard',
                    'index': '0',
                    'min': '1',
                    'max': '1'
                    },
                'player': 'hero'
                })
            ],
        'onAbility1': [
            ('moveCard', {
                'target': {
                    'type': ['Team Character', 'Support Character', 'Event', 'Gear'],
                    'group': 'me.Discard'
                    },
                'to': {
                    'group': 'me.Deck',
                    'index': '0',
                    'min': '1',
                    'max': '1'
                    },
                'player': 'hero',
                }),
            ('shuffle', {
                'group': 'me.Deck',
                'player': 'hero'
                })
            ]
        },
    ## Salvage Technology
    ## Success: You may search your deck for a card. 
    ## If you do, reveal it, take it into hand, and shuffle your deck.
    'c81249ce-abc2-489c-a32c-28ca0e18293b': {
        'onSuccess': [
            ('moveCard', {
                'target': {
                    'type': ['Gear'],
                    'group': 'me.Deck'
                    },
                'to': {
                    'group': 'me.hand',
                    'index': '-1',
                    'min': '1',
                    'max': '1'
                    },
                'player': 'hero',
                'skippable': True
                }),
            ('shuffle', {
                'group': 'me.Deck',
                'player': 'hero'
                })
            ]
        },
    ## Cure the Vorlix
    ## Success: You may search your deck for a character card.
    ## If you do, reveal it, take it into hand, and shuffle your deck.
    '99856f4c-c9d8-44de-8044-b995d84ce141': {
        'onSuccess': [
            ('moveCard', {
                'target': {
                    'type': ['Support Character', 'Team Character'],
                    'group': 'me.Deck'
                    },
                'to': {
                    'group': 'me.hand',
                    'index': '-1',
                    'min': '1',
                    'max': '1'
                    },
                'player': 'hero',
                'skippable': True
                }),
            ('shuffle', {
                'group': 'me.Deck',
                'player': 'hero'
                })
            ]
        },
    ## Ill-Gotten Gains
    ## To play this event, stop a team character.
    ## Search your deck for a card, reveal it, take it into hand, and shuffle your deck.
    'f8a88854-b6b8-4ccc-aa15-268d5539776c': {
        'onGetPlayCost': [
            ('statusChange', {
                'target': {
                    'status': ['r'],
                    'type': ['Team Character']
                    },
                'action': 'stop',
                'player': 'hero',
                'count': "1"
                })
            ],
        'onPlay': [
            ('moveCard', {
                'target': {
                    'type': ['Gear'],
                    'group': 'me.Deck'
                    },
                'to': {
                    'group': 'me.hand',
                    'index': '-1',
                    'min': '1',
                    'max': '1'
                    },
                'player': 'hero',
                }),
            ('shuffle', {
                'group': 'me.Deck',
                'player': 'hero'
                })
            ]
        },
    ## Relocate Advanced Civilizations
    '2bb7b341-26e1-495a-bd27-1635d81dcc5f': {
        'onPlayMission': [
            ('fillHand', {
                'player': 'enemy',
                'value': '8'
                })
            ]
        },
    ## Dialing Computer
    '39b6a212-7c89-4327-ae56-ae9d49e9935e': {
        'onDebrief': [
            ('statusChange', {
                'target': {
                    'type': ['Mission'],
                    'status': ['f']
                    },
                'action': 'mission',
                'player': 'hero',
                'skippable': True,
                'count': "len(storedGameStats['fm'])"
                })
            ]
        },
    ## Destroy Minor Goa'uld
    '7b22ba1c-5432-4ec9-bfdb-66e49180dcae': {
        'onSuccess': [
            ('statusChange', {
                'target': {
                    'type': ['Adversary']
                    },
                'action': 'destroy',
                'player': 'hero',
                'count': "1"
                })
            ]
        },
    ## Expose Blackmail
    'cbde5070-f65b-4f31-a929-9202aedfd374': {
        'onSuccess': [
            ('statusChange', {
                'target': {
                    'type': ['Support Character'],
                    'status': ['s','a','r']
                    },
                'action': 'ready',
                'player': 'hero',
                'count': "1"
                })
            ]
        },
    ## Acquire Specimen
    'b73da326-be80-41c8-b201-a0e6d7bf2ec6': {
        'onGetStats': [
            ('skillChange', {
                'trigger': "self",
                'skill': 'all',
                'value': "len([c for c in storedCards if storedCards[c]['s'] == 'a' and 'Obstacle' in Card(c).Type])"
                })
            ]
        },
    ## Infiltrate Summit
    'c0f58ccb-3278-4769-9040-31fec6b363ca': {
        'onGetStats': [
            ('skillChange', {
                'trigger': "self",
                'skill': 'all',
                'value': "0 if len([c for c in storedCards if storedCards[c]['s'] == 'a' and 'Adversary' in Card(c).Type]) == 0 else 1"
                })
            ]
        },
    ## Escape the Keeper
    'f2062900-e1ba-4d57-9d59-d571c7714fcb': {
        'onGetStats': [
            ('skillChange', {
                'trigger': "self",
                'skill': 'all',
                'value': "sum([len(storedCards[c]['g']) for c in storedCards if storedCards[c]['s'] == 'a' and 'g' in storedCards[c] ])"
                })
            ]
        },
    ## Survey Goa'uld Pleasure Palace
    'c4bf0315-ee48-4fd9-b02c-322f1b41e779': {
        'onGetStats': [
            ('skillChange', {
                'trigger': "self",
                'skill': 'all',
                'value': "1 if len([c for c in storedCards if storedCards[c]['s'] == 'c']) > 0 else 0"
                })
            ]
        },
    ## Seasoned Travelers
    '414ef0db-fe27-48c0-9e7a-9e13b346482b': {
        'onPlay': [
            ('skillChange', {
                'target': {
                    'type': ['Team Character']
                    },
                'skill': ['all'],
                'value': 'len(storedCards[card._id].get("g", []))',
                'player': 'hero',
                'count': '1',
                'duration': 'm',
                'ignoreSource': True
                })
            ]
        },
    ## Seek Assistance
    ## Each assigned Asgard character gets CUL +1.
    ## Success: The next mission this turn gets difficulty -1.
    'de071fbb-e426-4bb2-8ed5-d40bd7f28e7c': {
        'onGetStats': [
            ('skillChange', {
                'trigger': {
                    'type': ['Support Character', 'Team Character'],
                    'status': ['a'],
                    'trait': 'Asgard'
                    },
                'skill': ['Science'],
                'value': '1'
                })
            ],
        'onSuccess': [
            ('ruleSet', {
                'rule': 'nmd',
                'value': '-1',
                'list': True,
                
                })
            ]
        },
    ## Locate Renegades
    ## Failure: The next mission played this turn gets difficulty +1.
    '46b646c3-d60a-4030-8364-dab849d0f5ca': {
        'onFailure': [
            ('ruleSet', {
                'rule': 'nmd',
                'value': '1',
                'list': True
                })
            ]
        },
    ## Offworld Research
    'ec0d04f8-07e6-489f-8705-68aafac29407': {
        'onGetStats': [
            ('skillChange', {
                'trigger': {
                    'type': ['Support Character'],
                    'status': ['a']
                    },
                'skill': ['Science'],
                'value': '1'
                })
            ]
        },
    ## Evacuate Village
    'db9e6362-9cc3-4e4c-ba0c-0058379d12be': {
        'onGetStats': [
            ('skillChange', {
                'trigger': {
                    'type': ['Team Character'],
                    'status': ['a'],
                    'glyph': "[['O'],['G'],['L'],['P'],['T'],['S']]"
                    },
                'skill': ['Combat'],
                'value': '1'
                })
            ]
        },
    ## Martouf, Tok'ra Liaison
    '7dc161c5-2a99-4fb7-b3ee-0c421f48ad41': {
        'onGetStats': [
            ('skillChange', {
                'trigger': {
                    'type': ['Team Character', 'Support Character'],
                    'glyph': "[ [Card(x).Glyph] for x in storedCards[sourceId].get('g', [])]",
                    'ignoreSelf': True
                    },
                'skill': 'all',
                'value': '1'
                })
            ]
        },
    ## Loop of Kon Garat
    'dadf8a7e-525c-4440-9339-b9fe908ca265': {
        'onGetStats': [
            ('skillChange', {
                'trigger': "self",
                'condition': {
                    'custom': "len([c for c in storedCards if storedCards[c]['s'] == 'a' and Card(c).name == 'Samantha Carter']) > 0"
                    },
                'skill': 'all',
                'value': "-1"
                })
            ]
        },
    ## Pursue the Harcesis
    '1b4317d7-c293-46c2-aa30-87dae348e5c0': {
        'onGetStats': [
            ('skillChange', {
                'trigger': {
                    'cardName': ['Daniel Jackson']
                    },
                'skill': ['Culture'],
                'value': "len([c for c in storedCards if c != card._id and 'Team Character' in Card(c).Type and storedCards[c]['s'] == 'a'])"
                })
            ]
        },
    ## Special Training
    '33adafa3-d70e-46c9-9bd0-54ed1a1d77d7': {
        'onPlay': [
            ('skillChange', {
                'target': {
                    'type': ['Team Character']
                    },
                'skill': ['Science'],
                'value': '2 if "NID" in card.Traits else 1',
                'player': 'hero',
                'count': '1',
                'duration': 'm',
                'ignoreSource': True
                })
            ]
        },
    ## Search and Rescue
    'bcbbceee-417b-47a9-ae15-b11445a5dacb': {
        'onSuccess': [
            ('statusChange', {
                'target': {
                    'status': ['s','a','r'],
                    'type': ['Support Character', 'Team Character']
                    },
                'action': 'ready',
                'player': 'hero',
                'count': "1"
                })
            ]
        },
    ## Telekinetic Mutants
    'b5e4ff90-7a72-4696-a937-6542aef7af54': {
        'onPlay': [
            ('statusChange', {
                'target': {
                    'status': ['a','r'],
                    'type': ['Support Character', 'Team Character']
                    },
                'action': 'stop',
                'player': 'hero',
                'count': "1"
                })
            ]
        },
    ## Anubis, Banished Lord
    '2ecceca6-cd9d-4323-9aa4-6408626785b3': {
        'onPlay': [
            ('statusChange', {
                'target': {
                    'type': ['Support Character']
                    },
                'action': 'destroy',
                'player': 'villain',
                'count': "1"
                })
            ],
        'onRevive': [
            ('statusChange', {
                'target': {
                    'type': ['Support Character']
                    },
                'action': 'destroy',
                'player': 'hero',
                'count': "1"
                })
            ]
        },
    ## Loss of Funding
    '558106d3-ce22-43e1-92e8-8289723abc3a': {
        'onFailure': [
            ('statusChange', {
                'target': {
                    'status': ['s','a','r'],
                    'type': ['Support Character', 'Team Character']
                    },
                'action': 'stop',
                'player': 'hero',
                'count': 'all'
                })
            ]
        },
    ## Prison Break
    '9db0d9a1-edcd-45b4-947b-b4b979becac4': {
        'onPlayMission': [
            ('statusChange', {
                'target': {
                    'status': ['s','a','r'],
                    'type': ['Support Character']
                    },
                'action': 'stop',
                'player': 'hero',
                'count': 'all'
                })
            ],
        'onSuccess': [
            ('statusChange', {
                'target': {
                    'status': ['s','a','r'],
                    'type': ['Support Character']
                    },
                'action': 'ready',
                'player': 'hero',
                'count': 'all'
                })
            ]
        },
    ## Troop Landing
    'a2076dc6-9eea-420d-8db2-d7b2fa94e3ab': {
        'onFailure': [
            ('statusChange', {
                'target': {
                    'type': ['Support Character'],
                    'status': ['a', 's']
                    },
                'action': 'destroy',
                'player': 'villain',
                'count': "1"
                })
            ]
        },
    ## Salish Spirits
    '799a40e0-a9a9-4d4b-a548-b4a00bb004db': {
        'onFailure': [
            ('statusChange', {
                'target': {
                    'type': ['Support Character']
                    },
                'action': 'destroy',
                'player': 'villain',
                'count': "1"
                })
            ]
        },
    ## Cultural Exchange
    '24c42819-dc31-418c-b7f4-2b1183bacc7e': {
        'onPlayMission': [
            ('statusChange', {
                'target': {
                    'status': ['s','a'],
                    'type': ['Support Character']
                    },
                'action': 'ready',
                'player': 'hero',
                'skippable': True,
                'count': "1"
                })
            ]
        },
    ## Beneath the Surface
    '9f4d63c9-3b86-4f63-9d69-1232f3ca6122': {
        'onPlayMission': [
            ('statusChange', {
                'target': {
                    'status': ['s','a','r'],
                    'type': ['Team Character']
                    },
                'action': 'stop',
                'player': 'villain',
                'count': "1"
                })
            ]
        },
    ## Seek and Capture
    '7f109410-f062-44b2-9a84-bf51d698d4e3': {
        'onPlayMission': [
            ('statusChange', {
                'target': {
                    'type': ['Adversary'],
                    'status': ['a','r']
                    },
                'action': 'stop',
                'player': 'villain',
                'count': "1"
                })
            ]
        },
    ## Repel Cronus
    'c820d3f8-80a3-48fc-8dd3-0968cb7b9c23': {
        'onPlayMissionCost': [
            ('powerChange', {
                'player': 'hero',
                'value': '-1'
                }),
            ('confirm', {
                'message': "Repel Cronus's ability: Pay 1 power to ready Teal'c?",
                })
            ],
        'onPlayMission': [
            ('statusChange', {
                'target': {
                    'cardName': ["Teal'c"],
                    'status': ['s','a','r']
                    },
                'action': 'ready',
                'player': 'hero',
                'count': "1"
                })
            ]
        },
    ## Investigate Disappearance
    '43f27324-da6d-4009-802f-c670e76e4e70': {
        'onPlayMission': [
            ('statusChange', {
                'target': {
                    'type': ['Support Character']
                    },
                'action': 'destroy',
                'player': 'hero',
                'count': "1"
                })
            ]
        },
    ## Brief Candle
    '1db24625-e050-4a61-a0fe-c35e2cff1afe': {
        'onPlayMission': [
            ('statusChange', {
                'target': {
                    'type': ['Support Character', 'Team Character'],
                    'status': ['a','r']
                    },
                'action': 'stop',
                'player': 'hero',
                'count': "1"
                })
            ]
        },
    ## Fire Rain
    '8a097812-9963-4da7-ae55-0ff0196bfcff': {
        'onPlay': [
            ('statusChange', {
                'target': {
                    'type': ['Team Character', 'Support Character']
                    },
                'action': 'block',
                'player': 'villain',
                'count': "len([c for c in storedCards if 'Obstacle' in Card(c).Type and storedCards[c]['s'] == 'a']) - 1"
                })
            ]
        },
    ## Serpent Guards
    '7b84361c-da40-4a9a-8c2e-c4a327109f71': {
        'onGetPlayCost': [
            ('costChange', {
                'trigger': 'self',
                'condition': {
                    'custom': "len([c for c in storedCards if 'Team Character' in Card(c).Type and storedCards[c]['s'] == 'a' and len(storedCards[c].get('g',[])) == 0]) > 0"
                    },
                'value': "-1"
                })
            ]
        },
    ##Drey'auc
    '75708da0-602d-40f0-9381-b6cc3940ce23': {
        'onGetPlayCost': [
            ('costChange', {
                'trigger': 'self',
                'condition': {
                    'custom': "len(storedGameStats['sm']) > 0"
                    },
                'value': "-2"
                })
            ]
        },
    ## Artok
    '87b224b8-8ae0-4081-aef3-5863b67bad26': {
        'onGetPlayCost': [
            ('costChange', {
                'trigger': 'self',
                'condition': {
                    'custom': "storedMission[1] == 'Combat'"
                    },
                'value': "-1"
                }),
            ('costChange', {
                'trigger': 'self',
                'condition': {
                    'custom': "len([c for c in storedCards if Card(c).isFaceUp == False and storedCards[c]['s'] == 'c']) >= 1"
                    },
                'value': "-1"
                })
            ]
        },
    ## Time Loop
    ## Failure: You can't play any more missions this turn.
    '9f7363f0-0281-46d1-906c-da6ebcb61d3d': {
        'onFailure': [
            ('ruleSet', {
                'rule': 'nnm',
                'value': 'True'
                })
            ]
        },
    ## Contact the Asgard
    ## Success: Assigned adversaries can't be revived.
    '55047674-bacb-42d3-b9b7-ad515f27830c': {
        'onSuccess': [
            ('tagSet', {
                'target': {
                    'status': ['a'],
                    'type': ['Adversary']
                    },
                'player': 'hero',
                'tag': 'nr',
                'value': 'True',
                'ignoreSource': True
                })
            ]
        },
    ## Investigate Plague
    'f23eb8cc-5ecb-406e-824b-5549f356e317': {
        'onPlayMission': [
            ('powerChange', {
                'player': 'hero',
                'value': '-2'
                })
            ]
        },
    ## Supply Raid
    '5fbb2f8b-9b01-41f2-ad7d-d5aba336bcef': {
        'onSuccess': [
            ('powerChange', {
                'player': 'villain',
                'value': '-2'
                })
            ]
        },
    ## Destroy Battleship
    'ec130081-a970-4640-90d6-23f86970f654': {
        'onFailure': [
            ('powerChange', {
                'player': 'villain',
                'value': '2'
                })
            ]
        },
    ## Nyan
    '5f48ec23-8316-45e9-b6b9-a90ca1ad3f59': {
        'onSuccess': [
            ('powerChange', {
                'player': 'villain',
                'value': '-2'
                }),
            ('powerChange', {
                'player': 'hero',
                'value': '1'
                })
            ]
        },
    ## Rescue Operative
    ## When you play this mission, your opponent chooses a support character.
    ## Failure: Destroy the chosen character
    '3062cb52-5800-409d-b4a4-eb7f28f7dc27': {
        'onPlayMission': [
            ('statusChange', {
                'target': {
                    'type': ['Support Character']
                    },
                'action': 'store',
                'player': 'villain',
                'count': "1"
                })
            ],
        'onFailure': [
            ('statusChange', {
                'target': {
                    'special': "stored" 
                    },
                'action': 'destroy',
                })
            ]
        },
    ## Avert Disaster
    '7a3fddf6-79b3-4fbb-9974-f77169128116': {
        'onFailure': [
            ('statusChange', {
                'target': {
                    'type': ['Support Character']
                    },
                'action': 'destroy',
                'count': 'all'
                })
            ]
        },
    ## Bill Lee
    '2ecaf65d-1fe8-4cd7-8824-3160aef1d99b': {
        'onGetStats': [
            ('skillChange', {
                'trigger': "self",
                'skill': 'all',
                'value': "len(storedGameStats['sm'])"
                })
            ]
        },
    ## Convert Jaffa
    '7ee0dd5e-05ab-4a8c-848f-52792b362509': {
        'onGetStats': [
            ('skillChange', {
                'trigger': "self",
                'skill': 'all',
                'value': "1 if len(storedGameStats['sm']) == 0 else 0"
                })
            ]
        },
    ## What Fate Omaroca?
    'f4d43cdf-496a-40a6-9b5e-995a7db693fd': {
        'onGetStats': [
            ('skillChange', {
                'trigger': "self",
                'condition': {
                    'custom': "len([c for c in storedCards if storedCards[c]['s'] == 'a' and hasGlyph(storedCards[c].get('g',[]), [['G']])]) > 0"
                    },
                'skill': 'all',
                'value': "-1"
                })
            ]
        },
    ## Yu, the Great
    'dd59e9ee-9cf8-4d61-b891-5477c550b2b1': {
        'onGetStats': [
            ('skillChange', {
                'trigger': "self",
                'skill': 'all',
                'value': "len(storedGameStats['sm'])"
                })
            ]
        },
    ## Robert Kinsey
    '13b58f59-4156-4d15-9c27-3212d8448b65': {
        'onGetStats': [
            ('skillChange', {
                'trigger': "self",
                'skill': 'all',
                'value': "len([c for c in storedCards if storedCards[c]['s'] == 'a' and 'Obstacle' in Card(c).Type and 'Political' in Card(c).Traits]) + len(storedGameStats['fm'])"
                })
            ]
        },
    ## Red Sky
    'c2675662-cb79-4dc3-9507-64b1ebad8939': {
        'onGetStats': [
            ('skillChange', {
                'trigger': "self",
                'skill': 'all',
                'value': "len(storedGameStats['fm'])"
                })
            ]
        },
    ## Gerak, Leader of the Jaffa
    '0a124022-4054-4952-83d9-3ac43d16e7a1': {
        'onGetStats': [
            ('skillChange', {
                'trigger': "self",
                'condition': {
                    'custom': "me.Power >= 4"
                    },
                'skill': 'all',
                'value': "1"
                })
            ]
        },
    ## Disclosure
    '88e10d1d-e999-47ce-816c-9ba043641339': {
        'onGetStats': [
            ('skillChange', {
                'trigger': "self",
                'skill': 'all',
                'value': "len(storedGameStats['fm'])"
                })
            ]
        },
    ## Language Barrier
    'bbf126d3-587e-4be7-bd1d-121b79917281': {
        },
    ## Harsh Conditions
    'b52fa628-3c10-44ce-829b-4f9241bf6949': {
        },
    ## TEMPLATE CARD
    'guid': {
        'scriptHook': [
            ('scriptType', {
                'att1': 'val1',
                'att2': 'val2'
                })
            ]
        }
    }

def createDecks():
    mute()
    reloadLocalVars()
    me.setGlobalVariable("loadedCards", "[]")
    if not getSetting("debugMode", False):
        return
    scriptCards = []
    rand = askChoice("choose a deck:", ["O'Neil", "Jackson", "Carter", "Teal'c"])
#    rand = rnd(0,3)
    if rand == 1:
            deck = oneil
    elif rand == 2:
            deck = jackson
    elif rand == 3:
            deck = carter
    else:
            deck = tealc
    for c in deck['main']:
        qty, guid, name = c
        me.Deck.create(guid, qty)
        if guid not in scriptsDict:
            scriptCards.append(name)
    for c in deck['team']:
        qty, guid, name = c
        me.Team.create(guid, qty)
        if guid not in scriptsDict:
            scriptCards.append(name)
    for c in deck['mission']:
        qty, guid, name = c
        me.piles['Mission Pile'].create(guid, qty)
        if guid not in scriptsDict:
            scriptCards.append(name)
    if me.isInverted:
        registerTeam()
        remoteCall(players[1], "registerTeam", [])

def genTestCards(group, x = 0, y = 0):
    mute()
    for x in scriptsDict:
        if 'test' in scriptsDict[x]:
            me.hand.create(x)
