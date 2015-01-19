#---------------------------------------------------------------------------
# Constants
#---------------------------------------------------------------------------

import re
import clr

clr.AddReference("System.Drawing")
clr.AddReference("System.Windows.Forms")

from System.Drawing import Point, Color, Font, FontStyle
from System.Windows.Forms import *

def printGUID(card, x = 0, y = 0, txt = ""):
    if card.model in scriptsDict:
        txt = " (Scripted)"
    whisper("{}~{}{}".format(card, card.model, txt))

def moveCardEvent(player, card, fromGroup, toGroup, oldIndex, index, oldX, oldY, x, y, highlight = None, markers = {}, isScriptMove = False ):
    mute()
    if player != me:
        return
    if isScriptMove:
        return
    if fromGroup == table: ## Return cards to their original position on the table
        card.moveToTable(oldX,oldY)
        card.setIndex(oldIndex)
    elif fromGroup == me.hand and toGroup == me.hand: ## Allow re-arranging of the hand
        return
    else: ## Return card to itis original pile.
        card.moveTo(fromGroup, oldIndex)
        notify("Overriding card movement...")

def resetVars(group, x = 0, y = 0):
    for p in getPlayers():
        remoteCall(p, 'reloadLocalVars', [p])


def nextPhaseQueue():
    return ([], "game", "nextPhase", 0, turnPlayer()._id, False, None)

def reloadLocalVars(player):
    mute()
    if player == me:
        #### Prep initial variables
        global storedCards, storedTurnPlayer, storedPhase, storedPriority, storedVictory, storedOppVictory, storedMission, storedGameStats, storedQueue
        storedTurnPlayer = int(getGlobalVariable("turnplayer"))
        storedPhase = eval(getGlobalVariable("phase"))
        storedPriority = eval(getGlobalVariable("priority"))
        storedMission = eval(getGlobalVariable("activemission"))
        storedGameStats = eval(getGlobalVariable("gameStats"))
        storedCards = eval(getGlobalVariable("cards"))
        storedQueue = eval(getGlobalVariable("cardqueue"))
        storedVictory = int(getPlayers()[1].getGlobalVariable("victory"))
        storedOppVictory = int(me.getGlobalVariable("victory"))
        
def registerTeam(player, groups):
    mute()
    reloadLocalVars(me)
    global storedCards, storedPhase, storedVictory, storedOppVictory, storedQueue
    if player != me:  #only execute this event if its your own deck
        return
    #### The game only works with 2 players, so anyone else loading a deck will have their cards deleted
    if storedPhase not in [0, 1]: ## pre.1reg or pre.2reg
        whisper("cannot load deck -- there are already 2 players registered.")
        for group in [me.Deck, me.piles["Mission Pile"], me.Team]:
            for c in group:
                c.delete()
        return
    #### Verify deck contents
    if len(me.Team) != 4:
        whisper("cannot load deck -- it does not have 4 team characters.")
        for group in [me.Deck, me.piles["Mission Pile"], me.Team]:
            for c in group:
                c.delete()
        return
    if len(me.piles["Mission Pile"]) != 12:
        whisper("cannot load deck -- it does not have 12 missions.")
        for group in [me.Deck, me.piles["Mission Pile"], me.Team]:
            for c in group:
                c.delete()
        return
    #### Store victory points
    victory = 0
    for card in me.Team:
        card.moveToTable(0,0)
        storedCards = storeNewCards(card, {"s":"r"}, storedCards)
        victory += int(card.Cost)  #add the card's cost to the victory total
    me.setGlobalVariable("victory", str(victory)) #Stores your opponent's victory total
    storedVictory = int(getPlayers()[1].getGlobalVariable("victory"))
    storedOppVictory = int(me.getGlobalVariable("victory"))
    notify("{} registers their Team ({} points).".format(me, victory))
    me.Deck.shuffle()
    me.piles["Mission Pile"].shuffle()
    setGlobalVariable("cards", str(storedCards))
    #### Determine who goes first
    if storedPhase == 0: ## pre.1reg 
        setGlobalVariable("phase", "1") 
    #### After the second player registers their deck, the starting player can be determined
    elif storedPhase == 1: ## pre.2reg
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
        oppTeam = [c for c in storedCards if "Team Character" in Card(c).Type and not Card(c).controller == stopPlayer]
        setGlobalVariable("cardqueue", str([(oppTeam, "game", "stopCard", 0, stopPlayer._id, False, None), ([], "game", "nextPhase", 0, startingPlayer._id, False, None)]))
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
    global storedPhase, storedQueue, storedCards, storedGameStats, storedMission
    #### update python global variables
    if varName == "turnplayer":
        global storedTurnPlayer
        storedTurnPlayer = int(newValue)
    elif varName == "cards":
        storedCards = eval(newValue)
        cleanup()
    elif varName == "activemission":
        storedMission = eval(newValue)
    elif varName == "gameStats":
        storedGameStats = eval(newValue)
    elif varName == "priority":
        global storedPriority
        storedPriority = eval(newValue)
    elif varName == "cardqueue":
        storedQueue = eval(newValue)
        if len(storedQueue) > 0 and storedQueue[0][4] == me._id:
            resolveQueue()
        cleanup()
    #### Phase Changes
    elif varName == "phase":
        storedPhase = eval(newValue)
        #### First Player Mulligan
        if storedPhase == 2: ## "pre.1mul
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
                setGlobalVariable("phase", "3") ## pre.2mul
            return
        #### Second Player Mulligan
        if storedPhase == 3: ## pre.2mul
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
                setGlobalVariable("phase", "4") ## pow.main
            return
        #### Entering Power Phase
        if storedPhase == 4: ## pow.main
            power = 3 + len([c for c in storedCards if cardActivity(Card(c)) == "glyph"])
            me.Power = power
            notify("{} gained {} power.".format(me, power))
            #### Check for power phase script triggers
            if myTurn():
                triggerQueue = phaseTriggers("onPowerEnd", None)
                if len(triggerQueue) == 0:
                    setGlobalVariable("phase", "5") ## mis.start
                else:
                    storedQueue = triggerQueue + [nextPhaseQueue()] + storedQueue
                    setGlobalVariable("cardqueue", str(storedQueue))
            return
        #### Setting up a new Mission
        if storedPhase == 5: ## mis.start
            if myTurn():
                notify(" ~~ {}'s Mission Phase ~~ ".format(me))
                if storedMission != None:
                    notify("ERROR: There shouldn't be an active mission!")
                    return
                mission = me.piles["Mission Pile"].top()
                mission.moveToTable(0,0)
                storedCards = storeNewCards(mission, {"s": "am"}, storedCards)
                if mission.Culture != "":
                    skilltype = "Culture"
                elif mission.Science != "":
                    skilltype = "Science"
                elif mission.Combat != "":
                    skilltype = "Combat"
                elif mission.Ingenuity != "":
                    skilltype = "Ingenuity"
                else:
                    notify("ERROR: Mission has no skill types.")
                    return
                storedMission = (mission._id, skilltype, "a")
                setGlobalVariable("activemission", str(storedMission))
                notify("{}'s current mission is {}.".format(me, mission))
                ## Check for a rule that modifies this mission's starting difficulty
                if 'nmd' in storedGameStats: ## next mission difficulty changes apply now
                    boostList = storedCards[mission._id].get("m", [])
                    for boost in storedGameStats["nmd"]:
                        boostList += [(skillDict[skilltype], boost[0], None)]
                    storedCards[mission._id]["m"] = boostList
                    del storedGameStats['nmd']
                    setGlobalVariable("gameStats", str(storedGameStats))
                setGlobalVariable("cards", str(storedCards))
                ## Check for any card-specific scripts
                storedQueue = phaseTriggers("onPlayMission", mission._id) + [nextPhaseQueue()] + storedQueue
                setGlobalVariable("cardqueue", str(storedQueue))
                setGlobalVariable("priority", str((turnPlayer()._id, False)))
            return
        #### Resolving the current mission
        if storedPhase == 7: ## mis.res
            if myTurn():
                if storedMission == None:
                    notify("ERROR: There is no registered active mission!")
                    return
                mission = Card(storedMission[0])
                type = storedMission[1]
                status = storedMission[2]
                if mission not in table:
                    mission.moveToTable(0,0)
                if mission.markers[markerTypes["skill"]] >= mission.markers[markerTypes["diff"]]:
                    missionOutcome = "success"
                else:
                    missionOutcome = "failure"
                notify("{} was a {}!".format(mission, missionOutcome))
                setGlobalVariable("activemission", str((mission._id, type, missionOutcome[0])))
                setGlobalVariable("phase", "8") ## mis.sucfail
            return
        if storedPhase == 8: ## mis.sucfail
            if myTurn():
                if storedMission == None:
                    notify("ERROR: There is no registered active mission!")
                    return
                mission = Card(storedMission[0])
                status = "Success" if storedMission[2] == "s" else "Failure"
                heroTriggers = []
                villainTriggers = []
                ## add any success or failure triggers to the queue
                for c in storedCards:
                    card = Card(c)
                    if card in table and storedCards[c]["s"] == "a" and storedCards[c].get("r" + storedMission[2], False) == False and hasTriggers(card, "on" + status, card._id):
                        if card.controller == me:
                            heroTriggers.append(c)
                        else:
                            villainTriggers.append(c)
                if hasTriggers(mission, "on" + status, mission._id): ## Add the mission's trigger if it has one
                    heroTriggers.append(mission._id)
                newQueue = []
                if len(heroTriggers) > 0: ## attach hero triggers to queue
                    newQueue += [(heroTriggers, "trig", "on" + status, 0, turnPlayer()._id, False, None)]
                if len(villainTriggers) > 0: ## attach villain triggers to queue
                    newQueue += [(villainTriggers, "trig", "on" + status, 0, turnPlayer(False)._id, False, None)]
                if len(newQueue) == 0: ## skip all this junk if there's no actual triggers
                    setGlobalVariable("phase", "9") ## mis.adv
                else:
                    if len(heroTriggers) > 0:
                        notify("{} has {} triggers to resolve.".format(me, status))
                    else:
                        notify("{} has {} triggers to resolve.".format(turnPlayer(False), status))
                    storedQueue = newQueue + [nextPhaseQueue()] + storedQueue
                    setGlobalVariable("cardqueue", str(storedQueue))
            return
        if storedPhase == 9: ## mis.adv
            if myTurn():
                if storedMission == None:
                    notify("ERROR: There is no registered active mission!")
                    return
                #### First, stop all hero characters assigned to the mission.
                triggers = []
                for c in storedCards:
                    card = Card(c)
                    if card in table and storedCards[c]["s"] == "a" and card.controller != me and card.Type == "Adversary": ## add assigned adversaries to the trigger list
                        triggers.append(c)
                    elif card in table and storedCards[c]["s"] == "a" and card.controller == me and card.Type in heroTypes: ## stops all assigned hero cards
                        storedCards[c]["s"] = "s"
                        storedCards[c]["p"] = True
                    elif card not in table:
                        notify("ERROR: {} in storedCards could not be found in table!".format(card))
                setGlobalVariable("cards", str(storedCards))
                if len(triggers) == 0:
                    ## skip all this junk
                    setGlobalVariable("phase", "10") ## mis.gly
                else:
                    notify("{} has adversaries to revive.".format(turnPlayer(False)))
                    storedQueue = [(triggers, "game", "revive", 0, turnPlayer(False)._id, False, None)] + [nextPhaseQueue()] + storedQueue
                    setGlobalVariable("cardqueue", str(storedQueue))
            return
        if storedPhase == 10: ## mis.gly
            #### Destroy all complications and obstacles
            if not myTurn():
                heroEndTriggers = []
                villainEndTriggers = []
                triggers = []
                for c in storedCards.keys():
                    card = Card(c)
                    if card not in table:
                        notify("ERROR: {} in storedCards could not be found in table!".format(card))
                    else:
                        ##find all previously assigned characters as glyph targets
                        if "p" in storedCards[c]:
                            triggers.append(c)
                            del storedCards[c]["p"]
                        if storedCards[c]["s"] == "c" and card.controller == me and card.isFaceUp == False:
                            card.moveTo(me.Discard)
                            del storedCards[c]
                        elif storedCards[c]["s"] == "a" and card.controller == me and card.Type == "Obstacle":
                            card.moveTo(me.Discard)
                            del storedCards[c]
                        ## Check for end of mission triggers
                        if cardActivity(card) == "active" and hasTriggers(card, "onMissionEnd", card._id):
                            if card.controller == me:
                                villainEndTriggers.append(c)
                            else:
                                heroEndTriggers.append(c)
                #### Check the mission's status and skip glyph step if it was a failure
                if storedMission == None:
                    notify("ERROR: There is no registered active mission!")
                    return
                mission = storedMission[0]
                status = storedMission[2]
                #### Add end of mission triggers to the queue
                newQueue = []
                if status == "s":
                    notify("{} must choose a character to earn the glyph.".format(turnPlayer()))
                    storedGameStats["sm"] += [mission] ## Add the successful mission to the game stats
                    setGlobalVariable("gameStats", str(storedGameStats))
                    newQueue += [(triggers, "game", "glyph", 0, turnPlayer()._id, False, mission)]
                else:
                    #### Mission Failure
                    storedCards[mission]["s"] = "f"
                    storedGameStats["fm"] += [mission]
                    setGlobalVariable("gameStats", str(storedGameStats))
                setGlobalVariable("cards", str(storedCards))
                if len(heroEndTriggers) > 0: ## attach hero triggers to queue
                    newQueue += [(heroEndTriggers, "trig", "onMissionEnd", 0, turnPlayer()._id, False, None)]
                if len(villainEndTriggers) > 0: ## attach villain triggers to queue
                    newQueue += [(villainEndTriggers, "trig", "onMissionEnd", 0, turnPlayer(False)._id, False, None)]
                #### if the mission was successful we need to add the glyph-granting card queue
                if len(newQueue) == 0:
                    setGlobalVariable("phase", "11") ## mis.end
                else:
                    setGlobalVariable("cardqueue", str(newQueue + [nextPhaseQueue()] + storedQueue))
            return
        if storedPhase == 11: ## mis.end
            if myTurn():
                setGlobalVariable("activemission", "None")
                failCount = len(storedGameStats["fm"]) ##count the number of failed missions so far
                if 'cp' in storedGameStats:
                    del storedGameStats['cp']
                if storedGameStats.get("nnm", [False])[0]:
                    nextMission = False ##don't continue to another mission
                    del storedGameStats["nnm"]
                elif me.Power < failCount:
                    nextMission = False ##don't continue to another mission
                else:
                    nextMission = confirm("Would you like to continue to another mission?\n\n({} failed missions this turn.)".format(failCount))
                setGlobalVariable("gameStats", str(storedGameStats))
                for c in storedCards.keys():
                    if "m" in storedCards[c]: ## Remove skill boosts lasting until end of mission
                        del storedCards[c]["m"]
                    if "b" in storedCards[c]: ## Remove blocked status from all cards
                        del storedCards[c]["b"]
                    if "rf" in storedCards[c]: ## Remove the tag that blocks failure text
                        del storedCards[c]["rf"]
                if nextMission: ## continue to next mission
                    me.Power -= failCount
                    turnPlayer(False).Power += failCount
                    setGlobalVariable("cards", str(storedCards))
                    setGlobalVariable("phase", "5") ## mis.start
                else: ## Skip to Debrief Phase
                    notify(" ~~ {}'s Debrief Phase ~~ ".format(me))
                    newQueue = phaseTriggers("onDebrief", None)
                    if len(newQueue) == 0:
                        setGlobalVariable("phase", "12") ## deb.start
                    else:
                        setGlobalVariable("cardqueue", str(newQueue + [nextPhaseQueue()] + storedQueue))
            return
        if storedPhase == 12: ## deb.start
            if myTurn():
                ## Clear the successful and failed missions
                failedMissions = storedGameStats["fm"]
                for mission in failedMissions:
                    if Card(mission) not in table:
                        failedMissions.remove(mission)
                storedGameStats["fm"] = []
                storedGameStats["sm"] = []
                if 'cp' in storedGameStats:
                    del storedGameStats['cp']
                if 'nmd' in storedGameStats:
                    del storedGameStats['nmd']
                ## Ready all stopped characters
                for c in storedCards.keys():
                    if storedCards[c]["s"] == "s":
                        storedCards[c]["s"] = "r"
                    if "t" in storedCards[c]: ## Remove skill boosts lasting until end of turn
                        del storedCards[c]["t"]
                setGlobalVariable("cards", str(storedCards))
                setGlobalVariable("gameStats", str(storedGameStats))
                if len(failedMissions) > 0:
                    notify("{} has failed missions to return to their mission pile.".format(me))
                    setGlobalVariable("cardqueue", str([(failedMissions, "game", "failMiss", -len(failedMissions), turnPlayer()._id, False, None)] + [nextPhaseQueue()] + storedQueue))
                else:
                    setGlobalVariable("phase", "13") ## deb.ref
            return
        if storedPhase == 13: ## deb.ref
            if myTurn():
                newQueue = []
                handSize = len(me.hand)
                for player in [turnPlayer(), turnPlayer(False)]:
                    handSize = len(player.hand)
                    if handSize > 8: ## Discard down to 8
                        newQueue += [([], "game", "discardTo8", 8 - len(player.hand), player._id, False, None)]
#                        notify("{} must discard {} cards, down to 8.".format(me, handSize - 8))
                    elif handSize < 8: ## Fill hand to 8
                        newQueue += [([], "game", "drawTo8", 0, player._id, False, None)]
#                        notify("{} refilled hand to 8, drawing {} cards.".format(me, count))
                if len(newQueue) == 0: ## jump to end of debrief step
                    setGlobalVariable("phase", "14") ## deb.end
                else:
                    storedQueue = newQueue + [nextPhaseQueue()] + storedQueue
                    setGlobalVariable("cardqueue", str(storedQueue))
            return
        if storedPhase == 14: ## deb.end
            if myTurn():
                notify("{}'s turn ends.".format(me))
                nextPlayer = turnPlayer(False)
                nextPlayer.setActivePlayer()
                setGlobalVariable("turnplayer", str(nextPlayer._id))
                cleanup()
                notify(" ~~ {}'s Power Phase ~~ ".format(nextPlayer))
                setGlobalVariable("phase", "4") ## pow.main

def doubleClick(card, mouseButton, keysDown):
    mute()
    ##TODO: Allow discard queue triggers to target cards in your hand (currently only works for table)
    global storedPhase, storedQueue, storedCards
    phase = storedPhase
    #### Card Queue Actions
    if storedQueue != []:
        resolveQueue(card._id)
        return
    #### Phase-specific Doubleclick Actions
    if card not in table:
        return
    if cardActivity(card) == "inactive":
        whisper("You cannot perform on an inactive card.")
        return
    if not myPriority():  ## You need priority to use doubleClick
        whisper("Cannot perform action on {}: You don't have priority.".format(card))
        return
    #### general assigning character to the mission
    if phase == 6: ## mis.main
        if card.Type not in ["Adversary", "Team Character", "Support Character"]:
            whisper("Cannot assign {}: It is not an assignable card type.".format(card))
            return
        if storedMission == None:
            whisper("Cannot assign {} as there is no active mission.".format(card))
            return
        mission = storedMission[0]
        type = storedMission[1]
        status = storedMission[2]
        cardSkill = getStats(card)[type] ## grab the card's skill value of the active mission
        if cardSkill == None:
            whisper("Cannot assign {}: Does not match the active mission's {} skill.".format(card, type))
            return
        if card._id not in storedCards:
            notify("ERROR: {} not in cards global dictionary.".format(card))
            return
        if storedCards[card._id]["s"] != "r":
            whisper("Cannot assign: {} is not Ready.".format(card))
            return
        #### Check for additional costs to play the card
        if not checkCosts(card, "onAssignCost", card._id):
            return
        #### check if the card is being blocked
        blockedList = storedCards[card._id].get("b", [])
        for blocker in blockedList:
            if blocker != None and blocker not in storedCards: ## If the blocker isn't in play anymore, remove it from the list.
                blockedList.remove(blocker)
        if len(blockedList) > 0:
            whisper("Cannot assign: {} is being blocked{}.".format(card, "" if blockedList == [None] else " by " + ", ".join([Card(x).name for x in blockedList if x != None])))
            return
        storedQueue = phaseTriggers("onAssignCost", card._id) + [([card._id], "game", "assignCard", 0, me._id, False, None)] + phaseTriggers("onAssign", card._id) + storedQueue
        setGlobalVariable("priority", str((getPlayers()[1]._id, False)))
        setGlobalVariable("cardqueue", str(storedQueue))

def playcard(card, x = 0, y = 0):
    mute()
    global storedPhase
    if storedPhase != 6: ## mis.main
        return
    if not myPriority():
        whisper("Cannot choose {}: You don't have priority.".format(card))
        return
    global storedQueue
    if len(storedQueue) > 0:
        whisper("Cannot play {}: There are effects that need resolving.".format(card))
        return
    if cardActivity(card) == "inactive":
        whisper("You cannot play {} during your {}turn.".format(card, "" if myTurn() else "opponent's "))
        return
    if card.Type == "Obstacle":
        if storedMission == None:
            whisper("Cannot play {} as there is no active mission.".format(card))
            return
        missionSkill = storedMission[1]
        if card.properties[missionSkill] == None or card.properties[missionSkill] == "":
            whisper("Cannot play {}: Does not match the active mission's {} skill.".format(card, missionSkill))
            return
    global storedCards
    #### Deal with Boosting cards, or preventing duplicate card names
    if card.Type in ["Team Character", "Support Character", "Adversary"]:
        matchingCards = [c for c in storedCards if Card(c).controller == me and Card(c).name == card.name and cardActivity(Card(c)) == "active"]
        for c in matchingCards: ## check the status of the matched cards
            if storedCards[c]["s"] == "a":
                ## Boost card
                if confirm("Cannot play {}: You already have a character with that name in play.\n\nBoost it?".format(card.name)):
                    card.moveTo(card.owner.Discard)
                    missionBoosts = storedCards[c].get("m", [])
                    storedCards[c]["m"] = missionBoosts + [(5, 1, 'boost')]
                    setGlobalVariable("cards", str(storedCards))
                    setGlobalVariable("priority", str((getPlayers()[1]._id, False)))
                return
            whisper("Cannot play {}: You already have a character with that name in play.".format(card))
            return
    global storedGameStats
    for (value, source) in storedGameStats.get('cp', []):
        if card.Type in value and cardActivity(Card(source)) in ["active", "active mission"]:
            whisper("Cannot play {}: {} is preventing it.".format(card, Card(source)))
            return
    #### Check for additional costs to play the card
    if not checkCosts(card, "onPlayCost", card._id):
        return
    #### Pay power cost to play card
    cardCost = int(card.Cost)
    for c in storedCards.keys() + [card._id]:
        cardScripts = scriptsDict.get(Card(c).model, [])
        if "onGetPlayCost" in cardScripts:
            for (actionType, params) in cardScripts["onGetPlayCost"]:
                if actionType == "costChange":
                    if checkConditions(Card(c), params.get("condition", {}), card._id)[0] == False:
                        continue
                    if "trigger" in params:
                        if params["trigger"] == "self":
                            if c == card._id:
                                cardCost += eval(params["value"])
                        elif checkConditions(card, params["trigger"], c)[0]:
                            if params["trigger"].get("ignoreSelf", False) and c == card._id:
                                continue
                            cardCost += eval(params["value"])
    if me.Power < cardCost:
        whisper("You do not have enough Power to play that.")
        return
    me.Power -= cardCost
    card.moveTo(me.Team)
    storedQueue = triggerScripts(card, "onPlayCost", card._id) + phaseTriggers("onPlayCost", card._id) + [([card._id], "game", "playCard", 0, me._id, False, None)] + storedQueue
    setGlobalVariable("priority", str((getPlayers()[1]._id, False)))
    setGlobalVariable("cardqueue", str(storedQueue))

def activateAbility(card, x = 0, y = 0):
    mute()
    if not myPriority():
        whisper("Cannot activate {}'s ability: You don't have priority.".format(card))
        return
    global storedPhase
    if storedPhase != 6: ## mis.main
        whisper("Cannot activate {}'s ability at this time.".format(card))
        return
    if cardActivity(card) == "inactive":
        whisper("You cannot activate {} during your {}turn.".format(card, "" if myTurn() else "opponent's "))
        return
    global storedQueue
    if len(storedQueue) > 0:
        whisper("Cannot activate {}: There are effect that need resolving.".format(card))
        return
    #### check for scripted abilities
    abilityText = [x for x in card.text.split('\r') if u'\u2013' in x] ## grab all abilities from card text
    if len(abilityText) == 0: ## cancel out if the card has no abilities
        return
    elif len(abilityText) == 1:
        abilityTrigger = "onAbility1"
    else:
        abilityTrigger = "onAbility" + str(askChoice("Choose an ability:", abilityText, []))
    #### Check for additional costs to play the ability
    if not checkCosts(card, "{}Cost".format(abilityTrigger), card._id):
        return
    storedQueue = phaseTriggers("{}Cost".format(abilityTrigger), card._id) + phaseTriggers("{}".format(abilityTrigger), card._id) + storedQueue
    setGlobalVariable("priority", str((getPlayers()[1]._id, False)))
    setGlobalVariable("cardqueue", str(storedQueue))

def checkCosts(origCard, type, sourceId):  ## This function verifies if all costs can be met, but doesn't actually apply the costs
    mute()
    global storedCards
    for c in storedCards:
        card = Card(c)
        if cardActivity(card) not in ["active", "active mission"]:
            continue
        if type not in scriptsDict.get(card.model, []):
            continue
        for (actionType, params) in scriptsDict[card.model][type]:
            if card == origCard: ## if this is the original card
                conditionCheck = checkConditions(card, params.get("condition", {}), None)
                if conditionCheck[0] == False:
                    whisper("Cannot continue: {} does not have the required {}.".format(card, conditionCheck[1]))
                    return False
            elif 'trigger' in params:
                conditionCheck = checkConditions(origCard, params.get("trigger", {}), None)
                if conditionCheck[0] == False:
                    continue
#                    whisper("Cannot continue: {} does not have the required {}.".format(origCard, conditionCheck[1]))
#                    return False
            else:  ## skip if the card doesn't trigger
                continue
            if actionType == "powerChange":
                if params["player"] == "hero":
                    player = turnPlayer()
                else:
                    player = turnPlayer(False)
                if player.Power + eval(params["value"]) < 0:
                    whisper("Cannot continue: {} cannot pay the Power cost.".format(player))
                    return False
                continue
            if actionType == "statusChange":
                targets = queueTargets(card._id, params, sourceId)
                if len(targets) == 0:
                    whisper("Cannot continue: there are no valid targets for {}.".format(card))
                    return False
                continue
            if actionType == "moveCard":
                if params["player"] == "hero":
                    player = turnPlayer()
                else:
                    player = turnPlayer(False)
                if len(eval(params["target"]["group"])) < eval(params["count"]):
                    whisper("Cannot continue: {} does not have enough cards in their hand.".format(player))
                    return False
    return True

def myPriority():
    global storedPriority
    if storedPriority == 0:
        return False
    if Player(storedPriority[0]) == me:
        return True
    else:
        return False

def cardActivity(card):
    mute()
    global storedCards
    status = storedCards.get(card._id, {}).get("s", "active")
    if status == "am":
        ret = "active mission"
    elif status == "c":
        ret = "complication"
    elif status == "g":
        ret = "glyph"
    elif status == "f":
        ret = "failed mission"
    else:
        ret = "active"
#    if myTurn() == ((card.controller == me) == ((card.Type in heroTypes) and (card.isFaceUp))):
    if myTurn():
        if card.isFaceUp == False:
            if card.controller == me:
                return "inactive"
            else:
                return ret
        if card.Type in heroTypes or card.Type == "Mission":
            if card.controller == me:
                return ret
            else:
                return "inactive"
        else:
            if card.controller == me:
                return "inactive"
            else:
                return ret
    else:
        if card.isFaceUp == False:
            if card.controller == me:
                return ret
            else:
                return "inactive"
        if card.Type in heroTypes or card.Type == "Mission":
            if card.controller == me:
                return "inactive"
            else:
                return ret
        else:
            if card.controller == me:
                return ret
            else:
                return "inactive"

def turnPlayer(var = True):
    global storedTurnPlayer
    if var == False:
        for p in getPlayers():
            if p._id != storedTurnPlayer:
                return p
    else:
        return Player(storedTurnPlayer)

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

def storeNewCards(card, initialState, cardDict):
    mute()
    cardData = dict(initialState)
    if len(cardDict) == 0:
        cardData["#"] = 1
    else:
        cardData["#"] = max([c.get("#", 0) for c in cardDict.values()]) + 1
#    for (k,v) in scriptsDict.get(card.model, {}).items():
#        for (actionType, params) in v:
#            if k == "onGetStats" and params.get("target", "self") != "self":
#                cardData["gs"] = (True, None, "p")
    cardDict[card._id] = cardData
    return cardDict

def hasGlyph(glyphList, requiredGlyphs):
    mute()
    attachedGlyphs = [Card(c).Glyph for c in glyphList]
    orGlyphCheck = False
    for orGlyphs in requiredGlyphs: ## First layer of list uses OR matching
        andGlyphCheck = True
        for andGlyphs in orGlyphs: ## Second layer of list uses AND matching
            if andGlyphs not in attachedGlyphs:
                andGlyphCheck = False
        if andGlyphCheck == True and orGlyphCheck == False:
            orGlyphCheck = True
    if orGlyphCheck == False: ## Will be False if the glyph requirements aren't met
        return False
    return True

def getStats(card):
    mute()
    global storedCards
    baseSkills = {"Culture": None, "Science": None, "Combat": None, "Ingenuity": None, "Difficulty": None}
    allSkillsValue = 0
    ## Set the base skill from the printed card
    for baseSkill in baseSkills.keys():
        if card.properties[baseSkill] not in ["", "?"]:
            baseSkills[baseSkill] = int(card.properties[baseSkill])
    cardScripts = []
    for c in storedCards:
        if cardActivity(Card(c)) in ["active", "active mission"]:
            for (actionType, params) in scriptsDict.get(Card(c).model, {}).get("onGetStats", {}):
                if actionType == "skillChange":
                    if checkConditions(Card(c), params.get("condition", {}), card._id)[0] == False:
                        continue
                    if "trigger" in params:
                        if params["trigger"] == "self":
                            if c == card._id:
                                cardScripts += [(params["skill"], eval(params["value"]))]
                        elif checkConditions(card, params["trigger"], c)[0]:
                            if params["trigger"].get("ignoreSelf", False) and c == card._id:
                                continue
                            cardScripts += [(params["skill"], eval(params["value"]))]
    ## Apply static skill changes from card abilities
    for (skill, value) in cardScripts:
        if skill == "all": ## Special case for abilities that boost all skills equally, and are listed as 'skills' or 'difficulty'
            allSkillsValue += value
        else:
            for baseSkill in skill:
                if baseSkills[baseSkill]: ## add value to existing skill
                    baseSkills[baseSkill] += value
                else: ## Add the skill if the card doesn't already have a base for it
                    baseSkills[baseSkill] = value
    ## Apply mission- and turn-duration boosts from storedCards dict
    if card in table and card._id in storedCards: ##only cards on the table are checked for boosts
        for boost in storedCards[card._id].get("m", []) + storedCards[card._id].get("t", []):
            boostSkill = skillDict[boost[0]]
            boostValue = boost[1]
            boostOrigin = boost[2]
            if boostOrigin not in [None, "boost"] and Card(boostOrigin) not in table: ## skip if the originating card isn't in play anymore
                continue
            if boostSkill == "all":## Special case for abilities that boost all skills equally, and are listed as 'skills' or 'difficulty'
                allSkillsValue += boostValue
            else:
                if baseSkills[boostSkill]:## add value to existing skill
                    baseSkills[boostSkill] += boostValue
                else: ## Add the skill if the card doesn't already have a base for it
                    baseSkills[boostSkill] = boostValue
    #### apply 'all skills' boosts
    for baseSkill in baseSkills.keys():
        if baseSkills[baseSkill] != None: ## Only apply the skill change if the character has the skill, skip otherwise
            baseSkills[baseSkill] += allSkillsValue
    return baseSkills

def passturn(group, x = 0, y = 0): 
    mute()
    #### Pass on skippable triggers in the queue
    global storedQueue
    if len(storedQueue) > 0: ## if the queue's not empty
        resolveQueue(skip = True)
        return
    global storedPhase
    if storedPhase == 6: ## mis.main
        global storedPriority
        if Player(storedPriority[0]) != me:
            whisper("Cannot pass turn: You don't have priority.")
            return
        if len(storedQueue) > 0:
            whisper("Cannot pass priority: There are abilities that need resolving.")
            return
        if storedPriority[1] == False:
            notify("{} passes.".format(me))
            setGlobalVariable("priority", str((getPlayers()[1]._id, True)))
        else:
            notify("{} passes, enters Mission Resolution.".format(me))
            setGlobalVariable("priority", str((turnPlayer()._id, False)))
            setGlobalVariable("phase", "7") ## mis.res

def queueTargets(qCard = None, params = None, qSource = None):
    mute()
    global storedQueue, storedCards
    if qCard == None and params == None:
        if storedQueue == []:
            return []
        (qCard, qTrigger, qType, qCount, qPriority, qSkippable, qSource) = storedQueue[0]
        if qTrigger == "trig": ## This queue contains all the cards that trigger off certain actions
            return [c for c in qCard if c in storedCards] ## Only return cards that are still on the table
#           action, params = scriptsDict["game"][qType][int(qTrigger)]
        elif qTrigger == "game": ## These are special game-based triggers, no card-specific scripts
            action, params = scriptsDict["game"][qType][0]
        else:
            action, params = scriptsDict[Card(qCard).model][qType][int(qTrigger)]
    targetDict = params.get("target", None)
    if targetDict == None:
        return []
    if targetDict.get("special", None) == "self":
        return [qCard]
    if targetDict.get("special", None) == "source":
        return [qSource]
    if targetDict.get("special", None) == "stored":
        return storedCards[qCard].get("st", [])
    targetGroup = params["target"].get("group", None)
    if targetDict.get("special", None) == "queue":
        if targetGroup == None:
            return [c for c in qCard if c in storedCards]
        else:
            return [c for c in qCard if Card(c) in eval(targetGroup)]
    ####Get targets
    if targetGroup == None:
        targets = [c for c in storedCards if checkConditions(Card(c), targetDict, qSource)[0] == True ]
    else:
        targets = [c._id for c in eval(targetGroup) if checkConditions(c, targetDict, qSource)[0] == True ]
    if targetDict.get("ignoreSelf", False) and qSource in targets:
        targets.remove(qSource)
    return targets

def phaseTriggers(triggerName, sourceId, skippable = False):
    mute()
    global storedCards, storedQueue
    heroTriggers = []
    villainTriggers = []
    newQueue = []
    for c in storedCards:
        card = Card(c)
        if card in table and cardActivity(card) in ["active", "active mission"] and hasTriggers(card, triggerName, sourceId):
            if card.controller == me:
                heroTriggers.append(c)
            else:
                villainTriggers.append(c)
    if len(villainTriggers) == 0 and heroTriggers == [sourceId]: ## Don't queue if the only trigger is the source
        return triggerScripts(Card(sourceId), triggerName, sourceId)
    if len(heroTriggers) > 0: ## attach hero triggers to queue
        newQueue += [(heroTriggers, "trig", triggerName, 0, turnPlayer()._id, skippable, sourceId)]
    if len(villainTriggers) > 0: ## attach villain triggers to queue
        newQueue += [(villainTriggers, "trig", triggerName, 0, turnPlayer(False)._id, skippable, sourceId)]
    if len(newQueue) == 0: ## skip all this junk if there's no actual triggers
        return []
    return newQueue

def hasTriggers(card, triggerName, sourceId):
    mute()
    if sourceId == None:
        sourceId = card._id
    if triggerName not in scriptsDict.get(card.model, []): #return false if the card doesn't have any trigger
        return False
    for (trigger, params) in scriptsDict[card.model].get(triggerName, []): #Check each trigger to see if it is valid
        if card._id == sourceId: ## if the card is the source of the trigger
            if checkConditions(card, params.get("condition", {}), sourceId)[0]:
                return True
        else: ## if the card is triggering off the source
            if 'trigger' in params and checkConditions(Card(sourceId), params["trigger"], card._id)[0]:
                return True
    return False

def checkConditions(card, conditions, sourceId):
    mute()
    global storedCards, storedMission
    if card._id in storedCards and cardActivity(card) == "inactive":
        return (False, "Inactive")
    if not eval(conditions.get("custom", 'True')):
        return (False, "State")
    glyphCheck = conditions.get("glyph", [])
    if glyphCheck == "None":
        if len(storedCards[card._id].get("g", [])) > 0:
            return (False, "Glyph")
    elif glyphCheck != [] and not hasGlyph(storedCards[card._id].get("g", []), eval(glyphCheck)):
        return (False, "Glyph")
    statusCheck = conditions.get("status", [])
    if statusCheck != [] and storedCards[card._id]["s"] not in statusCheck:
        return (False, "Status")
    skillCheck = conditions.get("hasSkill", None)
    if skillCheck != None and getStats(card)[skillCheck] != None:
        return (False, "Skill")
    typeCheck = conditions.get("type", [])
    if typeCheck != [] and not card.Type in typeCheck:
        return (False, "Type")
    traitCheck = conditions.get("trait", [])
    if traitCheck != [] and not card.Traits in traitCheck:
        return (False, "Trait")
    nameCheck = conditions.get("cardName", [])
    if nameCheck != [] and not card.Name in nameCheck:
        return (False, "Name")
    return (True, None)

def triggerScripts(card, type, sourceId): ## note this function assumes that the card scripts exist, doesn't do any verifying
    mute()
    if not hasTriggers(card, type, sourceId):
        return []
    cardScripts = scriptsDict[card.model][type]
    global storedCards
    queue = []
    scriptIndex = -1
    for (actionType, params) in cardScripts:
        scriptIndex += 1
        ## Verify that the condition is met
        if checkConditions(card, params.get("condition", {}), sourceId)[0] == False:
            continue #### Skip this trigger if the condition wasn't met    
        ## Acquire the targets for whatever action it may use
#        targets = queueTargets(card._id, params, sourceId)
#        targetCount = params.get("count", "None")
#        ## add trigger to card queue
#        if len(targets) == 0 or targetCount <= 0: ## Skip this loop if there are no legal targets to choose
#            continue
        if params.get("player", "hero" if myTurn() else "enemy") == "hero":
            player = turnPlayer()._id
        else:
            player = turnPlayer(False)._id
        queue.append((card._id, scriptIndex, type, 0, player, params.get("skippable", False), sourceId))
    return queue

def resolveQueue(target = None, skip = False):
    global storedQueue, storedCards, storedPhase, storedGameStats
    ## Set the initial values of the queue and card database, to compare later on
    tempQueue = eval(str(storedQueue))
    tempCards = eval(str(storedCards))
    tempPhase = eval(str(storedPhase))
    queueLoop = True
    while queueLoop == True:
        if len(storedQueue) == 0:
            queueLoop = "EMPTY"
            continue
        (qCard, qTrigger, qType, qCount, qPriority, qSkippable, qSource) = storedQueue[0] ## split apart the queue tuple
        if qSource == None: ##
            sourceCard = Player(qPriority).name
        else:
            sourceCard = Card(qSource)
        if Player(qPriority) != me: ## Skip if you don't have priority during the current card queue
            queueLoop = "BREAK"
            continue
        if skip == True:
            if qSkippable == True:
                notify("{} skips {}'s {} trigger.".format(me, Card(qSource), qType))
                del storedQueue[0]
                skip = False
            else:
                whisper("Cannot skip this trigger.")
                queueLoop = "BREAK"
            continue
        if qTrigger == "trig":  ## These hold cards which trigger on specific situations
            qTargets = queueTargets() ## the list of valid targets for that trigger
            if len(qTargets) == 0: ## If there's no cards with triggers waiting to resolve
                target = None
            elif len(qTargets) == 1: ## if there's only 1 target, automatically select it even if no target was passed
                target = qTargets[0]
                qTargets = []
            elif target == None: ## We need a target, so break the loop if there is none
                queueLoop = False
                continue
            elif target not in qTargets:
                whisper("{} is not a valid target!".format(Card(target)))
                queueLoop = False
                continue
            else:
                qTargets.remove(target)
            if len(qTargets) == 0: ## If the queue is now empty
                del storedQueue[0]
            else:
                storedQueue[0] = (qTargets, qTrigger, qType, qCount + 1, qPriority, qSkippable, qSource)
            storedQueue = triggerScripts(Card(target), qType, qSource) + storedQueue ## Add the new triggers to the queue
            target = None
            continue
        elif qTrigger == "game":  ## Game engine scripts, non-card specific
            qAction, params = scriptsDict["game"][qType][0] ## Get card script data for the queue trigger
            qTargets = queueTargets() ## Valid targets are always listed in game engine queues
        else: ## Card-specific triggers
            qAction, params = scriptsDict[Card(qCard).model][qType][int(qTrigger)] ## Get card script data for the queue trigger
            if checkConditions(Card(qCard), params.get("condition", {}), qSource)[0] == False: ##Skip this trigger if the condition wasn't met
                break ####
            qTargets = queueTargets()  ## The list of valid targets for that trigger
        targetCount = params.get("count", "1")
        if 'target' in params: ## Does the ability require a target?
            if len(qTargets) == 0:
                whisper("No valid targets for {}'s {} ability.".format(Card(qCard), qType))
                targets = []
            elif params["target"].get("special", "None") in ["self", "stored"] or qAction == "moveCard" or targetCount == "all": ## We don't need the target passed in for these
                targets = [x for x in qTargets]
            elif len(qTargets) == 1 and qSkippable == False: # If there's only 1 valid target, automatically target that one
                targets = [x for x in qTargets]
            else:
                if target == None:
                    queueLoop = False
                    continue
                if target not in qTargets:
                    whisper("{} is not a valid target!".format(Card(target)))
                    queueLoop = False
                    continue
                targets = [target]
            for t in targets:
                if t in qTargets:
                    qTargets.remove(t)
        else:
            targets = []
        ## Update the queue status
        if qTrigger == "game": ## game triggers keep a running list of queue objects
            for c in [x for x in qCard]: # scan through the queue for cards no longer in play
                if c in targets or c not in storedCards: ## remove the active targets as well
                    qCard.remove(c) ## remove the card from the queue
        if qAction == "moveCard" or targetCount == "all" or ('target' in params and len(qTargets) == 0) or qCount + 1 >= eval(targetCount):
            del storedQueue[0]
        else:
            storedQueue[0] = (qCard, qTrigger, qType, qCount + 1, qPriority, qSkippable, qSource)
        target = None  ## remove the active target so the engine doesn't re-target the same card again
        ## Announce that the triggers are resolving
        if qSource != None:
            notify("{} is resolving {}'s {} ability.".format(me, Card(qSource), qType))
        ## Apply trigger effects from the game engine
        if qAction == "phaseChange": ## This is a game trigger to switch phases once the queue empties
            storedPhase = phaseDict[storedPhase][1]
        elif qAction == "playCard":
            for targetCard in targets:
                #### Move the card to the correct location after playing it
                card = Card(targetCard)
                storedQueue = triggerScripts(card, "onPlay", qSource) + phaseTriggers("onPlay", targetCard) + storedQueue
                if card.Type == "Event":
                    card.moveTo(card.owner.Discard)
                elif card.Type == "Obstacle":
                    card.moveToTable(0,0)
                    storedCards = storeNewCards(card, {"s": "a"}, storedCards)
                else:
                    card.moveToTable(0,0)
                    storedCards = storeNewCards(card, {"s": "r"}, storedCards)
                notify("{} plays {}.".format(me, card))
        elif qAction == "revive":
            for targetCard in targets:
                card = Card(targetCard)
                #### Get status of mission to choose the correct action for the adversary
                if storedMission == None:
                    notify("ERROR: There is no registered active mission!")
                    continue
                choiceMap = {1:"Score", 2:"Revive", 3:"Destroy"}
                ## Remove the Revive option if you can't pay revive cost or if revive is disabled
                if len(me.Deck) < int(card.Revive) or storedGameStats.get("nr", [False])[0]:
                    choiceMap[2] = "Destroy"
                    del choiceMap[3]
                ##Remove the Score option if the mission was a success
                if storedMission[2] == "s":
                    choiceMap[1] = choiceMap[2]
                    if choiceMap[2] == "Revive":
                        choiceMap[2] = choiceMap[3]
                        del choiceMap[3]
                    else:
                        del choiceMap[2]
                    notify("{}".format(choiceMap))
                choiceList = sorted(choiceMap.values(), key=lambda x:x[1])
                choiceResult = 0
                while choiceResult == 0:
                    choiceResult = askChoice("Choose an action for {}".format(card.name), choiceList, [])
                choiceResult = choiceMap[choiceResult]
                #### Apply the action to the adversary
                if choiceResult == "Score": ## Score
                    del storedCards[targetCard]
                    card.moveTo(card.owner.piles["Villain Score Pile"])
                    scriptTrigger = "onScore"
                elif choiceResult == "Revive": ## Revive
                    for c in me.Deck.top(int(card.Revive)): ## discard cards from top of deck to pay revive cost
                        c.moveTo(me.Discard)
                    storedCards[targetCard]["s"] = "s" ## stops the adversary
                    scriptTrigger = "onRevive"
                else: ## destroy
                    del storedCards[targetCard]
                    card.moveTo(card.owner.Discard)
                    scriptTrigger = "onDestroy"
                qCount -= 1
                if storedGameStats.get("nr", [False])[0]:
                    del storedGameStats["nr"]
                    setGlobalVariable("gameStats", str(storedGameStats))
                storedQueue = triggerScripts(card, scriptTrigger, None) + storedQueue
        elif qAction == "glyph":
            for targetCard in targets:
                if storedMission == None:
                    notify("ERROR: There is no registered active mission!")
                    return
                glyphList = storedCards[targetCard].get("g", [])
                storedCards[targetCard]["g"] = glyphList + [qSource]  ## Add the glyph to the chosen character
                storedCards[qSource]["s"] = "g"  ## Sets the mission's status as an earned glyph
                notify("{} earns the glyph ({}.)".format(Card(targetCard), Card(qSource)))
                setGlobalVariable("activemission", "None")  ## Empties the active mission
        elif qAction == "moveCard":
            targetCheck = params["target"]
            fromGroup = eval(targetCheck["group"])
            if fromGroup == me.Deck:
                if params.get("skippable", False): #when a choice is required
                    if not confirm("Do you want to search your deck for a card?\n\nSource: {}".format(Card(qCard).name)):
                        continue
                me.Deck.setVisibility('me')
                rnd(1,10)
            skillCheck = targetCheck.get("hasSkill", None)
            typeCheck = targetCheck.get("type", [])
            loopCount = 0
            choices = []
            while qCount + loopCount < eval(params.get("count", "0")):
                targets = [c for c in fromGroup
                    if (typeCheck == [] or c.Type in typeCheck)
                    and (skillCheck == None or getStats(c)[skillCheck] != None)
                    ]
                if len(targets) == 0:
                    break
                choice = askCard(targets)
                if choice == None: ## If the player closes the window
                    if params.get("skippable", False) == False: #when a choice is required
                        continue
                    else:
                        break
                choices.append(choice)
                choice.moveTo(me.Team)
                loopCount += 1
            toGroup = eval(params["to"][0])
            toIndex = params["to"][1]
            doShuffle = False
            if toIndex == "shuffle":
                toIndex = 0
                doShuffle = True            
            for c in choices:
                if fromGroup == me.hand and toGroup == me.Discard:
                    notify("{} discards {} from hand.".format(me, choice))
                else:
                    notify("{} moves {} to {} from {}.".format(me, choice, toGroup.name, fromGroup.name))
                c.moveTo(toGroup, toIndex)
            if fromGroup == me.Deck or (toGroup == me.Deck and doShuffle == True): ## Shuffle the deck after looking at it
                me.Deck.setVisibility('none')
                rnd(1,10)
                me.Deck.shuffle()
                notify("{} shuffled their Deck.".format(me))
        elif qAction == "ruleSet":
            rule = params["rule"]
            value = eval(params["value"])
            newRule = storedGameStats.get(rule, [])
            if params.get("list", False):
                storedGameStats[rule] = storedGameStats.get(rule, []) + [(value, qSource)]
            else:
                storedGameStats[rule] = (value, qSource)
            setGlobalVariable("gameStats", str(storedGameStats))
        elif qAction == "powerChange":
            if params["player"] == "hero":
                player = turnPlayer()
            else:
                player = turnPlayer(False)
            powerNum = eval(params["value"])
            if player.Power + powerNum < 0: ## if the player doesn't have enough power to pay
                player.Power = 0
                powerNum = player.Power
            else:
                player.Power += powerNum
            notify("{} {} {} power from {}.".format(player, "loses" if powerNum < 0 else "gains", abs(powerNum), Card(qCard)))
        elif qAction == "fillHand":
            count = fillHand(eval(params["value"]))
            notify("{} refilled hand to 8, drawing {} cards.".format(me, count))
        elif qAction == "statusChange":
            for targetCard in targets:
                ## Clean up the blocked status
                blockedList = storedCards[targetCard].get("b", [])
                for blocker in blockedList:
                    if blocker != None and blocker not in storedCards: ## If the blocker isn't in play anymore, remove it from the list.
                        blockedList.remove(blocker)
                if len(blockedList) == 0: ## Remove the blocked status from the card if no cards are blocking anymore
                    if "b" in storedCards[targetCard]:
                        del storedCards[targetCard]["b"]
                else:
                    storedCards[targetCard]["b"] = blockedList
                ## Apply the status change
                action = params["action"]
                if action == "store":
                    if "st" in storedCards[qCard]:
                        storedCards[qSource]["st"] += [targetCard]
                    else:
                        storedCards[qSource]["st"] = [targetCard]
                elif action == "stop":
                    storedCards[targetCard]["s"] = "s"
                    notify("{} stops {}'s {}.".format(sourceCard, Card(targetCard).owner, Card(targetCard)))
                elif action == "block":
                    blockedList = storedCards[targetCard].get("b", [])
                    if params.get("ignoreBlockAssign", False): ## Certain cards, like events, won't unblock when they leave play
                        storedCards[targetCard]["b"] = blockedList + [None]
                    else:
                        storedCards[targetCard]["b"] = blockedList + [qSource]
                    notify("{} blocks {}'s {}.".format(sourceCard, Card(targetCard).owner, Card(targetCard)))
                elif action == "ready":
                    storedCards[targetCard]["s"] = "r"
                    if "b" in storedCards[targetCard]:
                        del storedCards[targetCard]["b"]
                    notify("{} readies {}'s {}.".format(sourceCard, Card(targetCard).owner, Card(targetCard)))
                elif action == "assign":
                    storedCards[targetCard]["s"] = "a"
                    notify("{} assigns {}'s {}.".format(sourceCard, Card(targetCard).owner, Card(targetCard)))
                elif action == "incapacitate":
                    storedCards[targetCard]["s"] = "i"
                    notify("{} incapacitates {}'s {}.".format(sourceCard, Card(targetCard).owner, Card(targetCard)))
                elif action == "destroy":
                    Card(targetCard).setController(Card(targetCard).owner)
                    del storedCards[targetCard]
                    remoteCall(Card(targetCard).owner, "remoteMove", [Card(targetCard), 'Discard'])
                    notify("{} destroys {}'s {}.".format(sourceCard, Card(targetCard).owner, Card(targetCard)))
                elif action == "mission":
                    Card(targetCard).setController(Card(targetCard).owner)
                    del storedCards[targetCard]
                    remoteCall(Card(targetCard).owner, "remoteMove", [Card(targetCard), 'Mission Pile'])
                    notify("{} puts {}'s {} on top of their Mission Pile.".format(sourceCard, Card(targetCard).owner, Card(targetCard)))
                elif action == "missionBottom":
                    Card(targetCard).setController(Card(targetCard).owner)
                    del storedCards[targetCard]
                    remoteCall(Card(targetCard).owner, "remoteMove", [Card(targetCard), 'Mission Pile', True])
                    notify("{} puts {}'s {} on bottom of their Mission Pile.".format(sourceCard, Card(targetCard).owner, Card(targetCard)))
                elif action == "complication":
                    storedCards[targetCard]["s"] = "c"
                    if "b" in storedCards[targetCard]:
                        del storedCards[targetCard]["b"]
                    notify("{} turns {}'s {} into a complication.".format(sourceCard, Card(targetCard).owner, Card(targetCard)))
        elif qAction == "skillChange":
            for targetCard in targets:
                card = Card(targetCard)
                if params.get("ignoreSource", False): ## True if the skill change is permanent after the source is gone
                    source = None
                else:
                    source = qSource
                skillBoosts = storedCards[targetCard].get(params["duration"], []) ##gets list of card's current skill changes for that duration
                for skillType in params["skill"]:
                    skillBoosts += [(skillDict[skillType], eval(params["value"]), source)]
                storedCards[targetCard][params["duration"]] = skillBoosts
        elif qAction == "tagSet":
            for targetCard in targets:
                if params.get("ignoreSource", False):
                    source = None
                else:
                    source = qSource
                storedCards[targetCard][params["tag"]] = (eval(params["value"]), source, params.get("duration", "p"))
    ## create notify messages for triggers requiring a target
    if queueLoop not in ["EMPTY", "BREAK"] and storedQueue == tempQueue:
        notify("{}: {} {} target.{}".format(
                storedQueue[0][2] if storedQueue[0][1] == "game" else "{}".format(Card(storedQueue[0][0])) + "'s " + storedQueue[0][2] + " ability",
                    Player(storedQueue[0][4]).name,
                       "chooses a" if storedQueue[0][5] else "must choose a",
                                 " (Press TAB to skip)" if storedQueue[0][5] else ""
                                            ))
    ## Update the variables if they have changed
    if storedCards != tempCards:
        setGlobalVariable("cards", str(storedCards))
    if storedQueue != tempQueue:
        setGlobalVariable("cardqueue", str(storedQueue))
    if storedPhase != tempPhase:
        setGlobalVariable("phase", str(storedPhase))


def cleanTable(group, x = 0, y = 0):
    mute()
    cleanup()

def cleanup():
    mute()
    if turnPlayer().hasInvertedTable():
        invert = True
    else:
        invert = False
    missionSkill, missionDiff, failcount, compcount, glyphwin, expwin, villwin = (0, 0, 0, 0, 0, 0, 0)
    alignvars = {"a": 0, "r": 0, "s": 0, "va": 0, "vr": 0, "vs": 0}
    global storedCards, storedQueue
    if len(storedQueue) > 0 and len(storedQueue[0]) > 0:
        actionQueue = queueTargets()
        if storedQueue[0][4] == turnPlayer()._id:
            actionColor = HeroActionColor
        elif storedQueue[0][4] == turnPlayer(False)._id:
            actionColor = VillainActionColor
        else:
            actionColor = None
    else:
        actionQueue = []
    #### Get the active mission's data
    if storedMission != None:
        mission = Card(storedMission[0])
        type = storedMission[1]
        status = storedMission[2]
        value = getStats(mission)[type]
#    #### Scan the table for cards that shouldn't belong there
#    for card in table:
#        if card._id not in storedCards and card != mission:
#            notify("ERROR: {}'s {} did not enter play properly.".format(card.controller, card))
    #### Start aligning the cards on the table
    for c in sorted(storedCards.items(), key=lambda x: x[1]["#"]):
        c = c[0]
        card = Card(c)
        status = storedCards[c]["s"]
        if card.controller == me:
            if card not in table: ## If for some reason the card is no longer on the table, move it back
                if status == "c":
                    card.moveToTable(0,0, True)
                else:
                    card.moveToTable(0,0)
            if c in actionQueue:  ## add highlight for cards in the action queue
                if card.highlight != actionColor:
                    card.highlight = actionColor
            else:
                if card.highlight != None:
                    card.highlight = None
        if status == "am": ## skip general alignment of the active mission since it's done later on
            continue
        if not cardActivity(card) == "inactive":
            if card.controller == me:
                if status == "c" and card.isFaceUp == True: ## fix face-up complications
                    card.isFaceUp = False
                if status != "c" and card.isFaceUp == False: ## fix face-down cards that are supposed to be face-up
                    card.isFaceUp = True
                if status in ["i", "g"] or "b" in storedCards[c]:  ## rotate all cards that are blocked, incapacitated, or glyphs
                    if card.orientation != Rot90:
                        card.orientation = Rot90
                else:
                    if card.orientation != Rot0:
                        card.orientation = Rot0
            if status == "g": ## Skip direct alignment of earned glyphs
                if card.controller == me:
                    for marker in card.markers:
                        if card.markers[marker] > 0:
                            card.markers[marker] = 0
                continue                
            #### Prep Failed Missions
            if status == "f" and card.Type == "Mission":
                xpos = (-79 if invert else -101) - 20 * failcount
                ypos = (-145 - 10 * failcount) if invert else (60 + 10 * failcount)
                failcount += 1
                if card.controller == me: 
                    if card.position != (xpos, ypos):
                        card.moveToTable(xpos, ypos)
                    for marker in card.markers:
                        if card.markers[marker] > 0:
                            card.markers[marker] = 0
            #### Prep Complications
            elif status == "c":
                xpos = (-79 if invert else -81) - 20 * compcount
                ypos = (70 + 10 * compcount) if invert else (-155 - 10 * compcount)
                compcount += 1
                missionDiff += 1
                if card.controller == me:
                    if card.position != (xpos, ypos):
                        card.moveToTable(xpos, ypos)
                    for marker in card.markers:
                        if card.markers[marker] > 0:
                            card.markers[marker] = 0
            else:
                cardSkills = getStats(card)
                #### Prep Hero cards
                if card.Type in heroTypes:
                    if status == "a":
                        countType = "a"
                        ypos = -98 if invert else 10
                        if storedMission != None and cardSkills[type] != "":
                            missionSkill += cardSkills[type]
                    elif status == "r":
                        countType = "r"
                        ypos = -207 if invert else 119
                    else:
                        countType = "s"
                        ypos = -316 if invert else 228
                #### Prep Villain Cards
                elif card.Type in villainTypes:
                    if status == "a":
                        countType = "va"
                        ypos = 10 if invert else -98
                        if storedMission != None and cardSkills[type] != "":
                            missionDiff += cardSkills[type]
                    elif status == "r":
                        countType = "vr"
                        ypos = 119 if invert else -207
                    else:
                        countType = "vs"
                        ypos = 228 if invert else -316
                xpos = alignvars[countType]
                invertxpos = alignvars[countType]
                #### Align the card
                glyphs = storedCards[c].get("g", [])
                invertxpos += 14*len(glyphs)
                if len(glyphs) > 0:
                    invertxpos += 12
                if card.orientation == Rot90:
                    invertxpos += 14 if len(glyphs) > 0 else 26
                if card.controller == me:
                    if card.position != (invertxpos if invert else xpos, ypos):
                        card.moveToTable(invertxpos if invert else xpos, ypos)
                if len(glyphs) > 0 and card.orientation == Rot90:
                        xpos += 14
                        invertxpos -= 14
                for glyphID in glyphs:
                    glyph = Card(glyphID)
                    expwin += int(glyph.experience)
                    glyphwin += 1
                    if glyph.controller == me:
                        if glyph.position != (invertxpos if invert else xpos, ypos):
                            glyph.moveToTable(invertxpos if invert else xpos, ypos)
                            glyph.sendToBack()
                    invertxpos -= 14
                    xpos += 14
                if len(glyphs) > 0:
                    xpos += 12
                if card.orientation == Rot90 and len(glyphs) == 0:
                    alignvars[countType] = xpos + 90
                else:
                    alignvars[countType] = xpos + 64
                #### Add skill markers on the card to show its current values
                if card.controller == me and card.Type != "Mission":
                    if card.isFaceUp:
                        for cardSkill in ["Culture", "Science", "Combat", "Ingenuity"]:
                            skillValue = cardSkills[cardSkill]
                            if skillValue == None:
                                skillValue = 0
                            if card.markers[markerTypes[cardSkill]] != skillValue:
                                card.markers[markerTypes[cardSkill]] = skillValue
        #### Align inactive cards
        else:
            if card.controller == me:
                if card.position != (-197, -44):
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
            if mission.position != (-81 if invert else -105, -45 if invert else -44):
                mission.moveToTable(-81 if invert else -105, -45 if invert else -44)
            if mission.orientation != Rot90:
                mission.orientation = Rot90
            missionDiff += value
            mission.markers[markerTypes["skill"]] = missionSkill
            mission.markers[markerTypes["diff"]] = missionDiff
    #### Determine victory conditions
    me.counters["Glyph Win"].value = glyphwin
    me.counters["Experience Win"].value = expwin
    for villain in me.piles["Villain Score Pile"]:
        villwin += int(villain.cost)
    me.counters["Villain Win"].value = villwin
    if storedPhase > 3:
        if glyphwin >= 7:
            notify("{} has won through Glyph Victory (7 glyphs.)".format(me))
        if expwin >= storedVictory:
            notify("{} has won through Experience Victory ({} points.)".format(me, expwin))
        if villwin >= storedVictory:
            notify("{} has won through Villain Victory ({} points.)".format(me, villwin))

def playComplication(card, x = 0, y = 0):
    mute()
    if myTurn():
        whisper("Cannot play {} as the Hero player.".format(card))
        return
    global storedPhase
    phase = storedPhase
    if phase != 6: ## mis.main
        whisper("Cannot play {}: It's not the main mission phase.".format(card))
        return
    if not myPriority():
        whisper("Cannot play {}: You don't have priority.".format(card))
        return
    global storedQueue
    if len(storedQueue) > 0:
        whisper("Cannot play {}: There are abilities that need resolving.".format(card))
        return
    global storedCards
    cost = 1 ## base cost for complication
    for c in storedCards:
        if storedCards[c]["s"] == "c":
            cost += 1  ## Add 1 to the cost for each complication already in play
        else:
            for (actionType, params) in scriptsDict.get(Card(c).model, {}).get("onGetComplicationCost", []):
                if actionType == "costChange":
                    if checkConditions(Card(c), params.get("condition", {}), card._id)[0] == True:
                        cost += eval(params["value"])
    if me.Power < cost:
        whisper("You do not have enough Power to play that as a complication.")
        return
    card.moveToTable(0,0, True)
    setGlobalVariable("cards", str(storeNewCards(card, {"s": "c"}, storedCards)))
    card.peek()
    me.Power -= cost
    notify("{} plays a complication.".format(me))
    setGlobalVariable("priority", str((turnPlayer()._id, False)))

def remoteMove(card, pile, bottom = False):
    mute()
    if bottom == True:
        card.moveToBottom(card.owner.piles[pile])
    else:
        card.moveTo(card.owner.piles[pile])

def assign(card, x = 0, y = 0):
    mute()
    if cardActivity(card) == "inactive":
        whisper("You cannot play {} during your {}turn.".format(card, "" if myTurn() else "opponent's "))
        return
    if card.Type not in ["Adversary", "Team Character", "Support Character"]:
        whisper("Cannot assign {}: It is not an assignable card type.".format(card))
        return
    global storedPhase
    phase = storedPhase
    if phase != 6: ## mis.main
        whisper("Cannot assign {}: It's not the main mission phase.".format(card))
        return
    if not myPriority():
        whisper("Cannot assign {}: You don't have priority.".format(card))
        return
    if storedMission == None:
        whisper("Cannot assign {} as there is no active mission.".format(card))
        return
    global storedQueue
    if len(storedQueue) > 0:
        whisper("Cannot assign {}: There are abilities that need resolving.".format(card))
        return
    mission, type, value, status = storedMission
    if card.properties[type] == None or card.properties[type] == "":
        whisper("Cannot assign {}: Does not match the active mission's {} skill.".format(card, type))
        return
    global storedCards
    if card._id in storedCards:
        if storedCards[card._id]["s"] != "r":
            whisper("Cannot assign: {} is not Ready.".format(card))
            return
        storedCards[card._id]["s"] = "a"
        setGlobalVariable("cards", str(storedCards))
        setGlobalVariable("priority", str((turnPlayer(False)._id, False)))
        notify("{} assigns {}.".format(me, card))
    else:
        notify("ERROR: {} not in cards global dictionary.".format(card))

def checkScripts(card, actionType):
    mute()
    if card.name in scriptsDict:
        cardScripts = scriptsDict[card.name]
        if actionType in cardScripts:
            script = cardScripts[actionType]
            
    return None


#---------------------------------------------------------------------------
# Table group actions
#---------------------------------------------------------------------------

def endquest(group, x = 0, y = 0):
    mute()
    myCards = (card for card in table
        if card.controller == me)
    for card in myCards:
        card.highlight = None
        card.markers[markerTypes["block"]] = 0
    notify("{} is ending the quest.".format(me))

def endturn(group, x = 0, y = 0):
    mute()
    myCards = (card for card in table
        if card.controller == me)
    for card in myCards:
        card.markers[markerTypes["stop"]] = 0
        card.markers[markerTypes["block"]] = 0
        card.highlight = None
        if card.orientation == rot180:
          card.orientation = rot90
          card.markers[markerTypes["stop"]] = 1
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
    global storedCards
    storedCards[card._id]["s"] = "r"
    if "b" in storedCards[card._id]:
        del storedCards[card._id]["b"]
    setGlobalVariable("cards", str(storedCards))
    notify("{} readies {}.".format(me, card))

def block(card, x = 0, y = 0):
    mute()
    global storedCards
    storedCards[card._id]["b"] = [None]
    setGlobalVariable("cards", str(storedCards))
    notify("{} blocks {} from the quest.".format(me, card))

def stop(card, x = 0, y = 0):
    mute()
    global storedCards
    storedCards[card._id]["s"] = "s"
    setGlobalVariable("cards", str(storedCards))
    notify("{} stops {}.".format(me, card))

def incapacitate(card, x = 0, y = 0):
    mute()
    global storedCards
    storedCards[card._id]["s"] = "i"
    setGlobalVariable("cards", str(storedCards))
    notify("{} KO's {}.".format(me, card))

def destroy(card, x = 0, y = 0):
    mute()
    global storedCards
    if card._id in storedCards:
        del storedCards[card._id]
    setGlobalVariable("cards", str(storedCards))
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
    card.markers[markerTypes["counter"]] += 1

def removeMarker(card, x = 0, y = 0):
    mute()
    addmarker = markerTypes["counter"]
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