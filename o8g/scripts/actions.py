#---------------------------------------------------------------------------
# Constants
#---------------------------------------------------------------------------
import re
import clr

clr.AddReference("System.Drawing")
clr.AddReference("System.Windows.Forms")

from System.Drawing import Point, Color, Font, FontStyle
from System.Windows.Forms import *

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
    storedVictory = int(players[1].getGlobalVariable("victory"))
    storedOppVictory = int(me.getGlobalVariable("victory"))
    notify("{} registers their Team ({} points).".format(me, victory))
    me.Deck.shuffle()
    me.piles['Mission Pile'].shuffle()
    #### Determine who goes first
    if storedPhase == "pre.1reg":
        setGlobalVariable("phase", "pre.2reg")
    #### After the second player registers their deck, the starting player can be determined
    elif storedPhase == "pre.2reg":
        if storedVictory > storedOppVictory:
            startingPlayer = me
            notify("{} will play first.".format(me))
        elif storedVictory < storedOppVictory:
            startingPlayer = players[1]
            notify("{} will play first.".format(players[1]))
        elif storedVictory == storedOppVictory:  ##randomly determine in the event of a tie
            if rnd(1,2) == 1:
                startingPlayer = me
                notify("{} will play first, chosen randomly.".format(me))
            else:
                startingPlayer = players[1]
                notify("{} will play first, chosen randomly.".format(players[1]))
        if startingPlayer == me:
            setGlobalVariable("turnplayer", str(me._id))
            stopPlayer = players[1]
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
                    notify("ERROR: Mission has no skill types.")
                    return
                missionVars = (mission._id, skilltype, skillvalue, "a")
                setGlobalVariable("activemission", str(missionVars))
                global storedMission
                storedMission = missionVars
                notify("{}'s current mission is {}.".format(me, mission))
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
                status = storedMission[3]
                triggers = []
                priority = False
                for c in cardDict:
                    card = Card(c)
                    if card in table and cardDict[c]["s"] == "a" and scriptsDict.get(card.model) == status:
                        triggers.append(c)
                        if card.controller == me:
                            priority = True
                if scriptsDict.get(mission.model):
                    triggers.append(mission._id)
                if len(triggers) == 0:
                    ## skip all this junk
                    setGlobalVariable("phase", "mis.adv")
                    return
                setGlobalVariable("cardqueue", str(triggers))
                if priority:
                    notify("{} has {} triggers to resolve.".format(me, status))
                    setGlobalVariable("priority", str((me._id, False)))
                else:
                    notify("{} has {} triggers to resolve.".format(players[1], status))
                    setGlobalVariable("priority", str((players[1]._id, False)))
                cleanup()
            return
        if newValue == "mis.adv":
            if myTurn():
                if storedMission == None:
                    notify("ERROR: There is no registered active mission!")
                    return
                #### First, stop all hero characters assigned to the mission.
                cardDict = eval(getGlobalVariable("cards"))
                triggers = []
                for c in cardDict:
                    card = Card(c)
                    if card in table and cardDict[c]["s"] == "a" and card.controller != me and card.Type == "Adversary":
                        triggers.append(c)
                    elif card in table and cardDict[c]["s"] == "a" and card.controller == me and card.Type in heroTypes:
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
                notify("{} has adversaries to revive.".format(players[1]))
                setGlobalVariable("cardqueue", str(triggers))
                setGlobalVariable("priority", str((players[1]._id, False)))
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
                triggers = []
                for c in cardDict.keys():
                    if "p" in cardDict[c]:
                        triggers.append(c)
                        del cardDict[c]["p"]
                #### Mission Failure
                if status == "f":
                    cardDict[mission] = startingCard
                    cardDict[mission]["s"] = "f"
                    setGlobalVariable("activemission", "None")
                    setGlobalVariable("cards", str(cardDict))
                    cleanup()
                    setGlobalVariable("phase", "mis.end")
                    return
                #### Mission Success (jumps to double-click)
                else:
                    notify("{} must choose a character to earn the glyph.".format(turnPlayer()))
                    setGlobalVariable("cardqueue", str(triggers))
                    setGlobalVariable("cards", str(cardDict))
                    cleanup()
                    setGlobalVariable("priority", str((turnPlayer()._id, False)))
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
                    players[1].Power += failCount
                    setGlobalVariable("phase", "mis.start")
                else:
                    #### Skip to Debrief Phase
                    ## Ready all stopped characters
                    failedMissions = []
                    for c in cardDict.keys():
                        card = Card(c)
                        if cardDict[c]["s"] == "s":
                            cardDict[c]["s"] = "r"
                        elif cardDict[c]["s"] == "f":
                            failedMissions.append(c)
                    setGlobalVariable("cardqueue", str(failedMissions))
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
                    setGlobalVariable("phase", "deb.ref2")
                    setGlobalVariable("priority", str((players[1]._id, False)))
            return
        if newValue == "deb.ref2":
            if not myTurn():
                handSize = len(me.hand)
                if handSize > 8:
                    notify("{} must discard {} cards, down to 8.".format(me, handSize - 8))
                    setGlobalVariable("priority", str((players[1]._id, False)))
                else:
                    count = fillHand(8)
                    notify("{} refilled hand to 8, drawing {} cards.".format(me, count))
                    setGlobalVariable("phase", "deb.end")
            return
        if newValue == "deb.end":
            if myTurn():
                notify("{}'s turn ends.".format(me))
                players[1].setActivePlayer()
                setGlobalVariable("turnplayer", str(players[1]._id))
                cleanup()
                notify(" ~~ {}'s Power Phase ~~ ".format(players[1]))
                setGlobalVariable("phase", "pow.main")

def doubleClick(card, mouseButton, keysDown):
    mute()
    if card not in table:
        return
    if not myPriority():  ## You need priority to use doubleClick
        whisper("Cannot perform action on {}: You don't have priority.".format(card))
        return
    if not isActive(card):
        whisper("You cannot assign an inactive card.")
        return
    global storedPhase
    phase = storedPhase
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
            setGlobalVariable("priority", str((players[1]._id, False)))
            notify("{} assigns {}.".format(me, card))
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
    #### Scoring/Reviving Adversaries
    if phase == "mis.adv":
        if card.controller == me and card.Type == "Adversary" and not myTurn():
            cardQueue = eval(getGlobalVariable("cardqueue"))
            if card._id not in cardQueue:
                return
            cardDict = eval(getGlobalVariable("cards"))
            if card._id not in cardDict:
                notify("ERROR: {} doesn't exist in cardDict!".format(card))
                return
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
            elif choiceResult == "Revive": ## Revive
                for c in me.Deck.top(int(card.Revive)): ## discard cards from top of deck to pay revive cost
                    c.moveTo(me.Discard)
                cardDict[card._id]['s'] = 's' ## stops the adversary
            else: ## destroy
                del cardDict[card._id]
                card.moveTo(card.owner.Discard)
            cardQueue.remove(card._id)
            setGlobalVariable("cardqueue", str(cardQueue))
            setGlobalVariable("cards", str(cardDict))
            if len(cardQueue) == 0:
                setGlobalVariable("priority", str((turnPlayer()._id, False)))
                setGlobalVariable("phase", "mis.gly")
            cleanup()
        return
    #### Earning Glyphs
    if phase == "mis.gly":
        if myTurn() and card.controller == me and card.Type in ["Team Character", "Support Character"]:
            cardQueue = eval(getGlobalVariable("cardqueue"))
            if card._id not in cardQueue:  ## reject any card not queued as accepting the glyph
                return
            cardDict = eval(getGlobalVariable("cards"))
            if card._id not in cardDict:
                notify("ERROR: {} doesn't exist in cardDict!".format(card))
                return
            if storedMission == None:
                notify("ERROR: There is no registered active mission!")
                return
            mission = storedMission[0]
            cardDict[card._id]["g"].append(mission)  ## Add the glyph to the chosen character
            cardDict[mission] = startingCard  ## Adds the mission to cardDict
            cardDict[mission]["s"] = "g"  ## Sets the mission's status as an earned glyph
            notify("{} earns the glyph ({}.)".format(card, Card(mission)))
            setGlobalVariable("cardqueue", "[]")  ## Clears the card queue
            setGlobalVariable("cards", str(cardDict))  ## Updates cardDict
            setGlobalVariable("activemission", "None")  ## Empties the active mission
            cleanup()
            setGlobalVariable("phase", "mis.end")
        return
    if phase == "deb.start":
        if myTurn():
            failedMissions = eval(getGlobalVariable("cardqueue"))
            cardDict = eval(getGlobalVariable("cards"))
            if card._id in failedMissions:
                failedMissions.remove(card._id)
                del cardDict[card._id]
                card.moveToBottom(me.piles["Mission Pile"])
                setGlobalVariable("cardqueue", str(failedMissions))
                setGlobalVariable("cards", str(cardDict))
                cleanup()
                if len(failedMissions) == 0:
                    setGlobalVariable("phase", "deb.ref1")
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
        if card.isFaceUp == False:
            if card.controller == me:
                return True
            else:
                return False
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
    global storedTurnPlayer
    if storedTurnPlayer == None:
        return Player(int(getGlobalVariable("turnplayer")))
    else:
        return storedTurnPlayer

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

def passturn(group, x = 0, y = 0):
    mute()
    phase = getGlobalVariable('phase')
    if phase == "mis.main":
        priority = eval(getGlobalVariable("priority"))
        if Player(priority[0]) != me:
            whisper("Cannot pass turn: You don't have priority.")
            return
        if priority[1] == False:
            notify("{} passes.".format(me))
            cleanup()
            setGlobalVariable("priority", str((players[1]._id, True)))
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
        if card.Type == "Obstacle":
            if storedMission == None:
                whisper("Cannot play {} as there is no active mission.".format(card))
                return
            type = storedMission[1]
            if card.properties[type] == None or card.properties[type] == "":
                whisper("Cannot play {}: Does not match the active mission's {} skill.".format(card, type))
                return
            status = "a" #assigned
        else:
            status = "r" #ready
        carddict = eval(getGlobalVariable("cards"))
        carddict[card._id] = startingCard
        carddict[card._id]["s"] = status
        me.Power -= int(card.Cost)
        if card.Type == "Event":
            card.moveTo(card.owner.Discard)
        else:
            setGlobalVariable("cards", str(carddict))
            card.moveToTable(0,0)
        notify("{} plays {}.".format(me, card))
        ## Check for any card-specific scripts
    ##    result = checkScripts(card, 'play')
        cleanup()
        setGlobalVariable("priority", str((players[1]._id, False)))
        return
    #### Discarding to max hand size at debrief
    if phase == "deb.ref1":
        if myTurn():
            card.moveTo(card.owner.Discard)
            notify("{} discards {}.".format(me, card))
            if len(me.hand) <= 8:
                setGlobalVariable("phase", "deb.ref2")
        return
    if phase == "deb.ref2":
        if not myTurn():
            card.moveTo(card.owner.Discard)
            notify("{} discards {}.".format(me, card))
            if len(me.hand) <= 8:
                setGlobalVariable("phase", "deb.end")
        return

def cleanup(remote = False):
    mute()
    if turnPlayer().hasInvertedTable():
        invert = True
    else:
        invert = False
    skill, diff, failcount, compcount, glyphwin, expwin, villwin = (0, 0, 0, 0, 0, 0, 0)
    alignvars = {'a': 0, 'r': 0, 's': 0, 'va': 0, 'vr': 0, 'vs': 0}
    cardDict = eval(getGlobalVariable("cards"))
    cardQueue = eval(getGlobalVariable("cardqueue"))
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
            if status == 'c' and card.isFaceUp == True: ## fix face-up complications
                card.isFaceUp = False
            if status != 'c' and card.isFaceUp == False: ## fix face-down cards that are supposed to be face-up
                card.isFaceUp = True
            if card._id in cardQueue:  ## add highlight for cards in the action queue
                if card.highlight != ActionColor:
                    card.highlight = ActionColor
            else:
                if card.highlight != None:
                    card.highlight = None
            if status in ['b', 'i', 'g']:  ## rotate all cards that are blocked, incapacitated, or glyphs
                if card.orientation != Rot90:
                    card.orientation = Rot90
            else:
                if card.orientation != Rot0:
                    card.orientation = Rot0
        if status == "g": ## Skip direct alignment of earned glyphs
            continue 
        if isActive(card):
            if status == 'f' and card.Type == 'Mission':
                xpos = (-79 if invert else -101) - 20 * failcount
                ypos = (-145 - 10 * failcount) if invert else (60 + 10 * failcount)
                failcount += 1
                if card.controller == me and card.position != (xpos, ypos):
                    card.moveToTable(xpos, ypos)
            elif status == 'c': ##deal with complications
                xpos = (-79 if invert else -81) - 20 * compcount
                ypos = (70 + 10 * compcount) if invert else (-155 - 10 * compcount)
                compcount += 1
                diff += 1
                if card.controller == me and card.position != (xpos, ypos):
                    card.moveToTable(xpos, ypos)
            else:
                if card.Type in heroTypes:
                    if status == "a":
                        countType = "a"
                        ypos = -98 if invert else 10
                        if storedMission != None and card.properties[type] != "":
                            skill += int(card.properties[type])
                    elif status == "r" or status == "b":
                        countType = "r"
                        ypos = -207 if invert else 119
                    else:
                        countType = "s"
                        ypos = -316 if invert else 228
                elif card.Type in enemyTypes:
                    if status == "a":
                        countType = "va"
                        ypos = 10 if invert else -98
                        if storedMission != None and card.properties[type] != "":
                            diff += int(card.properties[type])
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
        else:
            if card.controller == me and card.position != (-197, -44):
                card.moveToTable(-197, -44)
        #### Add skill markers on the card to show its current values
        if card.controller == me and card.Type != "Mission":
            if card.isFaceUp:
                if card.Culture != "":
                    card.markers[markerTypes['Culture']] = int(card.Culture)
                if card.Science != "":
                    card.markers[markerTypes['Science']] = int(card.Science)
                if card.Combat != "":
                    card.markers[markerTypes['Combat']] = int(card.Combat)
                if card.Ingenuity != "":
                    card.markers[markerTypes['Ingenuity']] = int(card.Ingenuity)
    #### Align the active mission
    if storedMission != None:
        if myTurn():
            mission.moveToTable(-81 if invert else -105, -45 if invert else -44)
            diff += value
            mission.markers[markerTypes['skill']] = skill
            mission.markers[markerTypes['diff']] = diff
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
        remoteCall(players[1], "cleanup", [True])




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
    setGlobalVariable("priority", str((players[1]._id, False)))

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
        setGlobalVariable("priority", str((players[1]._id, False)))
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