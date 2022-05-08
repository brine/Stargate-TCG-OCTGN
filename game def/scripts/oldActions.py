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
    if not getSetting("debugMode", False):
        return
    if card.model in scriptsDict:
        txt = " (Scripted)"
    whisper("{}~{}{}".format(card, card.model, txt))

def counterChange(args):
    mute()
    if args.scripted:
        return
    if getSetting("debugMode", False):
        return
    if args.player == me:
        args.counter.value = args.value

def debugQueue(group, x = 0, y = 0):
    mute()
    if not getSetting("debugMode", False):
        return
    resolveQueue()

def debugToggle(group, x = 0, y = 0):
    mute()
    debug = getSetting("debugMode", False)
    if debug == False:
        notify("{} enables Debug Mode.".format(me))
        setSetting("debugMode", True)
    else:
        notify("{} disables Debug Mode.".format(me))
        setSetting("debugMode", False)

def turnPassedOverride(args):
    mute()

def moveCardsOverride(args):
    mute()
    if not getSetting("debugMode", False):
        return
    for i in range(0, len(args.cards)):
        card = args.cards[i]
        if args.toGroups[i] == table:
            card.moveToTable(args.xs[i], args.ys[i], not args.faceups[i])
            card.index = args.indexs[i]
        else:
            card.moveTo(args.toGroups[i], args.indexs[i])

def moveCardsEvent(args):
    mute()
    if getSetting("debugMode", False):
        return
    if args.player != me:
        return
    count = 0
    for card in args.cards:
        if args.fromGroups[count] == table: ## Return cards to their original position on the table
            card.moveToTable(args.xs[count],args.ys[count], not args.faceups[count])
            card.index = args.indexs[count]
            if args.faceups[count] == False:
                card.peek()
        elif args.fromGroups[count] == me.hand and args.toGroups[count] == me.hand: ## Allow re-arranging of the hand
            return
        else: ## Return card to itis original pile.
            card.moveTo(args.fromGroups[count], args.indexs[count])
            notify("Overriding card movement...")
        count += 1

def resetVars(group, x = 0, y = 0):
    mute()
    for p in getPlayers():
        remoteCall(p, 'reloadLocalVars', [])

def nextPhaseQueue():
    return ([], "game", "nextPhase", 0, turnPlayer()._id, False, None)

def reloadLocalVars(args = None):
    mute()
    if args == None or args.player == me:
        #### Prep initial variables
        global storedCards, storedTurnPlayer, storedPriority, storedVictory, storedOppVictory, storedMission, storedGameStats, storedQueue
        storedMission = eval(getGlobalVariable("activemission"))
        storedTurnPlayer = int(getGlobalVariable("turnplayer"))
        storedPriority = eval(getGlobalVariable("priority"))
        storedGameStats = eval(getGlobalVariable("gameStats"))
        storedCards = eval(getGlobalVariable("cards"))
        storedQueue = eval(getGlobalVariable("cardqueue"))
        if len(getPlayers()) > 1:
            storedVictory = int(getPlayers()[1].getGlobalVariable("victory"))
        else:
            storedVictory = 0
        storedOppVictory = int(me.getGlobalVariable("victory"))

def registerTeam(args = None):
    mute()
    deleteDeck = False
    reloadLocalVars()
    global storedCards, storedVictory, storedOppVictory, storedQueue
    setupStep = int(getGlobalVariable("setupStep"))
    if args != None and args.player != me:  #only execute this event if its your own deck
        return
    safeCards = eval(me.getGlobalVariable("loadedCards"))
    #### The game only works with 2 players, so anyone else loading a deck will have their cards deleted
    if currentPhase()[1] > 0: ## pre.1load, pre.2load, or endgame
        whisper("cannot load deck -- game has already begun.")
        deleteDeck = True
    elif setupStep > 1:
        whisper("cannot load deck -- decks have already been loaded.")
        deleteDeck = True
    #### Delete loaded deck if a deck has already been loaded
    elif len(safeCards) != 0:
        whisper("cannot load deck -- you have already loaded a deck.")
        deleteDeck = True
    #### Verify deck contents
    else:
        whisper("~~~VALIDATING DECKS~~~")
        if len(me.Team) != 4:
            whisper("Team Error: You need exactly 4 Team Characters. ({} of 4)".format(len(me.Team)))
            deleteDeck = True
        deckCount = {}
        storedOppVictory = 0
        for c in me.Team:
            deckCount[c.Name] = deckCount.get(c.Name, 0) + 1
            storedOppVictory += int(c.Cost)  #add the card's cost to the victory total
        for x in deckCount:
            if deckCount[x] > 1:
                whisper("Team Error: You can only have one {} in your Team. ({} of 1)".format(x, deckCount[x]))
                deleteDeck = True
        heroCount = sum(1 for c in me.Deck if c.Type in heroTypes)
        if heroCount < 20:
            whisper("Deck Error: You need at least 20 Hero cards in your deck. ({} of 20)".format(heroCount))
            deleteDeck = True
        villainCount = sum(1 for c in me.Deck if c.Type in villainTypes)
        if villainCount < 20:
            whisper("Deck Error: You need at least 20 Villain cards in your deck. ({} of 20)".format(villainCount))
            deleteDeck = True
        for c in me.Deck:
            deckCount[c.Name] = deckCount.get(c.Name, 0) + 1
        for x in deckCount:
            if deckCount[x] > 3:
                whisper("Deck Error: You can have at most 3 {} in your Deck. ({} of 3)".format(x, deckCount[x]))
                deleteDeck = True
        if len(me.piles["Mission Pile"]) != 12:
            whisper("Mission Pile Error: You need exactly 12 Missions. ({} of 12)".format(len(me.piles["Mission Pile"])))
            deleteDeck = True
        deckCount = {}
        for c in me.piles["Mission Pile"]:
            deckCount[c.Name] = deckCount.get(c.Name, 0) + 1
        for x in deckCount:
            if deckCount[x] > 1:
                whisper("Mission Error: You can only have one {} in your Mission Pile. ({} of 1)".format(x, deckCount[x]))
                deleteDeck = True
        deckCount = {}
        for c in me.piles["Mission Pile"]:
            for stat in ["Culture", "Science", "Ingenuity", "Combat"]:
                if c.properties[stat] != "":
                    deckCount[stat] = deckCount.get(stat, 0) + 1
        for x in deckCount:
            if deckCount[x] != 3:
                whisper("Mission Error: You need exactly 3 {} missions in your Mission Pile. ({} of 3)".format(x, deckCount[x]))
                deleteDeck = True
    if deleteDeck == True:
        for group in [me.Deck, me.piles["Mission Pile"], me.Team]:
            for c in group:
                if c._id not in safeCards:
                    c.delete()
        return
    whisper("~~~DECKS ARE LEGAL~~~")
    #### Store the loaded card IDs
    me.setGlobalVariable("loadedCards", str([[x._id for x in me.Deck],[x._id for x in me.Team],[x._id for x in me.piles["Mission Pile"]]]))
    #### Add team to storedCards dict
    for card in me.Team:
        storedCards = storeNewCards(card, {"s":"r"}, storedCards)
    setGlobalVariable("cards", str(storedCards))
    me.Deck.shuffle()
    me.piles["Mission Pile"].shuffle()
    me.setGlobalVariable("victory", str(storedOppVictory)) #Stores your opponent's victory total
    
    if setupStep == 0: ##pre.1load
        setGlobalVariable("setupStep", "1")
    elif setupStep == 1: ##pre.2load
        setGlobalVariable("setupStep", "2")


def playerGlobalVarChanged(args):
    mute()
    if args.name == "victory":
        if args.player != me:
            global storedVictory
            storedVictory = int(args.value)
            return
        else:
            global storedOppVictory
            storedOppVictory = int(args.value)
            return

def phaseChanged(args):
    mute()
    phase = currentPhase()[1]
    global storedQueue, storedCards, storedGameStats, storedMission
    if phase == 0:
        return
    #### Entering Power Phase
    elif phase == 1: ## pow.main
        power = 3 + len([c for c in storedCards if cardActivity(Card(c)) == "glyph"])
        me.Power = power
        notify("{} gained {} power.".format(me, power))
        #### Check for power phase script triggers
        if myTurn():
            triggerQueue = phaseTriggers("onPowerEnd", None)
            if len(triggerQueue) == 0:
                setPhase(2) ## mis.start
            else:
                storedQueue = triggerQueue + [nextPhaseQueue()] + storedQueue
                setGlobalVariable("cardqueue", str(storedQueue))
    #### Setting up a new Mission
    elif phase == 2: ## mis.start
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
    #### Resolving the current mission
    elif phase == 4: ## mis.res
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
            setPhase(5) ## mis.sucfail
    elif phase == 5: ## mis.sucfail
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
                if cardActivity(card) != "inactive" and storedCards[c]["s"] == "a":  # find assigned characters
                    if card.Type in heroTypes:
                        storedCards[c]["p"] = True
                    if storedCards[c].get("r" + storedMission[2], False) == False and hasTriggers(card, "on" + status, card._id):
                        if card.controller == me:
                            heroTriggers.append(c)
                        else:
                            villainTriggers.append(c)
            setGlobalVariable("cards", str(storedCards))
            if hasTriggers(mission, "on" + status, mission._id): ## Add the mission's trigger if it has one
                heroTriggers.append(mission._id)
            newQueue = []
            if len(heroTriggers) > 0: ## attach hero triggers to queue
                newQueue += [(heroTriggers, "trig", "on" + status, 0, turnPlayer()._id, False, None)]
            if len(villainTriggers) > 0: ## attach villain triggers to queue
                newQueue += [(villainTriggers, "trig", "on" + status, 0, turnPlayer(False)._id, False, None)]
            if len(newQueue) == 0: ## skip all this junk if there's no actual triggers
                setPhase(6) ## mis.adv
            else:
                if len(heroTriggers) > 0:
                    notify("{} has {} triggers to resolve.".format(me, status))
                else:
                    notify("{} has {} triggers to resolve.".format(turnPlayer(False), status))
                storedQueue = newQueue + [nextPhaseQueue()] + storedQueue
                setGlobalVariable("cardqueue", str(storedQueue))
    elif phase == 6: ## mis.adv
        if myTurn():
            if storedMission == None:
                notify("ERROR: There is no registered active mission!")
                return
            #### First, stop all hero characters assigned to the mission.
            triggers = []
            for c in storedCards:
                card = Card(c)
                if cardActivity(card) != "inactive":
                    if storedCards[c]["s"] == "a" and card.controller != me and card.Type == "Adversary": ## add assigned adversaries to the trigger list
                        triggers.append(c)
                    elif storedCards[c]["s"] == "a" and card.controller == me and card.Type in heroTypes: ## stops all assigned hero cards
                        storedCards[c]["s"] = "s"
#                        storedCards[c]["p"] = True
            setGlobalVariable("cards", str(storedCards))
            if len(triggers) == 0:
                ## skip all this junk
                setPhase(7) ## mis.gly
            else:
                notify("{} has adversaries to revive.".format(turnPlayer(False)))
                storedQueue = [(triggers, "game", "revive", 0, turnPlayer(False)._id, False, None)] + [nextPhaseQueue()] + storedQueue
                setGlobalVariable("cardqueue", str(storedQueue))
    elif phase == 7: ## mis.gly
        #### Destroy all complications and obstacles
        if not myTurn():
            heroEndTriggers = []
            villainEndTriggers = []
            triggers = []
            for c in storedCards.keys():
                card = Card(c)
                if cardActivity(card) != "inactive":
                    ##find all previously assigned characters as glyph targets
                    if "p" in storedCards[c]: ##previously assigned characters
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
 #               setGlobalVariable("activemission", "None")  ## Empties the active mission
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
                setPhase(8) ## mis.end
            else:
                setGlobalVariable("cardqueue", str(newQueue + [nextPhaseQueue()] + storedQueue))
    elif phase == 8: ## mis.end
        if myTurn():
            setGlobalVariable("activemission", "None")
            failCount = len(storedGameStats["fm"]) ##count the number of failed missions so far
            if 'cp' in storedGameStats: ## clear restrictions on playing cards
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
                setPhase(2) ## mis.start
            else: ## Skip to Debrief Phase
                notify(" ~~ {}'s Debrief Phase ~~ ".format(me))
                newQueue = phaseTriggers("onDebrief", None)
                if len(newQueue) == 0:
                    setPhase(9) ## deb.start
                else:
                    setGlobalVariable("cardqueue", str(newQueue + [nextPhaseQueue()] + storedQueue))
    elif phase == 9: ## deb.start
        if myTurn():
            ## Clear the successful and failed missions
            failedMissions = storedGameStats["fm"]
            for mission in failedMissions:
                if Card(mission) not in table:
                    failedMissions.remove(mission)
            storedGameStats["fm"] = []
            storedGameStats["sm"] = []
            if 'cp' in storedGameStats: #clear restrictions on playing cards
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
                setPhase(10) ## deb.ref
    elif phase == 10: ## deb.ref
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
                setPhase(11) ## deb.end
            else:
                storedQueue = newQueue + [nextPhaseQueue()] + storedQueue
                setGlobalVariable("cardqueue", str(storedQueue))
    elif phase == 11: ## deb.end
        if myTurn():
            notify("{}'s turn ends.".format(me))
            nextPlayer = turnPlayer(False)
#                nextPlayer.setActive()
            setActivePlayer(nextPlayer)
            setGlobalVariable("turnplayer", str(nextPlayer._id))
            if me.isInverted:
                table.board = ""
            else:
                table.board = "invert"
            notify(" ~~ {}'s Power Phase ~~ ".format(nextPlayer))
            setPhase(1) ## pow.main
    

def globalVarChanged(args):
    mute()
    varName = args.name
    newValue = args.value
    global storedQueue, storedCards, storedGameStats, storedMission
    #### update python global variables
    if varName == "turnplayer":
        global storedTurnPlayer
        storedTurnPlayer = int(newValue)
    elif varName == "cards":
        storedCards = eval(newValue)
        if currentPhase()[1] > 0:
            cleanup()
    elif varName == "activemission":
        storedMission = eval(newValue)
    elif varName == "gameStats":
        storedGameStats = eval(newValue)
    elif varName == "priority":
        global storedPriority
        storedPriority = eval(newValue)
    elif varName == "cardqueue":
        if currentPhase()[1] < 11:
            storedQueue = eval(newValue)
            if len(storedQueue) > 0 and storedQueue[0][4] == me._id:
                resolveQueue()
            cleanup()
    #### Phase Changes
    elif varName == "setupStep":
        setupStep = int(newValue)
        #### opponent stops a character for first turn
        if setupStep == 2:    
            for card in me.Team:
                card.moveToTable(0,0)
            notify("{} registers their Team ({} points).".format(me, storedOppVictory))
            if Player(1) == me:
                opponent = getPlayers()[1]
                if storedVictory > storedOppVictory:
                    startingPlayer = me
                    stopPlayer = opponent
                    notify("{} will play first.".format(me))
                elif storedVictory < storedOppVictory:
                    startingPlayer = opponent
                    stopPlayer = me
                    notify("{} will play first.".format(startingPlayer))
                else:
                    ##randomly determine in the event of a tie
                    if rnd(1,2) == 1:
                        startingPlayer = me
                        stopPlayer = opponent
                        notify("{} will play first, chosen randomly.".format(me))
                    else:
                        startingPlayer = opponent
                        stopPlayer = me
                        notify("{} will play first, chosen randomly.".format(opponent))
                setGlobalVariable("turnplayer", str(startingPlayer._id))
                if startingPlayer.isInverted:
                    table.board = "invert"
                else:
                    table.board = ""
                notify("{} will choose a team character to Stop.".format(stopPlayer))
                oppTeam = [c for c in storedCards if "Team Character" in Card(c).Type and not Card(c).controller == stopPlayer]
                setGlobalVariable("cardqueue", str([(oppTeam, "game", "stopCard", 0, stopPlayer._id, False, None), ([], "game", "setupStop", 0, startingPlayer._id, False, None)]))
                setGlobalVariable("setupStep", "3")
        elif setupStep == 4: ## "pre.1mul
            fillHand(8)
            if myTurn():
                choice = askChoice("Do you want to keep this hand?\nTo view your hand, close this window, then press TAB when ready.", ["Keep", "New Hand"])
                if choice == 1:
                    notify("{} keeps their hand.".format(me))
                    setGlobalVariable("setupStep", "5") ## pre.2mul
                elif choice == 2:
                    for c in me.hand:
                        c.moveTo(me.Deck)
                    me.Deck.shuffle()
                    fillHand(8)
                    notify("{} draws a new hand.".format(me))
                    setGlobalVariable("setupStep", "5") ## pre.2mul
        #### Second Player Mulligan
        elif setupStep == 5: ## pre.2mul
            if not myTurn():
                choice = askChoice("Do you want to keep this hand?\To view your hand, close this window, then press TAB when ready.", ["Keep", "New Hand"])
                if choice == 1:
                    notify("{} keeps their hand.".format(me))
                    setGlobalVariable("setupStep", "6")
                    setPhase(1)
                elif choice == 2:
                    for c in me.hand:
                        c.moveTo(me.Deck)
                    me.Deck.shuffle()
                    fillHand(8)
                    notify("{} draws a new hand.".format(me))
                    setGlobalVariable("setupStep", "6")
                    setPhase(1)

def endGame():
    setPhase(0)
    me.setGlobalVariable("victory", "0")
    setGlobalVariable("turnplayer", "1")
    setGlobalVariable("cards", "{}")
    setGlobalVariable("cardqueue", "[]")
    setGlobalVariable("activemission", "None")
    setGlobalVariable("gameStats", "{ 'fm':[], 'sm':[] }")
    setGlobalVariable("priority", "0")
    num = askChoice(
            "The game has now ended. Please choose an option:",
            ["Reload this deck", "Choose a new deck", "Continue game"]
            )
    if num in [1, 2]:
        for c in table:
            if c.controller == me:
                c.delete()
        for c in me.hand:
            c.delete()
        for c in me.discard:
            c.delete()
        for c in me.deck:
            c.delete()
        for c in me.team:
            c.delete()
        for c in me.piles["Mission Pile"]:
            c.delete()
        for c in me.piles["Villain Score Pile"]:
            c.delete()
        if num == 1:
            p = eval(me.getGlobalVariable("loadedCards"))
            for c in p[0]:
                me.deck.create(Card(c).model, 1)
            for c in p[1]:
                me.Team.create(Card(c).model, 1)
            for c in p[2]:
                me.piles["Mission Pile"].create(Card(c).model, 1)
            me.setGlobalVariable("loadedCards", "[]")
            registerTeam()
        else:
            me.setGlobalVariable("loadedCards", "[]")
    else:
        confirm("To start a new game, select 'reset' in the 'game' menu.")
    return

def doubleClick(args):
    mute()
    card = args.card
    ##TODO: Allow discard queue triggers to target cards in your hand (currently only works for table)
    global storedQueue, storedCards
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
    if currentPhase()[1] == 3: ## mis.main
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
        if not checkCosts(card, "onGetAssignCost", card._id):
            return 
        #### check if the card is being blocked
        blockedList = storedCards[card._id].get("b", [])
        for blocker in blockedList:
            if blocker != None and blocker not in storedCards: ## If the blocker isn't in play anymore, remove it from the list.
                blockedList.remove(blocker)
        if len(blockedList) > 0:
            whisper("Cannot assign: {} is being blocked{}.".format(card, "" if blockedList == [None] else " by " + ", ".join(["{}".format(Card(x)) for x in blockedList if x != None])))
            return
        storedQueue = phaseTriggers("onGetAssignCost", card._id) + [([card._id], "game", "assignCard", 0, me._id, False, None)] + phaseTriggers("onAssign", card._id) + storedQueue ##TODO move onAssign phaseTriggers to resolveQueue?
        setGlobalVariable("priority", str((getPlayers()[1]._id, False)))
        setGlobalVariable("cardqueue", str(storedQueue))

def playCard(card, x = 0, y = 0):
    mute()
    if currentPhase()[1] != 2: ## mis.main
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
    if not checkCosts(card, "onGetPlayCost", card._id):
        return
    #### Pay power cost to play card
    costModifier = int(card.Cost)
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
                                costModifier += eval(params["value"])
                        elif checkConditions(card, params["trigger"], c)[0]:
                            if params["trigger"].get("ignoreSelf", False) and c == card._id:
                                continue
                            costModifier += eval(params["value"])
    if costModifier > me.Power:
        whisper("You do not have enough Power to play that.")
        return
    me.Power -= costModifier
    card.moveTo(me.Team)
    storedQueue = triggerScripts(card, "onGetPlayCost", card._id) + phaseTriggers("onGetPlayCost", card._id) + [([card._id], "game", "playCard", 0, me._id, False, None)] + storedQueue
    setGlobalVariable("priority", str((getPlayers()[1]._id, False)))
    setGlobalVariable("cardqueue", str(storedQueue))

def activateAbility(card, x = 0, y = 0):
    mute()
    if not myPriority():
        whisper("Cannot activate {}'s ability: You don't have priority.".format(card))
        return
    if currentPhase()[1] != 2: ## mis.main
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
        abilityTrigger = "1"
    else:
        abilityTrigger = str(askChoice("Choose an ability:", abilityText, []))
    #### Check for additional costs to play the ability
    if not checkCosts(card, "onGetAbility" + abilityTrigger + "Cost", card._id):
        return
    storedQueue = phaseTriggers("onGetAbility" + abilityTrigger + "Cost", card._id) + phaseTriggers("onAbility" + abilityTrigger, card._id) + storedQueue
    setGlobalVariable("priority", str((getPlayers()[1]._id, False)))
    setGlobalVariable("cardqueue", str(storedQueue))

def checkCosts(origCard, type, sourceId):  ## This function verifies if all costs can be met, but doesn't actually apply the costs
    mute()
    global storedCards
    cardList = [x for x in storedCards if cardActivity(Card(x)) in ["active", "active mission"] and type in scriptsDict.get(Card(x).model, [])]
    if origCard in me.hand: #for play costs, the original card is still in hand
        cardList += [origCard._id]
    for c in cardList:
        card = Card(c)
        if type not in scriptsDict.get(card.model, []):
            continue
        for (actionType, params) in scriptsDict[card.model][type]:
            if actionType == "costChange":
                continue
            if card == origCard: ## if this is the original card
                conditionCheck = checkConditions(card, params.get("condition", {}), None)
                if conditionCheck[0] == False:
                    whisper("Cannot continue: {} does not have the required {}.".format(card, conditionCheck[1]))
                    return False
            elif "trigger" in params:
                conditionCheck = checkConditions(origCard, params.get("trigger", {}), None)
                if conditionCheck[0] == False:
                    continue
            else:  ## skip if the card doesn't trigger
                continue
            if actionType == "confirm":
                if not confirm("{}".format(params["message"])):
                    return False
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
                if len(targets) < eval(params.get("count", "1")):
                    whisper("Cannot continue: there are no valid targets for {}.".format(card))
                    return False
                continue
            if actionType == "moveCard":
                if params["player"] == "hero":
                    player = turnPlayer()
                else:
                    player = turnPlayer(False)
                if "min" in params["to"] and len(eval(params["target"]["group"])) < eval(params["to"]["min"]):
                    whisper("Cannot continue: {} does not have enough cards in their {}.".format(player, eval(params["to"]["group"]).name))
                    return False
    return True

def passturn(group, x = 0, y = 0): 
    mute()
    #### Pass on skippable triggers in the queue
    global storedQueue
    if len(storedQueue) > 0: ## if the queue's not empty
        resolveQueue(skip = True)
        return
    if currentPhase()[1] == 3: ## mis.main
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
            setPhase(4) ## mis.res
    else:
        setupStep = int(getGlobalVariable("setupStep"))
        if setupStep == 4:
            setGlobalVariable("setupStep", "4")
        elif setupStep == 5:
            setGlobalVariable("setupStep", "5")

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
#    if card in card.owner.Team:
#        return "inactive"
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
    if myTurn():
        if status == "c":
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
        if status == "c":
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

def getGlyphTarget(glyphId):
    mute()
    global storedCards
    for c in storedCards:
        if glyphId in storedCards[c].get("g", []):
            return c
    return None

def getStats(card):
    mute()
    global storedCards
    baseSkills = {"Culture": None, "Science": None, "Combat": None, "Ingenuity": None, "Difficulty": None}
    allSkillsValue = 0
    ## Set the base skill from the printed card
    for baseSkill in baseSkills.keys():
        if card.properties[baseSkill] not in ["?", ""]:
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
            if Card(qCard).model == None:
                return []
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
        if cardActivity(card) in ["active", "active mission"] and hasTriggers(card, triggerName, sourceId):
            if card.controller == me:
                heroTriggers.append(c)
            else:
                villainTriggers.append(c)
    if len(heroTriggers) > 0: ## attach hero triggers to queue
        newQueue += [(heroTriggers, "trig", triggerName, 0, turnPlayer()._id, skippable, sourceId)]
    if len(villainTriggers) > 0: ## attach villain triggers to queue
        newQueue += [(villainTriggers, "trig", triggerName, 0, turnPlayer(False)._id, skippable, sourceId)]
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
            if "trigger" in params:
                if params["trigger"] == "self":
                    if card._id == sourceId:
                        return True
                else:
                    if checkConditions(Card(sourceId), params["trigger"], card._id)[0]:
                        return True
    return False

def checkConditions(card, conditions, sourceId):
    mute()
    global storedCards, storedMission
    if card._id in storedCards and cardActivity(card) == "inactive":
        return (False, "Inactive")
    glyphCheck = conditions.get("glyph", [])
    if glyphCheck == "None":
        if len(storedCards[card._id].get("g", [])) > 0:
            return (False, "Glyph")
    elif glyphCheck != [] and not hasGlyph(storedCards[card._id].get("g", []), eval(glyphCheck)):
        return (False, "Glyph")
    statusCheck = conditions.get("status", [])
    if statusCheck != [] and storedCards[card._id]["s"] not in statusCheck:
        return (False, "Status")
    skillCheck = conditions.get("skill", None)
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
    if not eval(conditions.get("custom", 'True')):
        return (False, "State")
    return (True, None)

def triggerScripts(card, type, sourceId): ## note this function assumes that the card scripts exist, doesn't do any verifying
    mute()
    if not hasTriggers(card, type, sourceId):
        return []
    ## Check to see if all costs are possible to pay
    queue = []
    scriptIndex = -1
    for (actionType, params) in scriptsDict[card.model][type]:
        scriptIndex += 1
        ## Verify that the condition is met
        if checkConditions(card, params.get("condition", {}), sourceId)[0] == False:
            continue #### Skip this trigger if the condition wasn't met    
        if params.get("player", "hero" if myTurn() else "enemy") == "hero":
            player = turnPlayer()._id
        else:
            player = turnPlayer(False)._id
        queue.append((card._id, scriptIndex, type, 0, player, params.get("skippable", False), sourceId))
    return queue

def resolveQueue(target = None, skip = False):
    global storedQueue, storedCards, storedGameStats
    ## Set the initial values of the queue and card database, to compare later on
    tempQueue = eval(str(storedQueue))
    tempCards = eval(str(storedCards))
    nextPhase = False
    nextStep = False
    tempGameStats = eval(str(storedGameStats))
    queueLoop = True
    while queueLoop == True:
        if len(storedQueue) == 0:
            queueLoop = "EMPTY"
            continue
        (qCard, qTrigger, qType, qCount, qPriority, qSkippable, qSource) = storedQueue[0] ## split apart the queue tuple
        if qSource == None:
            sourceCard = Player(qPriority).name
        else:
            sourceCard = Card(qSource)
        if Player(qPriority) != me: ## Skip if you don't have priority during the current card queue
            queueLoop = "BREAK"
            continue
        if skip == True:
            if qSkippable == True:
                notify("{} skips {}'s {} trigger.".format(me, sourceCard, qType))
                del storedQueue[0]
                skip = False
            else:
                whisper("Cannot skip this trigger.")
                queueLoop = "BREAK"
            continue
        if qTrigger == "trig":  ## These hold cards which trigger on specific situations
            qTargets = [c for c in qCard if c in storedCards or c == qSource] ## the list of valid targets for that trigger
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
            if not checkCosts(Card(target), qType + "Cost", qSource):
                whisper("Cannot pay cost for {}'s {} ability.".format(Card(target), qType))
                target = None
                continue
            storedQueue = phaseTriggers(qType + "Cost", qSource) + triggerScripts(Card(target), qType, qSource) + storedQueue ## Add the new triggers to the queue
            target = None
            continue
        elif qTrigger == "game":  ## Game engine scripts, non-card specific
            qAction, params = scriptsDict["game"][qType][0] ## Get card script data for the queue trigger
            qTargets = queueTargets() ## Valid targets are always listed in game engine queues
        else: ## Card-specific triggers
            qAction, params = scriptsDict[Card(qCard).model][qType][int(qTrigger)] ## Get card script data for the queue trigger
            if checkConditions(Card(qCard), params.get("condition", {}), qSource)[0] == False: ##Skip this trigger if the condition wasn't met
                whisper("ERROR #25")
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
        target = None  ## remove the active target so the engine doesn't re-target the same card again
        ## Announce that the triggers are resolving
        if qSource != None and not ('target' in params and len(qTargets) == 0):
            notify("{} is resolving {}'s {} ability.".format(me, Card(qSource), qType)) ##TODO: Needs to be source of the ability
        ## Specialized actions with different queue interactions
        if qAction == "moveCard":
            del storedQueue[0]
            targetCheck = params["target"]
            fromGroup = eval(targetCheck["group"])
            ## subdivide the group if necessary
            if 'index' in targetCheck:
                groupList = [fromGroup[eval(targetCheck["index"])]]
            elif 'top' in targetCheck:
                groupList = list(fromGroup[:eval(targetCheck["top"])])
            elif 'bottom' in targetCheck:
                groupList = list(fromGroup[-eval(targetCheck["bottom"]):])
            else:
                groupList = fromGroup
            skippable = params.get("skippable", False)
            skillCheck = targetCheck.get("skill", None)
            typeCheck = targetCheck.get("type", [])
            targets = [c for c in groupList
                if (typeCheck == [] or c.Type in typeCheck)
                and (skillCheck == None or getStats(c)[skillCheck] != None)
                ]
            ## request permission to view piles that are normally hidden from that player
            if fromGroup.name in ["Deck", "Mission Pile"]:
                if not skippable: #when a choice is required
                    if not confirm("Do you want to search your {} for a card?\n\nSource: {}\n{}".format(fromGroup.name, Card(qCard).name, Card(qCard).text)):
                        continue
                ## place the peek icon on the cards we're looking at to prevent cheating, if the deck gets shuffled after then they'll disappear anyway
                for t in targets:
                    t.peek()
            toGroup = eval(params["to"]["group"])
            toIndex = eval(params["to"]["index"])
            dlg = cardDlg(targets)
            dlg.max = min(eval(params['to'].get("max", "len(targets)")), len(targets))
            if "min" in params["to"]:
                dlg.min = eval(params["to"]["min"])
            elif skippable:
                dlg.min = 0
            else:
                dlg.min = dlg.max
            dlg.label = params["to"].get("label", "from {} to {}".format(fromGroup.name, toGroup.name))
            if 'altTo' in params:
                dlg = cardDlg(targets, [])
                altToGroup = eval(params["altTo"]['group'])
                altToIndex = eval(params["altTo"]['index'])
                dlg.bottomLabel = params["altTo"].get("label", "from {} to {}".format(fromGroup.name, altToGroup.name))
            dlg.text = "Choose {}{} card(s) to move from {} to {}.".format(
                               "up to " if skippable else "",
                                 dlg.max,
                                                         fromGroup.name,
                                                               toGroup.name
                               )
            dlgChoice = dlg.show()
            for choice in (dlgChoice if dlg.min == 1 and dlg.max == 1 and dlg.bottomList == None else dlg.list):
                choice.moveTo(toGroup, toIndex)
                if fromGroup == me.hand and toGroup == me.Discard:
                    notify("{} discards {} from hand.".format(me, choice))
                else:
                    notify("{} moves {} to {} from {}.".format(me, choice, dlg.label, fromGroup.name))
            if dlg.bottomList != None:
                for choice in dlg.bottomList:
                    choice.moveTo(altToGroup, altToIndex)
                    if fromGroup == me.hand and altToGroup == me.Discard:
                        notify("{} discards {} from hand.".format(me, choice))
                    else:
                        notify("{} moves {} to {} from {}.".format(me, choice, dlg.bottomLabel, fromGroup.name))
        elif targetCount == "all" or ('target' in params and len(qTargets) == 0) or qCount + 1 >= eval(targetCount):
            del storedQueue[0]
        else:
            storedQueue[0] = (qCard, qTrigger, qType, qCount + 1, qPriority, qSkippable, qSource)
        if params.get("saveCount", False):
            storedGameStats["sc"] = qCount + 1
        ## Apply trigger effects from the game engine
        if qAction == "phaseChange": ## This is a game trigger to switch phases once the queue empties
            nextPhase = True
        elif qAction == "setupStop": ## This is a game trigger to move to the mulligan step after stopping a character
            nextStep = True
        elif qAction == "delCount":
            if "sc" in storedGameStats:
                del storedGameStats["sc"]
        elif qAction == "shuffle":
            shuffle = eval(params["group"])
            shuffle.shuffle()
            notify("{} shuffled their {}.".format(me, shuffle.name))
        elif qAction == "playCard":
            for targetCard in targets:
                #### Move the card to the correct location after playing it
                card = Card(targetCard)
                if card.Type == "Event":
                    card.moveTo(card.owner.Discard)
                    storedQueue = triggerScripts(card, "onPlay", targetCard) + phaseTriggers("onPlay", targetCard) + storedQueue
                elif card.Type == "Obstacle":
                    card.moveToTable(0,0)
                    storedCards = storeNewCards(card, {"s": "a"}, storedCards)
                    storedQueue = phaseTriggers("onPlay", targetCard) + storedQueue
                else:
                    card.moveToTable(0,0)
                    storedCards = storeNewCards(card, {"s": "r"}, storedCards)
                    storedQueue = phaseTriggers("onPlay", targetCard) + storedQueue
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
                if len(me.Deck) < int(card.Revive) or "nr" in storedCards[targetCard]:
                    choiceMap[2] = "Destroy"
                    del choiceMap[3]
                    del storedCards[targetCard]["nr"]
                ##Remove the Score option if the mission was a success
                if storedMission[2] == "s":
                    choiceMap[1] = choiceMap[2]
                    if choiceMap[2] == "Revive":
                        choiceMap[2] = choiceMap[3]
                        del choiceMap[3]
                    else:
                        del choiceMap[2]
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
        elif qAction == "chooseMode":
            choice = 0
            while choice == 0:
                choice = askChoice(params["message"], params["choices"])
                if choice == 0:
                    if params.get("skippable", False) == False:  # Mandatory choices must continue the loop until a choice is made
                        continue
                notify("{} chooses {}'s {} mode.".format(Player(qPriority), Card(qCard), params["choices"][choice - 1]))
                storedQueue = triggerScripts(Card(qCard), qType + str(choice), qCard) + storedQueue ## Add the new triggers to the queue
        elif qAction == "ruleSet":
            rule = params["rule"]
            value = eval(params["value"])
            newRule = storedGameStats.get(rule, [])
            if params.get("list", False):
                storedGameStats[rule] = storedGameStats.get(rule, []) + [(value, qSource)]
            else:
                storedGameStats[rule] = (value, qSource)
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
                    notify("{} targets {}'s {}.".format(sourceCard, Card(targetCard).owner, Card(targetCard)))
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
                elif action == "glyph":
                    glyphTarget = getGlyphTarget(targetCard)
                    glyphList = storedCards[glyphTarget]["g"]
                    glyphList.remove(targetCard)
                    storedCards[glyphTarget]["g"] = glyphList
                    newTargets = [c for c in storedCards if cardActivity(Card(c)) != "inactive" and Card(c).Type in params["attachTarget"] and c != glyphTarget]
                    storedQueue = [(newTargets, "game", "glyph", 0, qPriority, False, targetCard)] + storedQueue
                elif action == "assign":
                    storedCards[targetCard]["s"] = "a"
                    notify("{} assigns {}.".format(sourceCard, Card(targetCard)))
                elif action == "incapacitate":
                    storedCards[targetCard]["s"] = "i"
                    notify("{} incapacitates {}'s {}.".format(sourceCard, Card(targetCard).owner, Card(targetCard)))
                elif action == "destroy":
                    Card(targetCard).controller = Card(targetCard).owner
                    del storedCards[targetCard]
                    remoteCall(Card(targetCard).owner, "remoteMove", [Card(targetCard), 'Discard'])
                    notify("{} destroys {}'s {}.".format(sourceCard, Card(targetCard).owner, Card(targetCard)))
                elif action == "mission":
                    Card(targetCard).controller = Card(targetCard).owner
                    del storedCards[targetCard]
                    remoteCall(Card(targetCard).owner, "remoteMove", [Card(targetCard), 'Mission Pile'])
                    notify("{} puts {}'s {} on top of their Mission Pile.".format(sourceCard, Card(targetCard).owner, Card(targetCard)))
                elif action == "missionBottom":
                    Card(targetCard).controller = Card(targetCard).owner
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
                storedQueue[0][2] if storedQueue[0][1] in ("game", "trig") else "{}".format(Card(storedQueue[0][0])) + "'s " + storedQueue[0][2] + " ability",
                    Player(storedQueue[0][4]).name,
                       "chooses a" if storedQueue[0][5] else "must choose a",
                                 " (Press TAB to skip)" if storedQueue[0][5] else ""
                                            ))
    ## Update the variables if they have changed
    if storedCards != tempCards:
        setGlobalVariable("cards", str(storedCards))
    if storedQueue != tempQueue:
        setGlobalVariable("cardqueue", str(storedQueue))
    if nextPhase == True:
        phase = currentPhase()[1]
        if phase == 11:
            setPhase(0)
        else:
            setPhase(phase + 1)
    if nextStep == True:
        setGlobalVariable("setupStep", "4")
    if storedGameStats != tempGameStats:
        setGlobalVariable("gameStats", str(storedGameStats))


def cleanTable(group, x = 0, y = 0):
    mute()
    cleanup()

def cleanup():
    mute()
    if turnPlayer().isInverted:
        invert = True
    else:
        invert = False
    missionSkill, missionDiff, failcount, compcount, glyphwin, expwin, villwin = (0, 0, 0, 0, 0, 0, 0)
    alignvars = {"ha": (-71, 9), "hr": (-71, 117), "hg": (9,50), "va": (-70, -98) , "vg": (9,-138),
                 "hai": (9, -98), "hri": (9, -207), "hgi": (-71,-139), "vai": (9, 9) , "vgi": (-71,50 )    }
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
    #### Start aligning the cards on the table
    for c in sorted(storedCards.items(), key=lambda x: x[1]["#"]):
        c = c[0]
        card = Card(c)
        status = storedCards[c]["s"]
        if status == "am": ## skip general alignment of the active mission since it's done later on
            continue
        glyphs = [Card(x) for x in storedCards[c].get("g", [])] ## Gets the list of glyphs attached to the card
        for glyph in glyphs:
            if glyph.controller == me:
                expwin += int(glyph.experience)
                glyphwin += 1
        if cardActivity(card) != "inactive":
            if card.controller == me:
                ## If for some reason the card is no longer on the table, move it back
                if card not in table:
                    if status == "c":
                        card.moveToTable(0,0, True)
                    else:
                        card.moveToTable(0,0)
                ## add highlight for cards in the action queue
                if c in actionQueue:
                    if card.highlight != actionColor:
                        card.highlight = actionColor
                else:
                    if card.highlight != None:
                        card.highlight = None
                ## add a yellow filter to cards which are the source of a queue action
                if len(storedQueue) > 0 and storedQueue[0][0] == c:
                    if card.filter != FilterColor:
                        card.filter = FilterColor
                elif status ==  "i":
                    if card.filter != KOColor:
                        card.filter = KOColor
                else:
                    if card.filter != None:
                        card.filter = None
                ## fix face-up complications
                if status == "c" and card.isFaceUp == True:
                    card.isFaceUp = False
                    card.peek()
                ## fix face-down cards that are supposed to be face-up
                if status != "c" and card.isFaceUp == False:
                    card.isFaceUp = True
                ## rotate all cards that are stopped, blocked or incapacitated
                if status in ["i", "s"]:
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
                xpos = (-197 - 14 * failcount) if invert else (110 + 14 * failcount)
                ypos = (-32 if invert else -31)
                failcount += 1
                if card.controller == me: 
                    if card.position != (xpos, ypos):
                        card.moveToTable(xpos, ypos)
                    card.sendToBack()
                    for marker in card.markers:
                        if card.markers[marker] > 0:
                            card.markers[marker] = 0
            #### Prep Complications
            elif status == "c":
                xpos = (-347 - 14 * compcount) if invert else (260 + 14 * compcount)
                ypos = (-44 if invert else -45)
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
                if card.Type in ["Team Character", "Support Character"]:
                    if status == "a":
                        countType = "ha"
                        ypos = alignvars[countType][1]
                        if storedMission != None and cardSkills[type] != "":
                            missionSkill += cardSkills[type]
                    else:
                        countType = "hr"
                #### Prep Gear Cards
                elif card.Type == "Gear":
                    countType = "hg"
                #### Prep Villain Cards
                elif card.Type in villainTypes:
                    if status == "a":
                        countType = "va"
                        if storedMission != None and cardSkills[type] != "":
                            missionDiff += cardSkills[type]
                    else:
                        countType = "vg"
                else: ## in case a card doesnt match the above types?
                    continue
                if table.board == "invert":
                    countType += "i"
                ypos = alignvars[countType][1]
                xpos = alignvars[countType][0]
                dump = []
                if countType in ["hg", "vai"]:
                    #### normal side, positive x
                        if card.controller == me:
                            if card.position != (xpos, ypos):
                                card.moveToTable(xpos, ypos)
                        if card.orientation == Rot90:
                            xpos += 14
                            if len(glyphs) == 0:
                                xpos += 12
                        glyphpos = xpos + 0
                        xpos += 14 * len(glyphs)
                        if len(glyphs) > 0:
                            xpos += 12
                        alignvars[countType] = (xpos + 64, ypos)
                elif countType in ["vg", "hai", "hri"]:
                    #### invert side, positive x
                    xpos += 14*len(glyphs)
                    if len(glyphs) > 0:
                        xpos += 12
                    if card.orientation == Rot90:
                        xpos += 14 if len(glyphs) > 0 else 26
                    if card.controller == me:
                        if card.position != (xpos, ypos):
                            card.moveToTable(xpos, ypos)
                    glyphpos = xpos - (39 if card.orientation == Rot90 else 25)
                    alignvars[countType] = (xpos + 64, ypos)
                elif countType in ["va", "hgi"]:
                        #### normal side, negative x
                        if card.controller == me:
                            if card.position != (xpos, ypos):
                                card.moveToTable(xpos, ypos)
                        if card.orientation == Rot90:
                            xpos -= 14
                            if len(glyphs) == 0:
                                xpos -= 12
                        glyphpos = xpos - 25 
                        xpos -= 14 * len(glyphs)
                        if len(glyphs) > 0:
                            xpos -= 12
                        alignvars[countType] = (xpos - 64, ypos)
                elif countType in ["hr", "ha", "vgi"]:
                        #### invert side, negative x
                        xpos -= 14*len(glyphs)
                        if len(glyphs) > 0:
                            xpos -= 12
                        if card.orientation == Rot90:
                            xpos -= 14 if len(glyphs) > 0 else 26
                        if card.controller == me:
                            if card.position != (xpos, ypos):
                                card.moveToTable(xpos, ypos)
                        glyphpos = xpos + (14 if card.orientation == Rot90 else 0)
                        alignvars[countType] = (xpos - 64, ypos)
                for glyph in glyphs:
                    if glyph.controller == me:
                        glyphypos = ypos + (0 if invert else 26)
                        if glyph.position != (glyphpos, glyphypos):
                            glyph.moveToTable(glyphpos, glyphypos)
                            glyph.sendToBack()
                    glyphpos += 14 * (-1 if invert else 1)
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
                if card not in me.Team:
                    card.moveTo(me.Team)
    #### Align the active mission
    if storedMission != None:
        if myTurn():
            if table.board == "invert":
                if mission.position != (-97,-32):
                    mission.moveToTable(-97, -32)
                if mission.orientation != 0:
                    mission.orientation = 0
            else:
                if mission.position != (10, -31):
                    mission.moveToTable(10,-31)
                if mission.orientation != 0:
                    mission.orientation = 0
            missionDiff += value
            mission.markers[markerTypes["skill"]] = missionSkill
            mission.markers[markerTypes["diff"]] = missionDiff
    #### Determine victory conditions
    me.counters["Glyph Win"].value = glyphwin
    me.counters["Experience Win"].value = expwin
    for villain in me.piles["Villain Score Pile"]:
        villwin += int(villain.cost)
    me.counters["Villain Win"].value = villwin
    if currentPhase()[1] > 0:
        if glyphwin >= 7:
            notify("{} has won through Glyph Victory (7 glyphs.)".format(me))
            endGame()
        elif expwin >= storedVictory:
            notify("{} has won through Experience Victory ({} points.)".format(me, expwin))
            endGame()
        elif villwin >= storedVictory:
            notify("{} has won through Villain Victory ({} points.)".format(me, villwin))
            endGame()

def playComplication(card, x = 0, y = 0):
    mute()
    if myTurn():
        whisper("Cannot play {} as the Hero player.".format(card))
        return
    if currentPhase()[1] != 3: ## mis.main
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

#---------------------------------------------------------------------------
# Debug Actions
#---------------------------------------------------------------------------

def assign(card, x = 0, y = 0):
    mute()
    if not getSetting("debugMode", False):
        return
    global storedCards
    storedCards[card._id]["s"] = "a"
    setGlobalVariable("cards", str(storedCards))
    notify("{} readies {}.".format(me, card))

def ready(card, x = 0, y = 0):
    mute()
    if not getSetting("debugMode", False):
        return
    global storedCards
    storedCards[card._id]["s"] = "r"
    if "b" in storedCards[card._id]:
        del storedCards[card._id]["b"]
    setGlobalVariable("cards", str(storedCards))
    notify("{} readies {}.".format(me, card))

def block(card, x = 0, y = 0):
    mute()
    if not getSetting("debugMode", False):
        return
    global storedCards
    storedCards[card._id]["b"] = [None]
    setGlobalVariable("cards", str(storedCards))
    notify("{} blocks {} from the quest.".format(me, card))

def stop(card, x = 0, y = 0):
    mute()
    if not getSetting("debugMode", False):
        return
    global storedCards
    storedCards[card._id]["s"] = "s"
    setGlobalVariable("cards", str(storedCards))
    notify("{} stops {}.".format(me, card))

def incapacitate(card, x = 0, y = 0):
    mute()
    if not getSetting("debugMode", False):
        return
    global storedCards
    storedCards[card._id]["s"] = "i"
    setGlobalVariable("cards", str(storedCards))
    notify("{} KO's {}.".format(me, card))

def destroy(card, x = 0, y = 0):
    mute()
    if not getSetting("debugMode", False):
        return
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
    if not getSetting("debugMode", False):
        return
    if card.isFaceUp:
        notify("{} flips {} face down.".format(me, card))
        card.isFaceUp = False
    else:
        card.isFaceUp = True
        notify("{} morphs {} face up.".format(me, card))

def draw(group, x = 0, y = 0):
    if not getSetting("debugMode", False):
        return
    if len(group) == 0: return
    mute()
    group[0].moveTo(me.hand)
    notify("{} draws a card.".format(me))

def shuffle(group, x = 0, y = 0):
    if not getSetting("debugMode", False):
        return
    group.shuffle()