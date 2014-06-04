#---------------------------------------------------------------------------
# Constants
#---------------------------------------------------------------------------
import re
import clr

clr.AddReference("System.Drawing")
clr.AddReference("System.Windows.Forms")

from System.Drawing import Point, Color, Font, FontStyle
from System.Windows.Forms import *

def printGUID(card, x = 0, y = 0, txt = ''):
    if card.model in scriptsDict:
        txt = " (Scripted)"
    whisper("{}~{}{}".format(card, card.model, txt))

def moveCardEvent(player, card, fromGroup, toGroup, oldIndex, index, oldX, oldY, x, y, isScriptMove, highlight = None, markers = {}):
    mute()
    if player != me:
        return
    if isScriptMove:
        return
    if fromGroup == table:
        card.moveToTable(oldX,oldY)
        card.setIndex(oldIndex)
    elif fromGroup == me.hand and toGroup == me.hand:
        return
    else:
        card.moveTo(fromGroup, oldIndex)
        notify("Overriding card movement...")

def registerTeam(player, groups):
    mute()
    #### Prep initial variables
    global storedTurnPlayer, storedPhase, storedVictory, storedOppVictory, storedMission
    storedTurnPlayer = getGlobalVariable("turnplayer")
    if storedTurnPlayer == "None":
        storedTurnPlayer = None
    else:
        storedTurnPlayer = Player(int(storedTurnPlayer))
    storedPhase = getGlobalVariable("phase")
    storedMission = eval(getGlobalVariable("activemission"))
    if player != me:  #only execute this event if its your own deck
        return
    #### The game only works with 2 players, so anyone else loading a deck will have their cards deleted
    if storedPhase not in ['pre.1reg', 'pre.2reg']:
        whisper("cannot load deck -- there are already 2 players registered.")
        for group in [me.Deck, me.piles['Mission Pile'], me.Team]:
            for c in group:
                c.delete()
        return
    #### Verify deck contents
    if len(me.Team) != 4:
        whisper("cannot load deck -- it does not have 4 team characters.")
        for group in [me.Deck, me.piles['Mission Pile'], me.Team]:
            for c in group:
                c.delete()
        return
    if len(me.piles['Mission Pile']) != 12:
        whisper("cannot load deck -- it does not have 12 missions.")
        for group in [me.Deck, me.piles['Mission Pile'], me.Team]:
            for c in group:
                c.delete()
        return
    #### Store victory points
    victory = 0
    teamlist = eval(getGlobalVariable("cards"))
    for card in me.Team:
        teamlist[card._id] = startingCard
        card.moveToTable(0,0)
        victory += int(card.Cost)  #add the card's cost to the victory total
    setGlobalVariable("cards", str(teamlist))
    me.setGlobalVariable("victory", str(victory)) #Stores your opponent's victory total
    storedVictory = int(getPlayers()[1].getGlobalVariable("victory"))
    storedOppVictory = int(me.getGlobalVariable("victory"))
    notify("{} registers their Team ({} points).".format(me, victory))
    me.Deck.shuffle()
    me.piles['Mission Pile'].shuffle()
    #### Determine who goes first
    if storedPhase == "pre.1reg":
        setGlobalVariable("phase", "pre.2reg")
    #### After the second player registers their deck, the starting player can be determined
    elif storedPhase == "pre.2reg":
        opponent = getPlayers()[1]
        if storedVictory > storedOppVictory:
            startingPlayer = me
            notify("{} will play first.".format(me))
        elif storedVictory < storedOppVictory:
            startingPlayer = opponent
            notify("{} will play first.".format(startingPlayer))
        elif storedVictory == storedOppVictory:  ##randomly determine in the event of a tie
            if rnd(1,2) == 1:
                startingPlayer = me
                notify("{} will play first, chosen randomly.".format(me))
            else:
                startingPlayer = opponent
                notify("{} will play first, chosen randomly.".format(opponent))
        if startingPlayer == me:
            setGlobalVariable("turnplayer", str(me._id))
            stopPlayer = opponent
        else:
            setGlobalVariable("turnplayer", str(startingPlayer._id))
            stopPlayer = me
        notify("{} will choose a team character to Stop.".format(stopPlayer))
        setGlobalVariable("priority", str((stopPlayer._id, False)))
        cleanup()
        setGlobalVariable("phase", "pre.stopchar")
    else:
        notify("An error has occured: phase variable should be pre.1reg or pre.2reg")
        return

def playerGlobalVarChanged(player, varName, oldValue, newValue):
    mute()
    if varName == "victory":
        if player != me:
            global storedVictory
            storedVictory = int(newValue)
            return
        else:
            global storedOppVictory
            storedOppVictory = int(newValue)
            return

def globalVarChanged(varName, oldValue, newValue):
    mute()
    #### update python global variables
    if varName == "turnplayer":
        global storedTurnPlayer
        storedTurnPlayer = Player(int(newValue))
        return
    if varName == "activemission":
        global storedMission
        storedMission = eval(newValue)
        return
    #### Phase Changes
    if varName == "phase":
        global storedPhase
        storedPhase = newValue
        #### First Player Mulligan
        if newValue == "pre.1mul":
            fillHand(8)
            if myTurn():
                if confirm("Do you want to draw a new hand?"):
                    for c in me.hand:
                        c.moveTo(me.Deck)
                    rnd(1,10)
                    me.Deck.shuffle()
                    rnd(1,10)
                    fillHand(8)
                    notify("{} draws a new hand.".format(me))
                else:
                    notify("{} keeps their hand.".format(me))
                setGlobalVariable("phase", "pre.2mul")
            return
        #### Second Player Mulligan
        if newValue == "pre.2mul":
            if not myTurn():
                if confirm("Do you want to draw a new hand?"):
                    for c in me.hand:
                        c.moveTo(me.Deck)
                    rnd(1,10)
                    me.Deck.shuffle()
                    rnd(1,10)
                    fillHand(8)
                    notify("{} draws a new hand.".format(me))
                else:
                    notify("{} keeps their hand.".format(me))
                turnPlayer().setActivePlayer()
                cleanup()
                notify(" ~~ {}'s Power Phase ~~ ".format(turnPlayer()))
                setGlobalVariable("phase", "pow.main")
            return
        #### Entering Power Phase
        if newValue == "pow.main":
            power = 3
            me.Power = power
            notify("{} gained {} power.".format(me, power))
            if not myTurn():
                setGlobalVariable("phase", "mis.start")
            return
        #### Setting up a new Mission
        if newValue == "mis.start":
            if myTurn():
                notify(" ~~ {}'s Mission Phase ~~ ".format(me))
                if storedMission != None:
                    notify("ERROR: There shouldn't be an active mission!")
                    return
                mission = me.piles['Mission Pile'].top()
                mission.moveToTable(0,0)
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
                    notify("ERROR: Mission has no skill types.")
                    return
                global storedMission
                storedMission = (mission._id, skilltype, skillvalue, "a")
                setGlobalVariable("activemission", str(storedMission))
                notify("{}'s current mission is {}.".format(me, mission))
                cardDict = eval(getGlobalVariable("cards"))
                cardDict[mission._id] = startingCard
                cardDict[mission._id]["s"] = "am"
                setGlobalVariable("cards", str(cardDict))
                ## Check for any card-specific scripts
                cardScripts = scriptsDict.get(mission.model, [])
                if 'onPlay' in cardScripts:
                    triggerScripts(mission, 'onPlay')
                cleanup()
                setGlobalVariable("priority", str((turnPlayer()._id, False)))
                setGlobalVariable("phase", "mis.main")
            return
        #### Resolving the current mission
        if newValue == "mis.res":
            if myTurn():
                if storedMission == None:
                    notify("ERROR: There is no registered active mission!")
                    return
                mission = Card(storedMission[0])
                type = storedMission[1]
                value = storedMission[2]
                status = storedMission[3]
                if mission not in table:
                    mission.moveToTable(0,0)
                cleanup()
                if mission.markers[markerTypes['skill']] >= mission.markers[markerTypes['diff']]:
                    missionOutcome = "success"
                else:
                    missionOutcome = "failure"
                notify("{} was a {}!".format(mission, missionOutcome))
                setGlobalVariable("activemission", str((mission._id, type, value, missionOutcome[0])))
                setGlobalVariable("phase", "mis.sucfail")
            return
        if newValue == "mis.sucfail":
            if myTurn():
                cardDict = eval(getGlobalVariable("cards"))
                if storedMission == None:
                    notify("ERROR: There is no registered active mission!")
                    return
                mission = Card(storedMission[0])
                status = "success" if storedMission[3] == "s" else "failure"
                cardQueue = eval(getGlobalVariable("cardqueue"))
                heroTriggers = []
                enemyTriggers = []
                ## add any success or failure triggers to the queue
                for c in cardDict:
                    card = Card(c)
                    if card in table and cardDict[c]["s"] == "a" and "on" + status.title() in scriptsDict.get(card.model, []):
                        if card.controller == me:
                            heroTriggers.append(c)
                        else:
                            enemyTriggers.append(c)
                if "on" + status.title() in scriptsDict.get(mission.model, []): ## Add the mission's trigger if it has one
                    heroTriggers.append(mission._id)
                newQueue = []
                if len(heroTriggers) > 0: ## attach hero triggers to queue
                    newQueue += [(None, 'game', "on" + status.title(), heroTriggers, len(heroTriggers), turnPlayer()._id)]
                if len(enemyTriggers) > 0: ## attach enemy triggers to queue
                    newQueue += [(None, 'game', "on" + status.title(), enemyTriggers, len(enemyTriggers), turnPlayer(False)._id)]
                if len(newQueue) == 0: ## skip all this junk if there's no actual triggers
                    setGlobalVariable("phase", "mis.adv")
                    return
                if len(heroTriggers) > 0:
                    notify("{} has {} triggers to resolve.".format(me, status))
                else:
                    notify("{} has {} triggers to resolve.".format(turnPlayer(False), status))
                setGlobalVariable("cardqueue", str(newQueue + cardQueue))
                cleanup()
            return
        if newValue == "mis.adv":
            if myTurn():
                if storedMission == None:
                    notify("ERROR: There is no registered active mission!")
                    return
                #### First, stop all hero characters assigned to the mission.
                cardDict = eval(getGlobalVariable("cards"))
                cardQueue = eval(getGlobalVariable("cardqueue"))
                triggers = []
                for c in cardDict:
                    card = Card(c)
                    if card in table and cardDict[c]["s"] == "a" and card.controller != me and card.Type == "Adversary": ## add assigned adversaries to the trigger list
                        triggers.append(c)
                    elif card in table and cardDict[c]["s"] == "a" and card.controller == me and card.Type in heroTypes: ## stops all assigned hero cards
                        cardDict[c]["s"] = "s"
                        cardDict[c]["p"] = True
                    elif card not in table:
                        notify("ERROR: {} in cardDict could not be found in table!".format(card))
                setGlobalVariable("cards", str(cardDict))
                if len(triggers) == 0:
                    ## skip all this junk
                    cleanup()
                    setGlobalVariable("phase", "mis.gly")
                    return
                notify("{} has adversaries to revive.".format(turnPlayer(False)))
                setGlobalVariable("cardqueue", str([(None, 'game', 'revive', triggers, len(triggers), turnPlayer(False)._id)] + cardQueue))
                cleanup()
            return
        if newValue == "mis.gly":
            #### Destroy all complications and obstacles
            if not myTurn():
                cardDict = eval(getGlobalVariable("cards"))
                for c in cardDict.keys():
                    card = Card(c)
                    if card not in table:
                        notify("ERROR: {} in cardDict could not be found in table!".format(card))
                    else:
                        if cardDict[c]["s"] == "c" and card.controller == me and card.isFaceUp == False:
                            card.moveTo(me.Discard)
                            del cardDict[c]
                        elif cardDict[c]["s"] == "a" and card.controller == me and card.Type == "Obstacle":
                            card.moveTo(me.Discard)
                            del cardDict[c]
                #### Check the mission's status and skip glyph step if it was a failure
                if storedMission == None:
                    notify("ERROR: There is no registered active mission!")
                    return
                mission = storedMission[0]
                status = storedMission[3]
                cardQueue = eval(getGlobalVariable("cardqueue"))
                triggers = []
                for c in cardDict.keys():
                    if "p" in cardDict[c]:
                        triggers.append(c)
                        del cardDict[c]["p"]
                #### Mission Failure
                if status == "f":
                    cardDict[mission]["s"] = "f"
                    setGlobalVariable("activemission", "None")
                    setGlobalVariable("cards", str(cardDict))
                    cleanup()
                    setGlobalVariable("phase", "mis.end")
                    return
                #### Mission Success (jumps to double-click)
                else:
                    notify("{} must choose a character to earn the glyph.".format(turnPlayer()))
                    setGlobalVariable("cardqueue", str([(None, 'game', 'glyph', triggers, 1, turnPlayer()._id)] + cardQueue))
                    setGlobalVariable("cards", str(cardDict))
                    cleanup()
                    return
            return
        if newValue == "mis.end":
            if myTurn():
                cardDict = eval(getGlobalVariable("cards"))
                failCount = sum(1 for x in cardDict if cardDict[x]["s"] == "f")
                if me.Power < failCount:
                    nextMission = False
                else:
                    nextMission = confirm("Would you like to continue to another mission?\n\n({} failed missions this turn.)".format(failCount))
                if nextMission:
                    me.Power -= failCount
                    turnPlayer(False).Power += failCount
                    setGlobalVariable("phase", "mis.start")
                else:
                    #### Skip to Debrief Phase
                    ## Ready all stopped characters
                    cardQueue = eval(getGlobalVariable("cardqueue"))
                    failedMissions = []
                    for c in cardDict.keys():
                        card = Card(c)
                        if cardDict[c]["s"] == "s":
                            cardDict[c]["s"] = "r"
                        elif cardDict[c]["s"] == "f":
                            failedMissions.append(c)
                    setGlobalVariable("cardqueue", str([(None, 'game', 'failMiss', failedMissions, len(failedMissions), turnPlayer()._id)] + cardQueue))
                    setGlobalVariable("cards", str(cardDict))
                    cleanup()
                    notify(" ~~ {}'s Debrief Phase ~~ ".format(me))
                    if len(failedMissions) == 0:
                        setGlobalVariable("phase", "deb.ref1")
                    else:
                        notify("{} has failed missions to return to their mission pile.".format(me))
                        setGlobalVariable("phase", "deb.start")
            return
        if newValue == "deb.ref1":
            if myTurn():
                handSize = len(me.hand)
                if handSize > 8:
                    notify("{} must discard {} cards, down to 8.".format(me, handSize - 8))
                    setGlobalVariable("priority", str((turnPlayer()._id, False)))
                else:
                    count = fillHand(8)
                    notify("{} refilled hand to 8, drawing {} cards.".format(me, count))
                    setGlobalVariable("priority", str((turnPlayer(False)._id, False)))
                    setGlobalVariable("phase", "deb.ref2")
            return
        if newValue == "deb.ref2":
            if not myTurn():
                handSize = len(me.hand)
                if handSize > 8:
                    notify("{} must discard {} cards, down to 8.".format(me, handSize - 8))
                    setGlobalVariable("priority", str((turnPlayer(False)._id, False)))
                else:
                    count = fillHand(8)
                    notify("{} refilled hand to 8, drawing {} cards.".format(me, count))
                    setGlobalVariable("phase", "deb.end")
            return
        if newValue == "deb.end":
            if myTurn():
                notify("{}'s turn ends.".format(me))
                nextPlayer = turnPlayer(False)
                nextPlayer.setActivePlayer()
                setGlobalVariable("turnplayer", str(nextPlayer._id))
                cleanup()
                notify(" ~~ {}'s Power Phase ~~ ".format(nextPlayer))
                setGlobalVariable("phase", "pow.main")

def doubleClick(card, mouseButton, keysDown):
    mute()
    if card not in table:
        return
    if not isActive(card):
        whisper("You cannot perform on an inactive card.")
        return
    global storedPhase
    phase = storedPhase
    cardQueue = eval(getGlobalVariable("cardqueue"))
    #### Card Queue Actions
    if cardQueue != []:
        (qCard, qTrigger, qType, qTargets, qCount, qPriority) = cardQueue[0]
        if Player(qPriority) != me: #### Skip if you don't have priority during the current card queue
            return
        if card._id not in qTargets:
            return #### Ignore cards that aren't in the target queue
        #### Deal with game engine triggers
        if qTrigger == 'game':
            cardDict = eval(getGlobalVariable("cards"))
            if card._id not in cardDict:
                notify("ERROR: {} doesn't exist in cardDict!".format(card))
                return
            #### Scoring/Reviving Adversaries
            if qType == "revive":
                if phase == "mis.adv" and card.controller == me and not myTurn():
                    #### Get status of mission to choose the correct action for the adversary
                    if storedMission == None:
                        notify("ERROR: There is no registered active mission!")
                        return
                    status = storedMission[3]
                    choiceMap = {1:"Score", 2:"Revive", 3:"Destroy"}
                    if len(me.Deck) < int(card.Revive): ## Remove the Revive option if you can't pay revive cost
                        choiceMap[2] = "Destroy"
                        del choiceMap[3]
                    if status == "s": ##Remove the Score option if the mission was a success
                        choiceMap[1] = choiceMap[2]
                        if choiceMap[2] == "Revive":
                            choiceMap[2] == choiceMap[3]
                            del choiceMap[3]
                        else:
                            del choiceMap[2]
                    elif status != "f":  ## Covers cases where the activeMission var is messed up
                        return
                    choiceList = sorted(choiceMap.values(), key=lambda x:x[1])
                    choiceResult = askChoice("Choose an action for {}".format(card.name), choiceList, [])
                    if choiceResult == 0:
                        return
                    else:
                        choiceResult = choiceMap[choiceResult]
                    #### Apply the action to the adversary
                    if choiceResult == "Score": ## Score
                        del cardDict[card._id]
                        card.moveTo(card.owner.piles["Villain Score Pile"])
                        scriptTrigger = "onScore"
                    elif choiceResult == "Revive": ## Revive
                        for c in me.Deck.top(int(card.Revive)): ## discard cards from top of deck to pay revive cost
                            c.moveTo(me.Discard)
                        cardDict[card._id]['s'] = 's' ## stops the adversary
                        scriptTrigger = "onRevive"
                    else: ## destroy
                        del cardDict[card._id]
                        card.moveTo(card.owner.Discard)
                        scriptTrigger = "onDestroy"
                    qTargets.remove(card._id)
                    qCount -= 1
                    setGlobalVariable("cards", str(cardDict))
                    if qCount == 0 or len(qTargets) == 0:
                        del cardQueue[0]
                    else:
                        cardQueue[0] = (qCard, qTrigger, qType, qTargets, qCount, qPriority)
                    setGlobalVariable("cardqueue", str(cardQueue))
                    if scriptTrigger in scriptsDict.get(card.model, []):
                        triggerScripts(card, scriptTrigger)
                    if len(eval(getGlobalVariable("cardqueue"))) == 0: #### no more triggers to resolve, it's safe to proceed to the next phase
                        setGlobalVariable("priority", str((turnPlayer()._id, False)))
                        cleanup()
                        setGlobalVariable("phase", "mis.gly")
                    else:
                        cleanup()
                return
            #### Success/Failure ability triggers
            if qType in ['onSuccess', 'onFailure']:
                if phase == "mis.sucfail" and card.controller == me:
                    qTargets.remove(card._id)
                    qCount -= 1
                    if qCount == 0 or len(qTargets) == 0:
                        del cardQueue[0]
                    else:
                        cardQueue[0] = (qCard, qTrigger, qType, qTargets, qCount, qPriority)
                    setGlobalVariable("cardqueue", str(cardQueue))
                    if qType in scriptsDict.get(card.model, []):
                        triggerScripts(card, qType)
                    if len(eval(getGlobalVariable("cardqueue"))) == 0: #### no more triggers to resolve, it's safe to proceed to the next phase
                        setGlobalVariable("priority", str((turnPlayer()._id, False)))
                        cleanup()
                        setGlobalVariable("phase", "mis.adv")
                    else:
                        cleanup()
                return
            #### Earning Glyphs
            if qType == 'glyph':
                if phase == "mis.gly" and card.controller == me and card.Type in ["Team Character", "Support Character"] and myTurn():
                    if storedMission == None:
                        notify("ERROR: There is no registered active mission!")
                        return
                    mission = storedMission[0]
                    cardDict[card._id]["g"].append(mission)  ## Add the glyph to the chosen character
                    cardDict[mission]["s"] = "g"  ## Sets the mission's status as an earned glyph
                    notify("{} earns the glyph ({}.)".format(card, Card(mission)))
                    del cardQueue[0]
                    setGlobalVariable("cardqueue", str(cardQueue))  ## Clears the card queue
                    setGlobalVariable("cards", str(cardDict))  ## Updates cardDict
                    setGlobalVariable("activemission", "None")  ## Empties the active mission
                    cleanup()
                    setGlobalVariable("phase", "mis.end")
                return
            #### Put failed missions to the bottom of pile
            if qType == 'failMiss':
                if phase == "deb.start" and myTurn():
                    qTargets.remove(card._id)
                    qCount -= 1
                    del cardDict[card._id]
                    card.moveToBottom(me.piles["Mission Pile"])
                    if qCount == 0 or len(qTargets) == 0:
                        del cardQueue[0]
                        setGlobalVariable("cardqueue", str(cardQueue))
                        setGlobalVariable("cards", str(cardDict))
                        cleanup()
                        setGlobalVariable("phase", "deb.ref1")
                    else:
                        cardQueue[0] = (qCard, qTrigger, qType, qTargets, qCount, qPriority)
                        setGlobalVariable("cardqueue", str(cardQueue))
                        setGlobalVariable("cards", str(cardDict))
                        cleanup()
                return
        #### Card Scripting Functions
        else:
            sourceCard = Card(qCard)
            qAction, scripts = scriptsDict[sourceCard.model][qTrigger][int(qType)]
            #### status changes
            if qAction == "statusChange":
                cardDict = eval(getGlobalVariable("cards"))
                action = scripts["action"]
                if action == "store":
                    if "st" in cardDict[qCard]:
                        cardDict[qCard]["st"] += [card._id]
                    else:
                        cardDict[qCard]["st"] = [card_id]
                elif action == "stop":
                    cardDict[card._id]["s"] = "s"
                elif action == "block":
                    cardDict[card._id]["s"] = "b"
                    if "b" in cardDict[qCard]:
                        cardDict[qCard]["b"] += [card._id]
                    else:
                        cardDict[qCard]["b"] = [card._id]
                elif action == "ready":
                    cardDict[card._id]["s"] = "r"
                elif action == "assign":
                    cardDict[card._id]["s"] = "a"
                elif action == "incapacitate":
                    cardDict[card._id]["s"] = "i"
                elif action == "destroy":
                    card.moveTo(card.owner.Discard)
                    del cardDict[card._id]
                else:
                    whisper("ERROR: action {} not found!".format(action))
                    return
                if qCount > 1:
                    qCount -= 1
                    cardQueue[0] = (qCard, qTrigger, qType, qTargets, qCount, qPriority)
                else:
                    del cardQueue[0]
                setGlobalVariable("cardqueue", str(cardQueue))
                setGlobalVariable("cards", str(cardDict))
            ## When the queue finally empties, some specific phases need to be passed since they get skipped normally
            if cardQueue == [] or len(cardQueue) == 0:  ## only trigger when the queue is empty
                if storedPhase == "mis.sucfail":
                    setGlobalVariable("priority", str((turnPlayer()._id, False)))
                    cleanup()
                    setGlobalVariable("phase", "mis.adv")
                    return
                if storedPhase == "mis.adv": ## shift from revive adversaries to assign glyphs
                    setGlobalVariable("priority", str((turnPlayer()._id, False)))
                    cleanup()
                    setGlobalVariable("phase", "mis.gly")
                    return
                cleanup()
            else:
                cleanup()
            return
        return
#### Phase-specific Doubleclick Actions
    if not myPriority():  ## You need priority to use doubleClick
        whisper("Cannot perform action on {}: You don't have priority.".format(card))
        return
    #### general assigning character to the mission
    if phase == "mis.main":
        if card.Type not in ['Adversary', 'Team Character', 'Support Character']:
            whisper("Cannot assign {}: It is not an assignable card type.".format(card))
            return
        if storedMission == None:
            whisper("Cannot assign {} as there is no active mission.".format(card))
            return
        mission = storedMission[0]
        type = storedMission[1]
        value = storedMission[2]
        status = storedMission[3]
        cardDict = eval(getGlobalVariable("cards"))
        cardSkill = getStats(card, cardDict)[type] ## grab the card's skill value of the active mission
        if cardSkill == None:
            whisper("Cannot assign {}: Does not match the active mission's {} skill.".format(card, type))
            return
        if card._id in cardDict:
            if cardDict[card._id]["s"] != "r":
                whisper("Cannot assign: {} is not Ready.".format(card))
                return
            cardDict[card._id]["s"] = "a"
            setGlobalVariable("cards", str(cardDict))
            if 'onAssign' in scriptsDict.get(card.model, []):
                triggerScripts(card, 'onAssign')
            cleanup()
            notify("{} assigns {}.".format(me, card))
            setGlobalVariable("priority", str((getPlayers()[1]._id, False)))
        else:
            notify("ERROR: {} not in cards global dictionary.".format(card))
        return
    #### Enemy player must stop a character at the start of the game
    if phase == "pre.stopchar":
        if not myTurn():
            cardDict = eval(getGlobalVariable("cards"))
            if card._id not in cardDict:
                notify("ERROR: {} doesn't exist in cardDict!".format(card))
                return
            cardDict[card._id]["s"] = "s"
            setGlobalVariable("cards", str(cardDict))
            notify("{} Stops {}.".format(me, card))
            setGlobalVariable("phase", "pre.1mul")
        return


def myPriority():
    if Player(eval(getGlobalVariable("priority"))[0]) == me:
        return True
    else:
        return False

def isActive(card):
    if myTurn():
        if card.isFaceUp == False:
            if card.controller == me:
                return False
            else:
                return True
        if card.Type in heroTypes or card.Type == "Mission":
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
        if card.isFaceUp == False:
            if card.controller == me:
                return True
            else:
                return False
        if card.Type in heroTypes or card.Type == "Mission":
            if card.controller == me:
                return False
            else:
                return True
        else:
            if card.controller == me:
                return True
            else:
                return False

def turnPlayer(var = True):
    global storedTurnPlayer
    if storedTurnPlayer == None:
        hero = Player(int(getGlobalVariable("turnplayer")))
    else:
        hero = storedTurnPlayer
    if var == False:
        for p in getPlayers():
            if p != hero:
                return p
    else:
        return hero

def myTurn():
    if turnPlayer() == me:
        return True
    else:
        return False

def fillHand(maxHand):
    mute()
    count = 0
    while len(me.hand) < maxHand:
        if len(me.Deck) == 0: break
        me.Deck[0].moveTo(me.hand)
        count += 1
    return count

def getStats(card, cardDict):
    mute()
    baseSkills = {'Culture': None, 'Science': None, 'Combat': None, 'Ingenuity': None}
    ## Set the base skill from the printed card
    for baseSkill in baseSkills.keys():
        if card.properties[baseSkill] != "":
            baseSkills[baseSkill] = int(card.properties[baseSkill])
    ## Apply static skill changes from card abilities
    cardScripts = scriptsDict.get(card.model, {})
    for skillChange in cardScripts.get('skillChange', []):
        skill = skillChange['skill']
        value = eval(skillChange['value'])
        if skill == 'all': ## Special case for abilities that boost all skills equally, and are listed as 'skills' or 'difficulty'
            for baseSkill in baseSkills.keys():
                if baseSkills[baseSkill]: ## Only apply the skill change if the character has the skill, skip otherwise
                    baseSkills[baseSkill] += value
        else:
            for baseSkill in skill:
                if baseSkills[baseSkill]: ## add value to existing skill
                    baseSkills[baseSkill] += value
                else: ## Add the skill if the card doesn't already have a base for it
                    baseSkills[baseSkill] = value
    return baseSkills

def passturn(group, x = 0, y = 0):
    mute()
    phase = getGlobalVariable("phase")
    if phase == "mis.main":
        priority = eval(getGlobalVariable("priority"))
        if Player(priority[0]) != me:
            whisper("Cannot pass turn: You don't have priority.")
            return
        cardQueue = eval(getGlobalVariable("cardqueue"))
        if len(cardQueue) > 0:
            whisper("Cannot pass priority: There are abilities that need resolving.")
            return
        if priority[1] == False:
            notify("{} passes.".format(me))
            cleanup()
            setGlobalVariable("priority", str((getPlayers()[1]._id, True)))
        else:
            notify("{} passes, enters Mission Resolution.".format(me))
            setGlobalVariable("priority", str((turnPlayer()._id, False)))
            setGlobalVariable("phase", "mis.res")

def playcard(card, x = 0, y = 0):
    mute()
    global storedPhase
    phase = storedPhase
    if not myPriority():
        whisper("Cannot choose {}: You don't have priority.".format(card))
        return
    #### Normal playing card
    if phase == "mis.main":
        if not isActive(card):
            whisper("You cannot play {} during your {}turn.".format(card, "" if myTurn() else "opponent's "))
            return
        if me.Power < int(card.Cost):
            whisper("You do not have enough Power to play that.")
            return
        cardQueue = eval(getGlobalVariable("cardqueue"))
        if len(cardQueue) > 0:
            whisper("Cannot play {}: There are abilities that need resolving.".format(card))
            return
        if card.Type == "Obstacle":
            if storedMission == None:
                whisper("Cannot play {} as there is no active mission.".format(card))
                return
            missionSkill = storedMission[1]
            if card.properties[missionSkill] == None or card.properties[missionSkill] == "":
                whisper("Cannot play {}: Does not match the active mission's {} skill.".format(card, missionSkill))
                return
            status = "a" #assigned
        else:
            status = "r" #ready
        cardDict = eval(getGlobalVariable("cards"))
        cardCost = int(card.Cost)
        cardScripts = scriptsDict.get(card.model, [])
        if "costChange" in cardScripts:
            for script in cardScripts["costChange"]:
                if eval(script["condition"]): ## If the condition is met
                    cardCost += script["value"]
        me.Power -= cardCost
        if card.Type == "Event":
            card.moveTo(card.owner.Discard)
        else:
            cardDict[card._id] = startingCard
            cardDict[card._id]["s"] = status
            setGlobalVariable("cards", str(cardDict))
            card.moveToTable(0,0)
        notify("{} plays {}.".format(me, card))
        ## Check for any card-specific scripts
        if 'onPlay' in cardScripts:
            triggerScripts(card, 'onPlay')
        cleanup()
        setGlobalVariable("priority", str((getPlayers()[1]._id, False)))
        return
    #### Discarding to max hand size at debrief
    if phase == "deb.ref1":
        if myTurn():
            card.moveTo(card.owner.Discard)
            notify("{} discards {}.".format(me, card))
            if len(me.hand) <= 8:
                setGlobalVariable("priority", str((turnPlayer(False)._id, False)))
                setGlobalVariable("phase", "deb.ref2")
        return
    if phase == "deb.ref2":
        if not myTurn():
            card.moveTo(card.owner.Discard)
            notify("{} discards {}.".format(me, card))
            if len(me.hand) <= 8:
                setGlobalVariable("phase", "deb.end")
        return

def triggerScripts(card, type): ## note this function assumes that the card scripts exist, doesn't do any verifying
    mute()
    cardScripts = scriptsDict[card.model][type]
    cardDict = eval(getGlobalVariable("cards"))
    queue = []
    scriptIndex = 0
    for (actionType, params) in cardScripts:
        if actionType == 'powerChange':
            if params['player'] == 'hero':
                player = turnPlayer()._id
            else:
                player = turnPlayer(False)._id
            powerNum = eval(params['value'])
            if player.Power + powerNum < 0: ## if the player doesn't have enough power to pay
                player.Power = 0
            else:
                player.Power += powerNum
        if actionType == 'statusChange':
            statusCheck = params.get("status", [])
            if params["target"] == "stored":
               targets == cardDict[card._id]["st"]
            else:
                targets = [c for c in cardDict
                    if isActive(Card(c))
                    and params['target'] in Card(c).Type
                    and (statusCheck == [] or cardDict[c]["s"] in statusCheck)
                    ]
            if params['choice'] == "all": ## These affect all targets, no queue used
                action = params["action"]
                for target in targets:
                    if action == "store":
                        if "st" in cardDict[card._id]:
                            cardDict[card._id]["st"] += [target]
                        else:
                            cardDict[card._id]["st"] = [target]
                    elif action == "stop":
                        cardDict[target]["s"] = "s"
                    elif action == "block":
                        cardDict[target]["s"] = "b"
                        if "b" in cardDict[qCard]:
                            cardDict[qCard]["b"] += [card._id]
                        else:
                            cardDict[qCard]["b"] = [card._id]
                    elif action == "ready":
                        cardDict[target]["s"] = "r"
                    elif action == "assign":
                        cardDict[target]["s"] = "a"
                    elif action == "incapacitate":
                        cardDict[target]["s"] = "i"
                    elif action == "destroy":
                        Card(target).moveTo(Card(target).owner.Discard)
                        del cardDict[target]
                    else:
                        whisper("ERROR: action {} not found!".format(action))
                setGlobalVariable("cards", str(cardDict))
                cleanup()
                return
            targetCount = eval(params['count'])
            if len(targets) == 0 or targetCount <= 0: ## Skip this loop if there are no legal targets to choose
                continue
            if params['choice'] == "hero":
                player = turnPlayer()._id
            else:
                player = turnPlayer(False)._id
            queue.append((card._id, type, scriptIndex, targets, targetCount, player))
        scriptIndex += 1
    if queue != []: ## Only update cardqueue if there are changes to be made
        cardQueue = eval(getGlobalVariable("cardqueue"))
        setGlobalVariable("cardqueue", str(queue + cardQueue))

def cleanup(remote = False):
    mute()
    if turnPlayer().hasInvertedTable():
        invert = True
    else:
        invert = False
    missionSkill, missionDiff, failcount, compcount, glyphwin, expwin, villwin = (0, 0, 0, 0, 0, 0, 0)
    alignvars = {'a': 0, 'r': 0, 's': 0, 'va': 0, 'vr': 0, 'vs': 0}
    cardDict = eval(getGlobalVariable("cards"))
    cardQueue = eval(getGlobalVariable("cardqueue"))
    if len(cardQueue) > 0 and len(cardQueue[0]) > 0:
        actionQueue = cardQueue[0][3]
        if cardQueue[0][5] == turnPlayer()._id:
            actionColor = HeroActionColor
        elif cardQueue[0][5] == turnPlayer(False)._id:
            actionColor = EnemyActionColor
        else:
            actionColor = None
    else:
        actionQueue = []
    if storedMission != None:
        mission = Card(storedMission[0])
        type = storedMission[1]
        value = storedMission[2]
        status = storedMission[3]
    #### Scan the table for cards that shouldn't belong there
    for card in table:
        if card._id not in cardDict and card != mission:
            notify("ERROR: {}'s {} did not enter play properly.".format(card.controller, card))
    #### Start aligning the cards on the table
    for c in cardDict:
        card = Card(c)
        status = cardDict[c]["s"]
        if card.controller == me:
            if card not in table: ## If for some reason the card is no longer on the table, move it back
                if status == 'c':
                    card.moveToTable(0,0, True)
                else:
                    card.moveToTable(0,0)
            if c in actionQueue:  ## add highlight for cards in the action queue
                if card.highlight != actionColor:
                    card.highlight = actionColor
            else:
                if card.highlight != None:
                    card.highlight = None
        if status == "am": ## skip general alignment of the active mission
            continue
        if isActive(card):
            if card.controller == me:
                if status == 'c' and card.isFaceUp == True: ## fix face-up complications
                    card.isFaceUp = False
                if status != 'c' and card.isFaceUp == False: ## fix face-down cards that are supposed to be face-up
                    card.isFaceUp = True
                if status in ['b', 'i', 'g']:  ## rotate all cards that are blocked, incapacitated, or glyphs
                    if card.orientation != Rot90:
                        card.orientation = Rot90
                else:
                    if card.orientation != Rot0:
                        card.orientation = Rot0
            if status == "g": ## Skip direct alignment of earned glyphs
                for marker in card.markers:
                    if card.markers[marker] > 0:
                        card.markers[marker] = 0
                continue                
            #### Prep Failed Missions
            if status == 'f' and card.Type == 'Mission':
                xpos = (-79 if invert else -101) - 20 * failcount
                ypos = (-145 - 10 * failcount) if invert else (60 + 10 * failcount)
                failcount += 1
                if card.controller == me and card.position != (xpos, ypos):
                    card.moveToTable(xpos, ypos)
                for marker in card.markers:
                    if card.markers[marker] > 0:
                        card.markers[marker] = 0
            #### Prep Complications
            elif status == 'c':
                xpos = (-79 if invert else -81) - 20 * compcount
                ypos = (70 + 10 * compcount) if invert else (-155 - 10 * compcount)
                compcount += 1
                missionDiff += 1
                if card.controller == me and card.position != (xpos, ypos):
                    card.moveToTable(xpos, ypos)
            else:
                cardSkills = getStats(card, cardDict)
                #### Prep Hero cards
                if card.Type in heroTypes:
                    if status == "a":
                        countType = "a"
                        ypos = -98 if invert else 10
                        if storedMission != None and cardSkills[type] != "":
                            missionSkill += cardSkills[type]
                    elif status == "r" or status == "b":
                        countType = "r"
                        ypos = -207 if invert else 119
                    else:
                        countType = "s"
                        ypos = -316 if invert else 228
                #### Prep Enemy Cards
                elif card.Type in enemyTypes:
                    if status == "a":
                        countType = "va"
                        ypos = 10 if invert else -98
                        if storedMission != None and cardSkills[type] != "":
                            missionDiff += cardSkills[type]
                    elif status == "r" or status == "b":
                        countType = "vr"
                        ypos = 119 if invert else -207
                    else:
                        countType = "vs"
                        ypos = 228 if invert else -316
                xpos = alignvars[countType]
                if card.orientation == Rot90:
                    alignvars[countType] += 95
                else:
                    alignvars[countType] += 70
                #### Align the card
                if card.controller == me:
                    glyphs = cardDict[c]["g"]
                    glyphLen = len(glyphs)
                    if invert == True:
                        xpos += glyphLen*14
                        if glyphLen > 0:
                            xpos += 11
                        if card.orientation == Rot90:
                           xpos += 25
                    if card.position != (xpos, ypos):
                        card.moveToTable(xpos, ypos)
                    ## Align earned glyphs
                    if glyphLen > 0:
                        glyphCount = 0
                        if card.orientation == Rot90:
                            glyphCount += 25  ## takes into account the character being incapacitated or blocked
                        for glyphID in glyphs:
                            glyph = Card(glyphID)
                            expwin += int(glyph.experience)
                            glyphwin += 1
                            glyph.moveToTable(xpos + glyphCount*(-1 if invert else 1), ypos)
                            glyph.sendToBack()
                            glyphCount += 14
                            alignvars[countType] += glyphCount + 11  ## takes into account the last glyph being rotated for aligning the next character
                    if invert:
                        alignvars[countType] = xpos + 70
                #### Add skill markers on the card to show its current values
                if card.controller == me and card.Type != "Mission":
                    if card.isFaceUp:
                        for cardSkill in cardSkills:
                            skillValue = cardSkills[cardSkill]
                            if skillValue:
                                if card.markers[markerTypes[cardSkill]] != skillValue:
                                    card.markers[markerTypes[cardSkill]] = skillValue
        #### Align inactive cards
        else:
            if card.controller == me and card.position != (-197, -44):
                card.moveToTable(-197, -44)
                if card.orientation != Rot0:
                    card.orientation = Rot0
            #### Remove all markers from inactive cards
            for marker in card.markers:
                if card.markers[marker] > 0:
                    card.markers[marker] = 0
    #### Align the active mission
    if storedMission != None:
        if myTurn():
            mission.moveToTable(-81 if invert else -105, -45 if invert else -44)
            if mission.orientation != Rot90:
                mission.orientation = Rot90
            missionDiff += value
            mission.markers[markerTypes['skill']] = missionSkill
            mission.markers[markerTypes['diff']] = missionDiff
    #### Determine victory conditions
    me.counters["Glyph Win"].value = glyphwin
    if glyphwin >= 7:
        notify("{} has won through Glyph Victory (7 glyphs.)".format(me))
        #### GLYPHWIN
    me.counters["Experience Win"].value = expwin
    if expwin >= storedVictory:
        notify("{} has won through Experience Victory ({} points.)".format(me, expwin))
    for villain in me.piles["Villain Score Pile"]:
        villwin += int(villain.cost)
    me.counters["Villain Win"].value = villwin
    if villwin >= storedVictory:
        notify("{} has won through Villain Victory ({} points.)".format(me, villwin))
    if remote == False: ## We don't want to trigger a loop
        remoteCall(getPlayers()[1], "cleanup", [True])




def playComplication(card, x = 0, y = 0):
    mute()
    if myTurn():
        whisper("Cannot play {} as the Hero player.".format(card))
        return
    global storedPhase
    phase = storedPhase
    if phase != "mis.main":
        whisper("Cannot play {}: It's not the main mission phase.".format(card))
        return
    if not myPriority():
        whisper("Cannot play {}: You don't have priority.".format(card))
        return
    cardQueue = eval(getGlobalVariable("cardqueue"))
    if len(cardQueue) > 0:
        whisper("Cannot play {}: There are abilities that need resolving.".format(card))
        return
    carddict = eval(getGlobalVariable("cards"))
    cost = 1 + sum(1 for c in carddict if carddict[c]['s'] == 'c') ##count the number of complications in play
    if me.Power < cost:
        whisper("You do not have enough Power to play that as a complication.")
        return
    carddict[card._id] = {"m": { }, "t": { }, "s": "c"}
    setGlobalVariable("cards", str(carddict))
    card.moveToTable(0,0, True)
    card.peek()
    me.Power -= cost
    notify("{} plays a complication.".format(me))
    cleanup()
    setGlobalVariable("priority", str((turnPlayer()._id, False)))

def assign(card, x = 0, y = 0):
    mute()
    if not isActive(card):
        whisper("You cannot play {} during your {}turn.".format(card, "" if myTurn() else "opponent's "))
        return
    if card.Type not in ['Adversary', 'Team Character', 'Support Character']:
        whisper("Cannot assign {}: It is not an assignable card type.".format(card))
        return
    global storedPhase
    phase = storedPhase
    if phase != "mis.main":
        whisper("Cannot assign {}: It's not the main mission phase.".format(card))
        return
    if not myPriority():
        whisper("Cannot assign {}: You don't have priority.".format(card))
        return
    if storedMission == None:
        whisper("Cannot assign {} as there is no active mission.".format(card))
        return
    cardQueue = eval(getGlobalVariable("cardqueue"))
    if len(cardQueue) > 0:
        whisper("Cannot assign {}: There are abilities that need resolving.".format(card))
        return
    mission, type, value, status = storedMission
    if card.properties[type] == None or card.properties[type] == "":
        whisper("Cannot assign {}: Does not match the active mission's {} skill.".format(card, type))
        return
    carddict = eval(getGlobalVariable("cards"))
    if card._id in carddict:
        if carddict[card._id]["s"] != "r":
            whisper("Cannot assign: {} is not Ready.".format(card))
            return
        carddict[card._id]["s"] = "a"
        setGlobalVariable("cards", str(carddict))
        cleanup()
        setGlobalVariable("priority", str((turnPlayer(False)._id, False)))
        notify("{} assigns {}.".format(me, card))
    else:
        notify("ERROR: {} not in cards global dictionary.".format(card))

def defaultaction(card, x = 0, y = 0):
    mute()

def checkScripts(card, actionType):
    mute()
    if card.name in scriptsDict:
        cardScripts = scriptsDict[card.name]
        if actionType in cardScripts:
            script = cardScripts[actionType]
            
    return None

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
    cardDict = eval(getGlobalVariable("cards"))
    cardDict[card._id]["s"] = "r"
    setGlobalVariable("cards", str(cardDict))
    cleanup()
    notify("{} readies {}.".format(me, card))

def block(card, x = 0, y = 0):
    mute()
    cardDict = eval(getGlobalVariable("cards"))
    cardDict[card._id]["s"] = "b"
    setGlobalVariable("cards", str(cardDict))
    cleanup()
    notify("{} blocks {} from the quest.".format(me, card))

def stop(card, x = 0, y = 0):
    mute()
    cardDict = eval(getGlobalVariable("cards"))
    cardDict[card._id]["s"] = "s"
    setGlobalVariable("cards", str(cardDict))
    cleanup()
    notify("{} stops {}.".format(me, card))

def incapacitate(card, x = 0, y = 0):
    mute()
    cardDict = eval(getGlobalVariable("cards"))
    cardDict[card._id]["s"] = "i"
    setGlobalVariable("cards", str(cardDict))
    cleanup()
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