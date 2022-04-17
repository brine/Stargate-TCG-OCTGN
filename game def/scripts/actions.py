    
def assign(card, x = 0, y = 0):
    mute()
    if card.filter != None:
        whisper("Cannot assign {}: it is blocked from the mission.".format(card))
    elif not card.isFaceUp:
        whisper("Cannot assign {}: it is incapacitated.".format(card))
    elif card.orientation != Rot0:
        whisper("Cannot assign {}: it is not ready.".format(card))
    else:
        notify("{} assigns {} to the mission.".format(me, card))

def ready(card, x = 0, y = 0):
    mute()
    if card.filter != None:
        card.filter = None
        notify("{} unblocks {}.".format(me, card))
    else:
        if card.orientation != Rot0:
            card.orientation = Rot0
        notify("{} readies {}.".format(me, card))

def block(card, x = 0, y = 0):
    mute()
    if card.filter == None:
        card.filter = "#bb777777"
        notify("{} blocks {} from the mission.".format(me, card))
    else:
        card.filter = None
        whisper("{} unblocks {} from the mission.".format(me, card))

def stop(card, x = 0, y = 0):
    mute()
    if card.orientation != Rot90:
        card.orientation = Rot90
        notify("{} stops {}.".format(me, card))
    else:
        card.orientation = Rot0
        whisper("{} readies {}.".format(me, card))

def incapacitate(card, x = 0, y = 0):
    mute()
    if card.isFaceUp:
        card.isFaceUp = False
        card.orientation = Rot90
        card.peek()
        notify("{} incapacitates {}.".format(me, card))
    else:
        card.isFaceUp = True
        whisper("{} removes incapacitation from {}.".format(me, card))

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
        notify("{} flips {} face up.".format(me, card))

def draw(group, x = 0, y = 0):
    if len(group) == 0: return
    mute()
    group[0].moveTo(me.hand)
    notify("{} draws a card.".format(me))
    
def discardX(group, x = 0, y = 0):
    if len(group) == 0:
        return
    mute()
    count = min(askInteger("Discard how many cards?", 0), len(group))
    if count == None or count == 0:
        return
    for card in group.top(count):
        card.moveTo(card.owner.Discard)
    notify("{} discards {} cards from {} (top).".format(me, count, group.name))

def shuffle(group, x = 0, y = 0):
    if len(group) > 0:
        group.shuffle()

def activateAbility(card, x = 0, y = 0):
    mute()
    notify("{} activates {}'s ability.".format(me, card))

def passTurn(group, x = 0, y = 0):
    mute()
    notify("{} passes.".format(me))
    
def promotion(card, x = 0, y = 0):
    mute()
    card.markers[("Promotion", "Promotion")] += 1
    notify("{} adds a promotion counter to {}.".format(me, card))
    
######################################################
##
## SCRIPTS
##
######################################################


def debugToggle(group, x = 0, y = 0):
    mute()
    global DebugMode
    if isDebug() == False:
        notify("{} enables Debug Mode.".format(me))
        setSetting("debugMode", True)
        DebugMode = True
    else:
        notify("{} disables Debug Mode.".format(me))
        setSetting("debugMode", False)
        DebugMode = False
        
DebugMode = True

def isDebug():
    mute()
    global DebugMode
    if DebugMode == None:
        DebugMode = getSetting("debugMode", False)
    return DebugMode

def turnPassed(args):
    mute()
    if me.isActive:
        if me.isInverted:
            table.board = "invert"
        else:
            table.board = ""
        for c in table:
            if c.controller == me:
                if not c.isFaceUp and c.orientation == Rot90:
                    c.isFaceUp = True
                elif c.orientation == Rot90:
                    c.orientation = Rot0
                elif c.filter != None:
                    c.filter = None

def overrideCardsMoved(args):
    mute()
    for i in range(0, len(args.cards)):
        card = args.cards[i]
        if args.toGroups[i] == table:
            fromGroup = card.group
            card.moveToTable(args.xs[i], args.ys[i], not args.faceups[i])
            if fromGroup != table:
                card.index = args.indexs[i]
                if args.faceups[i]:
                    notify("{} plays {}.".format(me, card))
                else:
                    card.peek()
                    notify("{} plays {} as a complication.".format(me, card))
        else:
            group = card.group
            index = args.indexs[i]
            toGroup = args.toGroups[i]
            card.moveTo(toGroup, index)
            if toGroup.name in ["Hand", "Team", "Villain Score Pile", "Discard"]:
                notify("{} moves {} to {} from {}.".format(me, card, toGroup.name, group.name))
            elif index == 0 and toGroup:
                notify("{} moves {} to {} (top) from {}.".format(me, card, toGroup.name, group.name))
            elif index + 1 >= len(toGroup):
                notify("{} moves {} to {} (bottom) from {}.".format(me, card, toGroup.name, group.name))
            else:
                notify("{} moves {} to {} ({} from top) from {}.".format(me, card, toGroup.name, index, group.name))

def registerTeam(args = None):
    mute()
    if args != None and args.player != me:  #only execute this event if its your own deck
        return
    #### Verify deck contents
    validDeck = True
    whisper("~~~VALIDATING DECKS~~~")
    if len(me.Team) != 4:
        whisper("Team Error: You need exactly 4 Team Characters. ({} of 4)".format(len(me.Team)))
        validDeck = False
    deckCount = {}
    experience = 0
    for c in me.Team:
        deckCount[c.Name] = deckCount.get(c.Name, 0) + 1
        experience += int(c.Cost)  #add the card's cost to the victory total
    for x in deckCount:
        if deckCount[x] > 1:
            whisper("Team Error: You can only have one {} in your Team. ({} of 1)".format(x, deckCount[x]))
            validDeck = False
    heroCount = sum(1 for c in me.Deck if c.Type in heroTypes)
    if heroCount < 20:
        whisper("Deck Error: You need at least 20 Hero cards in your deck. ({} of 20)".format(heroCount))
        validDeck = False
    villainCount = sum(1 for c in me.Deck if c.Type in villainTypes)
    if villainCount < 20:
        whisper("Deck Error: You need at least 20 Villain cards in your deck. ({} of 20)".format(villainCount))
        validDeck = False
    for c in me.Deck:
        deckCount[c.Name] = deckCount.get(c.Name, 0) + 1
    for x in deckCount:
        if deckCount[x] > 3:
            whisper("Deck Error: You can have at most 3 {} in your Deck. ({} of 3)".format(x, deckCount[x]))
            validDeck = False
    if len(me.piles["Mission Pile"]) != 12:
        whisper("Mission Pile Error: You need exactly 12 Missions. ({} of 12)".format(len(me.piles["Mission Pile"])))
        validDeck = False
    deckCount = {}
    for c in me.piles["Mission Pile"]:
        deckCount[c.Name] = deckCount.get(c.Name, 0) + 1
    for x in deckCount:
        if deckCount[x] > 1:
            whisper("Mission Error: You can only have one {} in your Mission Pile. ({} of 1)".format(x, deckCount[x]))
            validDeck = False
    deckCount = {}
    for c in me.piles["Mission Pile"]:
        for stat in ["Culture", "Science", "Ingenuity", "Combat"]:
            if c.properties[stat] != "":
                deckCount[stat] = deckCount.get(stat, 0) + 1
    for x in deckCount:
        if deckCount[x] != 3:
            whisper("Mission Error: You need exactly 3 {} missions in your Mission Pile. ({} of 3)".format(x, deckCount[x]))
            validDeck = False
    if validDeck:
        notify("{} loaded a legal deck ({} experience).".format(me, experience))
        #### Store the loaded card IDs
        me.Deck.shuffle()
        me.piles["Mission Pile"].shuffle()
