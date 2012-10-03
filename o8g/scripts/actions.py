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

def myTurn():
    player = int(getGlobalVariable("turnplayer"))
    if me._id == player:
        return True
    else:
        return False

def registerTeam(group = Table, x = 0, y = 0):
    mute()
    if getGlobalVariable("phase") != "pregame" and getGlobalVariable("subphase") not in ["firstregister", "secondregister"]:
        whisper("Cannot register Team -- Game has already started")
        return
    if len(me.Team) != 4:
        notify("{}'s team does not have 4 members! Please restart game and load a legal deck.".format(me))
        return
    victory = 0
    teamlist = eval(getGlobalVariable("cards"))
    for card in me.Team:
        teamlist[card._id] = {"mission": { }, "turn": { }, "status": "ready"}
        card.moveToTable(0,0)
        victory = victory + card.Cost
    setGlobalVariable("cards", str(teamlist))
    me.setGlobalVariable("victory", str(victory))
    notify("{} registered his Team.".format(me))
    me.Deck.shuffle()
    me.piles['Mission Pile'].shuffle()
    if getGlobalVariable("subphase") == "firstregister":
        setGlobalVariable("subphase", "secondregister")
    elif getGlobalVariable("subphase") == "secondregister":
        himVictory = int(me.getGlobalVariable("victory"))
        meVictory = int(players[1].getGlobalVariable("victory"))
        if meVictory > himVictory:
            setGlobalVariable("turnplayer", str(me._id))
            notify("{} will play first.".format(me))
        elif meVictory < himVictory:
            setGlobalVariable("turnplayer", str(players[1]._id))
            notify("{} will play first.".format(players[1]))
        elif meVictory == himVictory:
            rng = rnd(1,2)
            if rng == 1:
                setGlobalVariable("turnplayer", str(me._id))
                notify("{} will play first, chosen randomly.".format(me))
            else:
                setGlobalVariable("turnplayer", str(players[1]._id))
                notify("{} will play first, chosen randomly.".format(players[1]))
        else:
            notify("Error: victory points not determined.")
            return
        setGlobalVariable("subphase", "stopcharacter")
        if myTurn():
             plyr = players[1]
        else:
             plyr = me
        notify("{} will target a team character to Stop.".format(plyr))
        cleanup()
    else:
        notify("An error has occured: subphase variable should be firstregister or secondregister")
        return

def confirmaction(group, x = 0, y = 0):
    mute()
    if getGlobalVariable("phase") == "pregame":
        subphase = getGlobalVariable("subphase")
        if subphase in ["firstregister", "secondregister"]:
            whisper("Nothing to confirm: Still waiting for players to register a team")
        elif subphase == "stopcharacter":
            if myTurn():
                whisper("Please wait while your opponent selects a target.")
                return
            else:
                target = [cards for cards in table if cards.targetedBy]
                if len(target) == 1:
                    for targetcard in target:
                        cards = eval(getGlobalVariable("cards"))
                        cards[targetcard._id]["status"] = "stop"
                        setGlobalVariable("cards", str(cards))
                        targetcard.target(False)
                        notify("{} Stops {}.".format(me, targetcard))
                    for p in players:
                        count = 0
                        while len(p.hand) < 8:
                            if len(p.Deck) == 0: break
                            p.Deck[0].moveTo(p.hand)
                            count = count + 1
                    notify("{} will decide to draw a new hand.".format(players[1]))
                    setGlobalVariable("subphase", "firstmulligan")
                else:
                    whisper("Please select a single target to Stop.")
        elif subphase == "firstmulligan":
            if myTurn():
              if confirm("Do you want to draw a new hand?"):
                for c in me.hand:
                  c.moveTo(me.Deck)
                rnd(1,10)
                me.Deck.shuffle()
                rnd(1,10)
                fillHand(me)
              else:
                notify("{} does not draw a new hand.".format(me))
              setGlobalVariable("subphase", "secondmulligan")
            else:
                whisper("Please wait until your opponent decides to draw a new hand.")
        elif subphase == "secondmulligan":
            if myTurn():
                whisper("You've already decided to draw a new hand.")
            else:
              if confirm("Do you want to draw a new hand?"):
                for c in me.hand:
                  c.moveTo(me.Deck)
                rnd(1,10)
                me.Deck.shuffle()
                rnd(1,10)
                fillHand(me)
              else:
                notify("{} does not draw a new hand.".format(me))
              cleanup()
              setGlobalVariable("phase", "power")
              setGlobalVariable("subphase", "none")
              powerPhase()
    elif getGlobalVariable("phase") == "mission":
        if getGlobalVariable("subphase") == "main":
            if int(getGlobalVariable("priority")) != me._id:
                whisper("Cannot pass: You don't have priority.")
            else:
                passcheck = getGlobalVariable("pass")
                if passcheck == "False":
                    setGlobalVariable("pass", "True")
                    setGlobalVariable("priority", str(players[1]._id))
                    notify('{} passes.'.format(me))
                    cleanup()
                else:
                    setGlobalVariable("pass", "False")
                    setGlobalVariable("subphase", "resolve")
                    setGlobalVariable("priority", str(turnPlayer()._id))
                    notify('{} passes, enters Mission Resolution.'.format(me))
                    resolveMission()
 

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
  notify("{} refilled hand to {}, drawing {} cards.".format(me, count, handsize))


def powerPhase():
  mute()
  power = 3
  for p in players:
    p.Power = power
    notify("{} gained {} power.".format(p, power))
  cleanup()
  setGlobalVariable("phase", "mission")
  setGlobalVariable("subphase", "start")
  missionPhase()

def missionPhase():
  if getGlobalVariable("activemission") == "None":
    turnplayer = turnPlayer()
    mission = turnplayer.piles['Mission Pile'][0]
    mission.moveToTable(0,0)
    mission.orientation = Rot90
    while mission.Culture == "?":
      rnd(1,10)
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
    tuple = (mission._id, skilltype, skillvalue)
    setGlobalVariable("activemission", str(tuple))
    setGlobalVariable("priority", str(turnplayer._id))
    setGlobalVariable("subphase", "main")
    cleanup()
  else:
    notify("Error: Active Mission variable not properly reset")

def resolveMission():
  mute()
  if getGlobalVariable("phase") != "mission":
    notify("ERROR: Cannot resolve mission -- not in mission phase")
    return
  if getGlobalVariable("subphase") != "resolve":
    notify("ERROR: Cannot resolve mission -- not in resolving step")
    return()
  activemission = getGlobalVariable("activemission")
  if activemission == "None":
    notify("ERROR: There is no registered active mission!")
    return
  mission, type, value = eval(activemission)
  mission = Card(mission)
  if mission not in table:
    mission.moveToTable(0,0)
  cleanup()
  if mission.markers[markerTypes['skill']] >= mission.markers[markerTypes['diff']]:
    return
    ###SUCCESS
  else:
    return
    ###FAIL

def cleanup():
  mute()
  if turnPlayer().hasInvertedTable():
    invert = True
  else:
    invert = False
  assigncount, readycount, stopcount, assigncounte, readycounte, stopcounte = (0, 0, 0, 0, 0, 0)
  skill = 0
  diff = 0
  carddict = eval(getGlobalVariable("cards"))
  activemission = getGlobalVariable("activemission")
  if activemission != "None":
    mission, type, value = eval(activemission)
  for card in table:
    if card._id not in carddict:
      notify("ERROr: {}'s {} did not enter play through the proper means.".format(card.controller, card))
  for c in carddict:
    card = Card(c)
    if card not in table:
      card.moveToTable(0,0)
    if card.Type != "Mission":
      if isActive(card):
        if card.Type in heroTypes:
          if carddict[card._id]["status"] == "assign":
            xpos = assigncount
            ypos = -98 if invert else 10
            assigncount = assigncount + 1
            if activemission != "None":
              if card.Type in heroTypes and card.properties[type] != "":
                skill = skill + int(card.properties[type])
              elif card.Type in enemyTypes and card.properties[type] != "":
                diff = diff + int(card.properties[type])
          elif carddict[card._id]["status"] == "ready":
            xpos = readycount
            ypos = -207 if invert else 119
            readycount = readycount + 1
          else:
            xpos = stopcount
            ypos = -316 if invert else 228
            stopcount = stopcount + 1
        else:
          if carddict[card._id]["status"] == "assign":
            xpos = assigncounte
            ypos = 10 if invert else -98
            assigncounte = assigncounte + 1
            if activemission != "None":
              if card.Type in heroTypes and card.properties[type] != "":
                skill = skill + int(card.properties[type])
              elif card.Type in enemyTypes and card.properties[type] != "":
                diff = diff + int(card.properties[type])
          elif carddict[card._id]["status"] == "ready":
            xpos = readycounte
            ypos = 119 if invert else -207
            readycounte = readycounte + 1
          else:
            xpos = stopcounte
            ypos = 228 if invert else -316
            stopcounte = stopcounte + 1
        card.moveToTable(70*xpos, ypos)
      else:
        card.moveToTable(-197, -44)
      if card.Culture != "":
        card.markers[markerTypes['Culture']] = int(card.Culture)
      if card.Science != "":
        card.markers[markerTypes['Science']] = int(card.Science)
      if card.Combat != "":
        card.markers[markerTypes['Combat']] = int(card.Combat)
      if card.Ingenuity != "":
        card.markers[markerTypes['Ingenuity']] = int(card.Ingenuity)
  if activemission != "None":
    mission = Card(mission)
    mission.moveToTable(-81 if invert else -105, -45 if invert else -44)
    diff = diff + value
    mission.markers[markerTypes['skill']] = skill
    mission.markers[markerTypes['diff']] = diff
  for card in me.hand:
    if card.Cost <= me.Power and isActive(card):
      card.highlight = PlayColor
    else:
      card.highlight = None

def playcard(card, x = 0, y = 0):
    mute()
    if getGlobalVariable("phase") != "mission":
      whisper("Cannot play {}: It's not the mission phase.".format(card))
      return
    if getGlobalVariable("subphase") != "main":
      whisper("Cannot play {} during this part of the mission phase.".format(card))
      return
    if int(getGlobalVariable("priority")) != me._id:
      whisper("Cannot play {}: You don't have priority.".format(card))
      return
    if card.Type == "Mission":
      notify("{} has Mission cards in his deck, play cannot continue.".format(me))
      return
    if not isActive(card):
      whisper("You cannot play {} during your {}turn.".format(card, "" if myTurn() else "opponent's "))
      return
    if me.Power < card.Cost:
      whisper("You do not have enough Power to play that.")
      return
    if card.Type == "Obstacle":
      activemission = getGlobalVariable("activemission")
      if activemission != "None":
        mission, type, value = eval(activemission)
      else:
        whisper("Cannot play {} as there is no active mission.".format(card))
        return
      if card.properties[type] == "":
        whisper("Cannot play {}: Does not match the active mission's {} skill.".format(card, type))
        return
      status = "assign"
    else:
      status = "ready"
    cards = eval(getGlobalVariable("cards"))
    cards[card._id] = {"mission": { }, "turn": { }, "status": status}
    setGlobalVariable("cards", str(cards))
    me.Power -= card.Cost
    card.moveToTable(0,0)
    cleanup()
    setGlobalVariable("priority", str(players[1]._id))
    notify("{} plays {}.".format(me, card))
    
def assign(card, x = 0, y = 0):
    mute()
    if getGlobalVariable("phase") != "mission":
      whisper("Cannot assign {}: It's not the mission phase.".format(card))
      return
    if getGlobalVariable("subphase") != "main":
      whisper("Cannot assign {} during this part of the mission phase.".format(card))
      return
    if int(getGlobalVariable("priority")) != me._id:
      whisper("Cannot assign {}: You don't have priority.".format(card))
      return
    activemission = getGlobalVariable("activemission")
    if activemission != "None":
      mission, type, value = eval(activemission)
    else:
      whisper("Cannot play {} as there is no active mission.".format(card))
      return
    if card.properties[type] == "":
      whisper("Cannot assign {}: Does not match the active mission's {} skill.".format(card, type))
      return
    carddict = eval(getGlobalVariable("cards"))
    if card._id in carddict:
      carddict[card._id]["status"] = "assign"
      setGlobalVariable("cards", str(carddict))
      cleanup()
      setGlobalVariable("priority", str(players[1]._id))
      notify("{} assigns {}.".format(me, card))
    else:
      notify("ERROR: {} not in cards global dictionary.".format(card))



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