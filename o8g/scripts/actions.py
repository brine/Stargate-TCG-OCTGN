#---------------------------------------------------------------------------
# Constants
#---------------------------------------------------------------------------
import re

AssignColor = "#ff0000"
BlockColor = "#ffff00"
KOColor = "#ffffff"
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

heroTypes = ["Support Character", "Team Character", "Gear", "Event"]
enemyTypes = ["Obstacle", "Adversary"]

def registerTeam(player, groups):
    mute()
    if player != me:  #only execute this event if its your own deck
        return
    phase = getGlobalVariable("phase")
    #### The game only works with 2 players, so anyone else loading a deck will have their cards deleted
    if phase not in ['pre.1reg', 'pre.2reg']:
        whisper("cannot load deck -- there are already 2 players registered.")
        for group in [me.Deck, me.piles['Mission Pile'], me.Team]:
            for c in group:
                c.delete()
        return
    #### Verify deck contents
    if len(me.Team) != 4:
        notify("{}'s team does not have 4 members! Please restart game and load a legal deck.".format(me))
        return
    #### Store victory points
    victory = 0
    teamlist = eval(getGlobalVariable("cards"))
    for card in me.Team:
        teamlist[card._id] = {"mission": { }, "turn": { }, "status": "ready"}
        card.moveToTable(0,0)
        victory += int(card.Cost)  #add the card's cost to the victory total
    setGlobalVariable("cards", str(teamlist))
    me.setGlobalVariable("victory", str(victory)) #Stores your victory total
    notify("{} registers their Team ({} points).".format(me, victory))
    me.Deck.shuffle()
    me.piles['Mission Pile'].shuffle()
    #### Determine who goes first
    if phase == "pre.1reg":
        setGlobalVariable("phase", "pre.2reg")
    #### After the second player registers their deck, the starting player can be determined
    elif phase == "pre.2reg":
        oppVictory = int(me.getGlobalVariable("victory"))
        meVictory = int(players[1].getGlobalVariable("victory"))
        if meVictory > oppVictory:
            setGlobalVariable("turnplayer", str(me._id))
            notify("{} will play first.".format(me))
        elif meVictory < oppVictory:
            setGlobalVariable("turnplayer", str(players[1]._id))
            notify("{} will play first.".format(players[1]))
        elif meVictory == oppVictory:  ##randomly determine in the event of a tie
            rng = rnd(1,2)
            if rng == 1:
                startingPlayer = me
                notify("{} will play first, chosen randomly.".format(me))
            else:
                startingPlayer = players[1]
                notify("{} will play first, chosen randomly.".format(players[1]))
        if startingPlayer == me:
             stopPlayer = players[1]
        else:
             stopPlayer = me
        notify("{} will choose a team character to Stop.".format(stopPlayer))
        cleanup()
        remoteCall(players[1], "cleanup", [])
        setGlobalVariable("turnplayer", str(startingPlayer._id))
        setGlobalVariable("phase", "pre.stopchar")
    else:
        notify("An error has occured: phase variable should be pre.1reg or pre.2reg")
        return

def doubleClick(card, mouseButton, keysDown):
    mute()
    phase = getGlobalVariable("phase")
    if phase == "pre.stopchar":
        #### Enemy player must stop a character at the start of the game
        if not myTurn():
            notify("6")
            cardsDict = eval(getGlobalVariable("cards"))
            if card._id not in cardsDict:
                notify("ERROR: {} doesn't exist in the cardsDict!".format(card))
                return
            cardsDict[card._id]["status"] = "stop"
            setGlobalVariable("cards", str(cardsDict))
            notify("{} Stops {}.".format(me, card))
            setGlobalVariable("phase", "pre.1mul")
            return

def globalVarChanged(varName, oldValue, newValue):
    mute()
    #### Phase Changes
    if varName == "phase":
        #### First Mulligan
        if newValue == "pre.1mul":
            fillHand(me)
            if myTurn():
                if confirm("Do you want to draw a new hand?"):
                    for c in me.hand:
                        c.moveTo(me.Deck)
                    rnd(1,10)
                    me.Deck.shuffle()
                    rnd(1,10)
                    fillHand(me)
                    notify("{} draws a new hand.".format(me))
                else:
                    notify("{} does not draw a new hand.".format(me))
                setGlobalVariable("phase", "pre.2mul")
            return
        #### Second Mulligan
        if newValue == "pre.2mul":
            if not myTurn():
                if confirm("Do you want to draw a new hand?"):
                    for c in me.hand:
                        c.moveTo(me.Deck)
                    rnd(1,10)
                    me.Deck.shuffle()
                    rnd(1,10)
                    fillHand(me)
                    notify("{} draws a new hand.".format(me))
                else:
                    notify("{} does not draw a new hand.".format(me))
                cleanup()
                remoteCall(players[1], "cleanup", [])
                setGlobalVariable("phase", "pow.main")
            return
        #### Resolving the current mission
        if newValue == "mis.res":
            activemission = getGlobalVariable("activemission")
            if activemission == "None":
                notify("ERROR: There is no registered active mission!")
                return
            mission, type, value = eval(activemission)
            mission = Card(mission)
            if mission not in table:
                mission.moveToTable(0,0)
            cleanup()
            remoteCall(players[1], "cleanup", [])
            if mission.markers[markerTypes['skill']] >= mission.markers[markerTypes['diff']]:
                notify("{} was a success!".format(mission))
                ###MISSION SUCCESS
                return
            else:
                notify("{} was a failure!".format(mission))
                ###MISSION FAIL
                return
            return
        #### Entering Power Phase
        if newValue == "pow.main":
            power = 3
            me.Power = power
            notify("{} gained {} power.".format(me, power))
            if myTurn():
                setGlobalVariable("phase", "mis.start")
            return
        #### Setting up a new Mission
        if newValue == "mis.start":
            if myTurn():
                if getGlobalVariable("activemission") != "None":
                    notify("ERROR: There shouldn't be an active mission!")
                    return
                mission = me.piles['Mission Pile'].top()
                mission.moveToTable(0,0)
                mission.orientation = Rot90
                if mission.Culture != "":
                    skilltype = "Culture"
                    skillvalue = int(mission.Culture)
                elif mission.Science != "":
                    skilltype = "Science"
                    skillvalue = int(mission.Science)
                elif mission.Combat != "":
                    skilltype = "Combat"
                    skillvalue = int(mission.combat)
                elif mission.Ingenuity != "":
                    skilltype = "Ingenuity"
                    skillvalue = int(mission.Ingenuity)
                else:
                    notify("ERROR: Mission has no skill types")
                    return
                tuple = (mission._id, skilltype, skillvalue)
                setGlobalVariable("activemission", str(tuple))
                cleanup()
                remoteCall(players[1], "cleanup", [])
                setGlobalVariable("priority", str(me._id))
                setGlobalVariable("phase", "mis.main")
            return

def myTurn():
    player = int(getGlobalVariable("turnplayer"))
    if me._id == player:
        return True
    else:
        return False

def isActive(card):
    if myTurn():
        if card.Type in heroTypes:
            if card.controller == me:
                return True
            else:
                return False
        else:
            if card.controller == me:
                return False
            else:
                return True
    else:
        if card.Type in heroTypes:
            if card.controller == me:
                return False
            else:
                return True
        else:
            if card.controller == me:
                return True
            else:
                return False

def turnPlayer():
    return Player(int(getGlobalVariable("turnplayer")))

def fillHand(p):
    mute()
    count = 0
    handsize = len(p.hand)
    while len(p.hand) < 8:
        if len(p.Deck) == 0: break
        p.Deck[0].moveTo(p.hand)
        count = count + 1
    return count, handsize
    #notify("{} refilled hand to {}, drawing {} cards.".format(me, count, handsize))

def passturn(group, x = 0, y = 0):
    mute()
    phase = getGlobalVariable('phase')
    if phase == "mis.main":
        priority = Player(int(getGlobalVariable("priority")))
        if priority != me:
            whisper("Cannot pass: You don't have priority.")
            return
        passcheck = getGlobalVariable("pass")
        if passcheck == "False":
            notify("{} passes.".format(me))
            cleanup()
            remoteCall(players[1], "cleanup", [])
            setGlobalVariable("pass", "True")
            setGlobalVariable("priority", str(players[1]._id))
        else:
            notify("{} passes, enters Mission Resolution.".format(me))
            setGlobalVariable("pass", "False")
            setGlobalVariable("phase", "mis.res")
            setGlobalVariable("priority", str(turnPlayer()._id))

def cleanup():
    mute()
    if turnPlayer().hasInvertedTable():
        invert = True
    else:
        invert = False
    skill, diff, assigncount, readycount, stopcount, vassigncount, vreadycount, vstopcount = (0, 0, 0, 0, 0, 0, 0, 0)
    cardDict = eval(getGlobalVariable("cards"))
    activeMission = getGlobalVariable("activemission")
    if activeMission != "None":
        mission, type, value = eval(activeMission)
    #### Scan the table for cards that shouldn't belong there
    for card in table:
        if card._id not in cardDict:
            notify("ERROR: {}'s {} did not enter play properly.".format(card.controller, card))
    #### Start aligning the cards on the table
    for c in cardDict:
        card = Card(c)
        if card not in table: ## If for some reason the card is no longer on the table, move it back
            card.moveToTable(0,0)
        if card.Type != "Mission":
            if isActive(card):
                if card.Type in heroTypes:
                    if cardDict[card._id]["status"] == "assign":
                        xpos = assigncount
                        ypos = -98 if invert else 10
                        assigncount = assigncount + 1
                        if activeMission != "None":
                            if card.Type in heroTypes and card.properties[type] != "":
                                skill = skill + int(card.properties[type])
                            elif card.Type in enemyTypes and card.properties[type] != "":
                                diff = diff + int(card.properties[type])
                    elif cardDict[card._id]["status"] == "ready":
                        xpos = readycount
                        ypos = -207 if invert else 119
                        readycount = readycount + 1
                    else:
                        xpos = stopcount
                        ypos = -316 if invert else 228
                        stopcount = stopcount + 1
                else:
                    if cardDict[card._id]["status"] == "assign":
                        xpos = vassigncount
                        ypos = 10 if invert else -98
                        vassigncount = vassigncount + 1
                        if activeMission != "None":
                            if card.Type in heroTypes and card.properties[type] != "":
                                skill = skill + int(card.properties[type])
                            elif card.Type in enemyTypes and card.properties[type] != "":
                                diff = diff + int(card.properties[type])
                    elif cardDict[card._id]["status"] == "ready":
                        xpos = vreadycount
                        ypos = 119 if invert else -207
                        vreadycount = vreadycount + 1
                    else:
                        xpos = vstopcount
                        ypos = 228 if invert else -316
                        vstopcount = vstopcount + 1
                if card.controller == me:
                    card.moveToTable(70*xpos, ypos)
            else:
                if card.controller == me:
                    card.moveToTable(-197, -44)
            #### Add skill markers on the card to show its current values
            if card.Culture != "":
                card.markers[markerTypes['Culture']] = int(card.Culture)
            if card.Science != "":
                card.markers[markerTypes['Science']] = int(card.Science)
            if card.Combat != "":
                card.markers[markerTypes['Combat']] = int(card.Combat)
            if card.Ingenuity != "":
                card.markers[markerTypes['Ingenuity']] = int(card.Ingenuity)
    #### Align the active mission
    if activeMission != "None":
        if myTurn():
            mission = Card(mission)
            mission.moveToTable(-81 if invert else -105, -45 if invert else -44)
            diff = diff + value
            mission.markers[markerTypes['skill']] = skill
            mission.markers[markerTypes['diff']] = diff
    #### Highlight cards in your hand that you can play
    for card in me.hand:
        if card.Cost <= me.Power and isActive(card):
            card.highlight = PlayColor
        else:
            card.highlight = None

def playcard(card, x = 0, y = 0):
    mute()
    phase = getGlobalVariable("phase")
    if phase != "mis.main":
        whisper("Cannot play {}: It's not the main mission phase.".format(card))
        return
    priority = Player(int(getGlobalVariable("priority")))
    if priority != me:
        whisper("Cannot play {}: You don't have priority.".format(card))
        return
    if not isActive(card):
        whisper("You cannot play {} during your {}turn.".format(card, "" if myTurn() else "opponent's "))
        return
    if me.Power < card.Cost:
        whisper("You do not have enough Power to play that.")
        return
    if card.Type == "Obstacle":
        activemission = getGlobalVariable("activemission")
        if activemission == "None":
            whisper("Cannot play {} as there is no active mission.".format(card))
            return
        mission, type, value = eval(activemission)
        if card.properties[type] == None or card.properties[type] == "":
            whisper("Cannot play {}: Does not match the active mission's {} skill.".format(card, type))
            return
        status = "assign"
    else:
        status = "ready"
    carddict = eval(getGlobalVariable("cards"))
    carddict[card._id] = {"mission": { }, "turn": { }, "status": status}
    me.Power -= card.Cost
    card.moveToTable(0,0)
    notify("{} plays {}.".format(me, card))
    setGlobalVariable("cards", str(carddict))
    ## Check for any card-specific scripts
    result = checkScripts(card, 'play')
    cleanup()
    remoteCall(players[1], "cleanup", [])
    setGlobalVariable("priority", str(players[1]._id))

def checkScripts(card, actionType):
    mute()
    if card.name in scriptDict:
        cardScripts = scriptDict[card.name]
        if actionType in cardScripts:
            script = cardScripts[actionType]
            
    return None

def assign(card, x = 0, y = 0):
    mute()
    phase = getGlobalVariable("phase")
    if phase != "mis.main":
        whisper("Cannot assign {}: It's not the main mission phase.".format(card))
        return
    priority = Player(int(getGlobalVariable("priority")))
    if priority != me:
        whisper("Cannot assign {}: You don't have priority.".format(card))
        return
    activemission = getGlobalVariable("activemission")
    if activemission == "None":
        whisper("Cannot assign {} as there is no active mission.".format(card))
        return
    mission, type, value = eval(activemission)
    if card.properties[type] == None or card.properties[type] == "":
        whisper("Cannot assign {}: Does not match the active mission's {} skill.".format(card, type))
        return
    carddict = eval(getGlobalVariable("cards"))
    if card._id in carddict:
        carddict[card._id]["status"] = "assign"
        setGlobalVariable("cards", str(carddict))
        cleanup()
        remoteCall(players[1], "cleanup", [])
        setGlobalVariable("priority", str(players[1]._id))
        notify("{} assigns {}.".format(me, card))
    else:
        notify("ERROR: {} not in cards global dictionary.".format(card))

#---------------------------------------------------------------------------
# Scripting Functions
#---------------------------------------------------------------------------

def scriptDestroy(card):
    mute()
    

#---------------------------------------------------------------------------
# Table group actions
#---------------------------------------------------------------------------

def endquest(group, x = 0, y = 0):
    mute()
    myCards = (card for card in table
        if card.controller == me)
    for card in myCards:
        card.highlight = None
        card.markers[markerTypes['block']] = 0
    notify("{} is ending the quest.".format(me))

def endturn(group, x = 0, y = 0):
    mute()
    myCards = (card for card in table
        if card.controller == me)
    for card in myCards:
        card.markers[markerTypes['stop']] = 0
        card.markers[markerTypes['block']] = 0
        card.highlight = None
        if card.orientation == rot180:
          card.orientation = rot90
          card.markers[markerTypes['stop']] = 1
        else:
          card.orientation = rot0
    notify("{} ends their turn.".format(me))

def clearAll(group, x = 0, y = 0):
    notify("{} clears all targets and combat.".format(me))
    for card in group:
      card.target(False)
      if card.controller == me and card.highlight in [AttackColor, BlockColor]:
          card.highlight = None

def roll20(group, x = 0, y = 0):
    mute()
    n = rnd(1, 20)
    notify("{} rolls {} on a 20-sided die.".format(me, n))

def flipCoin(group, x = 0, y = 0):
    mute()
    n = rnd(1, 2)
    if n == 1:
        notify("{} flips heads.".format(me))
    else:
        notify("{} flips tails.".format(me))

#---------------------------------------------------------------------------
# Table card actions
#---------------------------------------------------------------------------

def ready(card, x = 0, y = 0):
    mute()
    card.highlight = None
    card.markers[markerTypes['stop']] = 0
    card.markers[markerTypes['block']] = 0
    card.orientation = Rot0
    notify("{} readies {}.".format(me, card))

def block(card, x = 0, y = 0):
    mute()
    card.highlight = None
    card.markers[markerTypes['stop']] = 0
    card.markers[markerTypes['block']] = 1
    notify("{} blocks {} from the quest.".format(me, card))

def stop(card, x = 0, y = 0):
    mute()
    card.highlight = None
    card.markers[markerTypes['stop']] = 1
    card.markers[markerTypes['block']] = 0
    card.orientation = Rot90
    notify("{} stops {}.".format(me, card))

def incapacitate(card, x = 0, y = 0):
    mute()
    card.highlight = KOColor
    card.markers[markerTypes['stop']] = 0
    card.markers[markerTypes['block']] = 0
    card.orientation = Rot180
    notify("{} KO's {}.".format(me, card))

def destroy(card, x = 0, y = 0):
    mute()
    src = card.group
    card.moveTo(me.Discard)
    if src == table:
      notify("{} destroys {}.".format(me, card))
    else:
      notify("{} discards {} from their {}.".format(me, card, src.name))

def flip(card, x = 0, y = 0):
    mute()
    if card.isFaceUp:
        notify("{} flips {} face down.".format(me, card))
        card.isFaceUp = False
    else:
        card.isFaceUp = True
        notify("{} morphs {} face up.".format(me, card))

def addMarker(card, x = 0, y = 0):
    mute()
    notify("{} adds a counter to {}.".format(me, card))
    card.markers[markerTypes['counter']] += 1

def removeMarker(card, x = 0, y = 0):
    mute()
    addmarker = markerTypes['counter']
    if addmarker in card.markers:
      card.markers[addmarker] -= 1
      markername = addmarker[0]
      notify("{} removes a counter from {}".format(me, card))

#---------------------------------------------------------------------------
# Group Actions
#---------------------------------------------------------------------------

def randomDiscard(group, x = 0, y = 0):
    mute()
    card = group.random()
    if card == None: return
    notify("{} randomly discards a card.".format(me))
    card.moveTo(me.Discard)

def draw(group, x = 0, y = 0):
    if len(group) == 0: return
    mute()
    group[0].moveTo(me.hand)
    notify("{} draws a card.".format(me))

def refill(group, x = 0, y = 0):
    if len(group) == 0: return
    mute()
    count = len(me.hand)
    count2 = 8 - count
    for c in group.top(count2): c.moveTo(me.hand)
    notify("{} refills hand, drawing {} cards.".format(me, count2))

def shuffle(group, x = 0, y = 0):
    group.shuffle()