
ActionColor = "#ff0000" #red
BlockColor = "#ffff00" #yellow
KOColor = "#ffffff" #black
PlayColor = "#0000ff" #green

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

heroTypes = ["Support Character", "Team Character", "Gear", "Event", "Mission"]
enemyTypes = ["Obstacle", "Adversary"]
startingCard = { 'm':{ }, 't':{ }, 's':'r', 'g':[ ] }

storedTurnPlayer = None
storedPhase = None
storedMission = None
storedVictory = 0
storedOppVictory = 0

scriptsDict = {
        }

def createDecks():
    mute()
    if me.hasInvertedTable():
        deck = oneil
    else:
        deck = jackson
    for c in deck['main']:
        qty, guid, name = c
        me.Deck.create(guid, qty)
    for c in deck['team']:
        qty, guid, name = c
        me.Team.create(guid, qty)
    for c in deck['mission']:
        qty, guid, name = c
        me.piles['Mission Pile'].create(guid, qty)
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