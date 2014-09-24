
VillainActionColor = "#ff0000" #red
HeroActionColor = "#0000ff" #blue
BlockColor = "#ffff00" #yellow
KOColor = "#ffffff" #black

markerTypes = {
    'block': ("Block", "fc100fdc-aa4b-4429-97f5-02a7ccca2697"),
    'stop': ("Stop", "077ba8c6-840c-451f-9c3e-fe6856ccd0e9"),
    'counter': ("Counter", "b36d99e1-c1a0-4be6-b663-9cf3537b240a"),
    'Culture': ("Culture", "8426eeb9-478f-411c-98a4-48f24acd0602"),
    'Science': ("Science", "4dddc0c6-0c6b-4d21-8e53-d8af7cd789d5"),
    'Ingenuity': ("Ingenuity", "e9f07ca9-51c6-4c36-a3af-d06e3684d278"),
    'Combat': ("Combat", "74aa2881-b871-4452-ba25-c3c34dd10d7a"),
    'skill': ("Skill", "05660912-e56c-4eb3-8aa8-c06af722b3b3"),
    'diff': ("Difficulty", "8f61a0d9-615d-4382-b884-7fc27d5b615e")

    }

skillDict = {1: "Culture", 2: "Science", 3: "Combat", 4: "Ingenuity", 5: "all", "Culture": 1, "Science": 2, "Combat": 3, "Ingenuity": 4, "all": 5}
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
#                'gs':/True to trigger global static stat changes/, Source, Duration)
#                }

#queue = ( card, trigger, action, count, priority, skippable, source )
#gameStats = {
#               'fm':[failed missions]
#               'sm':[successful missions]
#               'nr': No Revive
#               'nnm': No Next Mission
#                }
#globalvar activemission = [mission type status]

storedTurnPlayer = None
storedPhase = "pre.1reg"
storedMission = None
storedVictory = 0
storedOppVictory = 0
storedCards = {}
storedGameStats = {}
storedQueue = []

scriptsDict = {
    ## Merrin, Orbanian Urrone
    'cec32155-7eb9-4001-a923-1bf3b4ca0150': {
        'onAssign': [
            ('tagSet', {
                'target': 'self',
                'tag': '!',
                'value': 'True',
                'ignoreSource': True
                })
            ],
        'onMissionEnd': [
            ('statusChange', {
                'target': 'self',
                'condition': {
                    'custom': "storedCards[card._id].get('!', [False])[0]"
                    },
                'action': 'destroy'
                })
            ]
        },
    ## Nicholas Ballard, Outcast Scholar
    'db2e0e15-0970-4302-a434-d37c410d10f9': {
        'onAbility1Cost': [
            ('discard', {
                'condition': {
                    'custom': "storedCards[card._id].get('!', (False, None))[0] == False"
                    },
                'player': 'hero',
                'count': '1'
                })
            ],
        'onAbility1': [
            ('skillChange', {
                'target': 'self',
                'skill': ['Culture'],
                'value': '2',
                'duration': "m",
                'ignoreSource': True
                }),
            ('tagSet', {
                'target': 'self',
                'tag': '!',
                'value': 'True',
                'ignoreSource': True
                })
            ],
        'onMissionEnd': [
            ('statusChange', {
                'target': 'self',
                'condition': {
                    'custom': "storedCards[card._id].get('!', [False])[0]"
                    },
                'action': 'destroy',
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
                'target': 'stored',
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
                'condition': {
                    'glyph': [['G','L']]
                    },
                'player': 'hero',
                'value': '1'
                })
            ]
        },
    ## Harold Maybourne, Ally of Opportunity
    'c5358e72-16ac-450e-a2b8-923d4964f52c': {
        'onAbility1Cost': [
            ('statusChange', {
                'target': 'self',
                'condition': {
                    'status': ['a','r'],
                    'glyph': [['S']]
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
    ## Teal'c, Enemy of the Goa'uld
    '5943d410-e654-46a4-9bc7-44124d8ee891': {
        'onGetComplicationCost': [
            ('costChange', {
                'condition': {
                    'glyph': [['O']],
                    'status': "a"
                    },
                'value': "1"
                }),
            ('costChange', {
                'condition': {
                    'glyph': [['P']],
                    'status': "a"
                    },
                'value': "1"
                })
            ]
        },
    ## Transport Rings
    '57e5bbd8-c2f4-4333-8aad-9934807ba6bd': {
        'onAbility1Cost': [
            ('statusChange', {
                'target': 'self',
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
    ## Galaran Memory Device
    '4e5d26f3-522e-43b4-b560-012b81b27a01': {
        'onAbility1Cost': [
            ('statusChange', {
                'target': 'self',
                'condition': {
                    'status': ['r']
                    },
                'action': 'stop'
                }),
            ('discard', {
                'player': 'hero',
                'count': '1'
                })
            ],
        'onAbility1': [
            ('moveCard', {
                'target': {
                    'type': ['Team Character', 'Support Character', 'Event', 'Gear'],
                    'group': 'me.Discard'
                    },
                'to': ('me.Deck', 'shuffle'),
                'player': 'hero',
                'skippable': True,
                'count': "1"
                })
            ]
        },
    ## Salvage Technology
    'c81249ce-abc2-489c-a32c-28ca0e18293b': {
        'onSuccess': [
            ('moveCard', {
                'target': {
                    'type': ['Gear'],
                    'group': 'me.Deck'
                    },
                'to': ('me.hand', -1),
                'player': 'hero',
                'skippable': True,
                'count': "1"
                })
            ]
        },
    ## Ill-Gotten Gains
    'f8a88854-b6b8-4ccc-aa15-268d5539776c': {
        'onPlayCost': [
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
                'to': ('me.hand', -1),
                'player': 'hero',
                'count': "1"
                })
            ]
        },
    ## Zat Gun
    'a853c2fe-bd32-44fb-9794-5213d00dfe22': {
        'onAbility1Cost': [
            ('statusChange', {
                'target': 'self',
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
                    'hasSkill': 'Combat'
                    },
                'skill': ['all'],
                'value': '-1',
                'player': 'hero',
                'count': "1",
                'duration': "m",
                'ignoreSource': True
                })
            ],
        'onAbility2Cost': [
            ('statusChange', {
                'target': 'self',
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
                    'hasSkill': 'Combat'
                    },
                'player': 'hero',
                'count': "1",
                'tag': 'rf',
                'value': 'True',
                'ignoreSource': True
                })
            ],
        'onAbility3Cost': [
            ('statusChange', {
                'target': 'self',
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
                    'hasSkill': 'Combat',
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
        'onAbility1Cost': [
            ('statusChange', {
                'target': 'self',
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
    ## Cameron Mitchell, Eager Adventurer
    'da9a7837-a593-4269-acb6-d88449a0d07a': {
        'onGetStats': [
            ('skillChange', {
                'target': 'self',
                'condition': {
                    'glyph': [['O']]
                    },
                'skill': 'all',
                'value': "1 if storedCards[card._id]['s'] == 'a' and len(storedGameStats['sm']) == 0 and len(storedGameStats['fm']) == 0 else 0"
                })
            ]
        },
    ## Vala Mal Doran, Probationary Member of the SG
    '67af6d35-4256-40e4-9b75-bff404d6a234': {
        'onGetStats': [
            ('skillChange', {
                'target': 'self',
                'skill': 'all',
                'value': "1 if storedCards[card._id]['s'] == 'a' and Card(storedMission[0]).Glyph in [Card(g).Glyph for g in storedCards[card._id].get('g', [])] else 0"
                })
            ]
        },
    ## Balinsky, Insightful Archaeologist
    '0f8362dc-132b-4eb3-96ec-453afddd5638': {
        'onGetStats': [
            ('skillChange', {
                'target': 'self',
                'skill': 'all',
                'value': "1 if len(storedCards[card._id].get('g', [])) > len([c for c in storedCards if 'Obstacle' in Card(c).Type and storedCards[c]['s'] == 'a']) else 0"
                })
            ]
        },
    ## Daniel Jackson, Trained Fighter
    '77d8c4e5-1911-40f1-a0e8-08f01cc8d082': {
        'onGetStats': [
            ('skillChange', {
                'target': 'self',
                'condition': {
                    'glyph': [['G']],
                    },
                'skill': ['Combat'],
                'value': "2"
                }),
            ('skillChange', {
                'target': 'self',
                'condition': {
                    'glyph': [['T']],
                    },
                'skill': ['Combat'],
                'value': "1"
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
    ## Tight Rein
    '7bc7ab47-5fb6-40c5-b46b-91caf0ee6db0': {
        'onAssignCost': [
            ('statusChange', {
                'target': {
                    'status': ['a','r'],
                    'type': ['Team Character', 'Support Character']
                    },
                'trigger': {
                    'type': ['Team Character', 'Support Character'],
                    'status': ['r']
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
                    },
                'condition': {
                    'custom': 'len(storedCards[sourceId].get("g", [])) > 0'
                    },
                'player': 'villain',
                'value': '-1',
                })
            ]
        },
    ## Establish Communications
    'edee7ab2-f431-4c28-b808-d6fa1ed59cc2': {
        'onAssign': [
            ('discard', {
                'trigger': {
                    'cardName': "Jack O'Neill"
                    },
                'player': 'hero',
                'count': 'len(me.hand)',
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
    ## Out of Your Depth
    'b95f875a-0f2a-416a-bdc9-6b7aac41ffa8': {
        'onFailure': [
            ('moveCard', {
                'target': {
                    'type': ['Obstacle'],
                    'hasSkill': 'Science',
                    'group': 'me.Discard'
                    },
                'to': ('me.hand', -1),
                'player': 'enemy',
                'skippable': True,
                'count': "1"
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
    ## Conduct Repairs
    'b443d736-2f46-4176-94b4-6c18f57cdf84': {
        'onSuccess': [
            ('moveCard', {
                'target': {
                    'type': ['Gear'],
                    'group': 'me.Discard'
                    },
                'to': ('me.hand', -1),
                'player': 'hero',
                'skippable': True,
                'count': "1"
                })
            ]
        },
    ## Attend Trial
    '7cd9c3b2-a979-460a-ae6d-0fa1dbe1431b': {
        'onSuccess': [
            ('moveCard', {
                'target': {
                    'type': ['Support Character', 'Team Character'],
                    'group': 'me.Discard'
                    },
                'to': ('me.hand', -1),
                'player': 'hero',
                'skippable': True,
                'count': "1"
                })
            ]
        },
    ## Prevent Invasion
    'a4e3f614-51f0-4976-8ee5-ca96f3e0cf63': {
        'onPlayMission': [
            ('moveCard', {
                'target': {
                    'type': ['Obstacle'],
                    'group': 'me.Discard'
                    },
                'to': ('me.hand', -1),
                'player': 'villain',
                'skippable': True,
                'count': "1"
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
    ## Acquire Specimen
    'b73da326-be80-41c8-b201-a0e6d7bf2ec6': {
        'onGetStats': [
            ('skillChange', {
                'target': 'self',
                'skill': 'all',
                'value': "len([c for c in storedCards if storedCards[c]['s'] == 'a' and 'Obstacle' in Card(c).Type])"
                })
            ]
        },
    ## Infiltrate Summit
    'c0f58ccb-3278-4769-9040-31fec6b363ca': {
        'onGetStats': [
            ('skillChange', {
                'target': 'self',
                'skill': 'all',
                'value': "0 if len([c for c in storedCards if storedCards[c]['s'] == 'a' and 'Adversary' in Card(c).Type]) == 0 else 1"
                })
            ]
        },
    ## Survey Goa'uld Pleasure Palace
    'c4bf0315-ee48-4fd9-b02c-322f1b41e779': {
        'onGetStats': [
            ('skillChange', {
                'target': 'self',
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
    ## Offworld Research
    'ec0d04f8-07e6-489f-8705-68aafac29407': {
        'onGetStats': [
            ('skillChange', {
                'target': {
                    'type': ['Support Character'],
                    'status': ['a']
                    },
                'skill': ['Science'],
                'value': '1',
                'count': 'all',
                'duration': 'm'
                })
            ]
        },
    ## Pursue the Harcesis
    '1b4317d7-c293-46c2-aa30-87dae348e5c0': {
        'onGetStats': [
            ('skillChange', {
                'target': {
                    'cardName': ['Daniel Jackson']
                    },
                'skill': ['Culture'],
                'value': "len([c for c in storedCards if c != card._id and 'Team Character' in Card(c).Type and storedCards[c]['s'] == 'a'])",
                'player': 'all',
                'duration': 'm'
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
                'player': 'all'
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
    ## Fire Rain
    '8a097812-9963-4da7-ae55-0ff0196bfcff': {
        'onPlay': [
            ('statusChange', {
                'target': {
                    'type': ['Team Character', 'Support Character']
                    },
                'action': 'block',
                'player': 'villain',
                'count': "len([c for c in storedCards if 'Obstacle' in Card(c).Type and Card(c).name != card.name and storedCards[c]['s'] == 'a'])"
                })
            ]
        },
    ## Serpent Guards
    '7b84361c-da40-4a9a-8c2e-c4a327109f71': {
        'onGetPlayCost': [
            ('costChange', {
                'target': 'self',
                'condition': {
                    'custom': "len([c for c in storedCards if 'Team Character' in Card(c).Type and storedCards[c]['s'] == 'a' and len(storedCards[c].get('g',[])) == 0]) > 0"
                    },
                'value': "-1"
                })
            ]
        },
    ## Artok
    '87b224b8-8ae0-4081-aef3-5863b67bad26': {
        'onGetPlayCost': [
            ('costChange', {
                'target': 'self',
                'condition': {
                    'custom': "storedMission[1] == 'Combat'"
                    },
                'value': "-1"
                }),
            ('costChange', {
                'target': 'self',
                'condition': {
                    'custom': "len([c for c in storedCards if Card(c).isFaceUp == False and storedCards[c]['s'] == 'c']) >= 1"
                    },
                'value': "-1"
                })
            ]
        },
    ## Time Loop
    '9f7363f0-0281-46d1-906c-da6ebcb61d3d': {
        'onFailure': [
            ('ruleSet', {
                'rule': 'nnm',
                'value': 'True'
                })
            ]
        },
    ## Contact the Asgard
    '55047674-bacb-42d3-b9b7-ad515f27830c': {
        'onSuccess': [
            ('ruleSet', {
                'rule': 'nr',
                'value': 'True'
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
    ## Rescue Operative
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
                'target': 'stored',
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
                'target': 'self',
                'skill': 'all',
                'value': "len(storedGameStats['sm'])"
                })
            ]
        },
    ## Convert Jaffa
    '7ee0dd5e-05ab-4a8c-848f-52792b362509': {
        'onGetStats': [
            ('skillChange', {
                'target': 'self',
                'skill': 'all',
                'value': "1 if len(storedGameStats['sm']) == 0 else 0"
                })
            ]
        },
    ## Yu, the Great
    'dd59e9ee-9cf8-4d61-b891-5477c550b2b1': {
        'onGetStats': [
            ('skillChange', {
                'target': 'self',
                'skill': 'all',
                'value': "len(storedGameStats['sm'])"
                })
            ]
        },
    ## Robert Kinsey
    '13b58f59-4156-4d15-9c27-3212d8448b65': {
        'onGetStats': [
            ('skillChange', {
                'target': 'self',
                'skill': 'all',
                'value': "len([c for c in storedCards if storedCards[c]['s'] == 'a' and 'Obstacle' in Card(c).Type and 'Political' in Card(c).Traits]) + len(storedGameStats['fm'])"
                })
            ]
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
    scriptCards = []
    if me.hasInvertedTable():
        deck = oneil
    else:
        deck = jackson
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
    notify("{}: {}".format(me, scriptCards))
    if me.hasInvertedTable():
        registerTeam(me, None)
        remoteCall(players[1], "registerTeam", [players[1], None])



jackson = {
  'main': [
    (3, "a2076dc6-9eea-420d-8db2-d7b2fa94e3ab", "Troop Landing"),
    (3, "b5e4ff90-7a72-4696-a937-6542aef7af54", "Telekinetic Mutants"),
    (2, "7b84361c-da40-4a9a-8c2e-c4a327109f71", "Serpent Guards"),
    (2, "799a40e0-a9a9-4d4b-a548-b4a00bb004db", "Salish Spirits"),
    (2, "13b58f59-4156-4d15-9c27-3212d8448b65", "Robert Kinsey"),
    (3, "6783ab0b-9da4-4375-9580-14ffb6661cf5", "Parasitic Insects"),
    (2, "558106d3-ce22-43e1-92e8-8289723abc3a", "Loss of Funding"),
    (2, "b52fa628-3c10-44ce-829b-4f9241bf6949", "Harsh Conditions"),
    (3, "8a097812-9963-4da7-ae55-0ff0196bfcff", "Fire Rain"),
    (2, "2ecceca6-cd9d-4323-9aa4-6408626785b3", "Anubis"),
    (3, "87b224b8-8ae0-4081-aef3-5863b67bad26", "Artok"),
    (2, "2ecaf65d-1fe8-4cd7-8824-3160aef1d99b", "Bill Lee"),
    (2, "39b6a212-7c89-4327-ae56-ae9d49e9935e", "Dialing Computer"),
    (3, "cec32155-7eb9-4001-a923-1bf3b4ca0150", "Merrin"),
    (2, "db2e0e15-0970-4302-a434-d37c410d10f9", "Nicholas Ballard"),
    (3, "414ef0db-fe27-48c0-9e7a-9e13b346482b", "Seasoned Travelers"),
    (2, "57e5bbd8-c2f4-4333-8aad-9934807ba6bd", "Transport Rings"),
    (3, "a853c2fe-bd32-44fb-9794-5213d00dfe22", "Zat Gun")
  ],
  'team': [
    (1, "67af6d35-4256-40e4-9b75-bff404d6a234", "Vala Mal Doran"),
    (1, "77d8c4e5-1911-40f1-a0e8-08f01cc8d082", "Daniel Jackson"),
    (1, "0f8362dc-132b-4eb3-96ec-453afddd5638", "Balinsky"),
    (1, "da9a7837-a593-4269-acb6-d88449a0d07a", "Cameron Mitchell")
  ],
  'mission': [
    (1, "b73da326-be80-41c8-b201-a0e6d7bf2ec6", "Acquire Specimen"),
    (1, "7a3fddf6-79b3-4fbb-9974-f77169128116", "Avert Disaster"),
    (1, "b443d736-2f46-4176-94b4-6c18f57cdf84", "Conduct Repairs"),
    (1, "55047674-bacb-42d3-b9b7-ad515f27830c", "Contact the Asgard"),
    (1, "ca77df97-efc9-4db8-875a-1eadd08fb4a9", "Defeat Ashrak"),
    (1, "ec130081-a970-4640-90d6-23f86970f654", "Destroy Battleship "),
    (1, "ec0d04f8-07e6-489f-8705-68aafac29407", "Offworld Research"),
    (1, "a4e3f614-51f0-4976-8ee5-ca96f3e0cf63", "Prevent Invasion"),
    (1, "1b4317d7-c293-46c2-aa30-87dae348e5c0", "Pursue the Harcesis"),
    (1, "2bb7b341-26e1-495a-bd27-1635d81dcc5f", "Relocate Advanced Civilization"),
    (1, "3062cb52-5800-409d-b4a4-eb7f28f7dc27", "Rescue Operative"),
    (1, "de071fbb-e426-4bb2-8ed5-d40bd7f28e7c", "Seek Assistance")
  ]}

oneil = {
  'main': [
    (2, "39b6a212-7c89-4327-ae56-ae9d49e9935e", "Dialing Computer"),
    (2, "4e5d26f3-522e-43b4-b560-012b81b27a01", "Galaran Memory Device"),
    (2, "f8a88854-b6b8-4ccc-aa15-268d5539776c", "Ill-Gotten Gains"),
    (3, "cec32155-7eb9-4001-a923-1bf3b4ca0150", "Merrin"),
    (2, "5abf19d6-b076-4cfb-bcaf-dc90c573d687", "Naquadah Reactor"),
    (3, "db2e0e15-0970-4302-a434-d37c410d10f9", "Nicholas Ballard"),
    (3, "745bea32-98ed-49ac-9120-52965ab2716c", "Sense of Adventure"),
    (3, "33adafa3-d70e-46c9-9bd0-54ed1a1d77d7", "Special Training"),
    (2, "dd59e9ee-9cf8-4d61-b891-5477c550b2b1", "Yu"),
    (3, "a2076dc6-9eea-420d-8db2-d7b2fa94e3ab", "Troop Landing"),
    (3, "7bc7ab47-5fb6-40c5-b46b-91caf0ee6db0", "Tight Rein"),
    (3, "cbdd5fa9-138e-4e3e-ab51-552d1e3e675b", "Team Compromised"),
    (2, "b95f875a-0f2a-416a-bdc9-6b7aac41ffa8", "Out of Your Depth"),
    (2, "558106d3-ce22-43e1-92e8-8289723abc3a", "Loss of Funding"),
    (2, "b52fa628-3c10-44ce-829b-4f9241bf6949", "Harsh Conditions"),
    (3, "8a097812-9963-4da7-ae55-0ff0196bfcff", "Fire Rain"),
    (2, "2aebfd9e-d838-4542-846b-6861f2d6d369", "Brainwashing"),
    (2, "2ecceca6-cd9d-4323-9aa4-6408626785b3", "Anubis")
  ],
  'team': [
    (1, "4901fb59-e7cc-47d4-8f3a-4f1f2e93f78d", "Jack O'Neill"),
    (1, "c5358e72-16ac-450e-a2b8-923d4964f52c", "Harold Maybourne"),
    (1, "da9a7837-a593-4269-acb6-d88449a0d07a", "Cameron Mitchell"),
    (1, "5943d410-e654-46a4-9bc7-44124d8ee891", "Teal'c")
  ],
  'mission': [
    (1, "7cd9c3b2-a979-460a-ae6d-0fa1dbe1431b", "Attend Triad"),
    (1, "9f4d63c9-3b86-4f63-9d69-1232f3ca6122", "Beneath the Surface"),
    (1, "7ee0dd5e-05ab-4a8c-848f-52792b362509", "Convert Jaffa"),
    (1, "7b22ba1c-5432-4ec9-bfdb-66e49180dcae", "Destroy Minor Goa'uld"),
    (1, "edee7ab2-f431-4c28-b808-d6fa1ed59cc2", "Establish Communication"),
    (1, "c0f58ccb-3278-4769-9040-31fec6b363ca", "Infiltrate Summit"),
    (1, "db9b3230-07e2-400a-92b3-679ae3a7254d", "Pandemic Containment"),
    (1, "c81249ce-abc2-489c-a32c-28ca0e18293b", "Salvage Technology"),
    (1, "7f109410-f062-44b2-9a84-bf51d698d4e3", "Seek and Capture"),
    (1, "5fbb2f8b-9b01-41f2-ad7d-d5aba336bcef", "Supply Raid"),
    (1, "c4bf0315-ee48-4fd9-b02c-322f1b41e779", "Survey Goa'uld Pleasure Palace"),
    (1, "9f7363f0-0281-46d1-906c-da6ebcb61d3d", "Time Loop")
  ]}