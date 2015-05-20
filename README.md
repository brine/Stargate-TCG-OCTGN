Stargate-TCG
============

An OCTGN3 (http://www.octgn.net) game plugin for the Stargate Trading Card Game.

To install this game, add the feed URL https://www.myget.org/f/stargatetcg to OCTGN in the Games Manager.

The game plugin is currently in development and may contain many bugs which hamper gameplay.  It was made available to install and play only for testing and debug purposes.  The version found on the game feed is built off of the 'DEMO' branch, and contains only the cards & images available in the four Set-1 starter decks released for the game. 

## GAMEPLAY

The game plugin is written with full rules enforcement, and is 100% automated.  Most game actions can be performed on a card by double-clicking to:
 - assign a card in play
 - play a card in hand
 - select a card in a pop-up window
 - target a card to resolve an ability

Other game actions (with hotkeys if available, otherwise by selecting an option in the right-click menu) are as follows:
 - press TAB to pass the game action to your opponent (if both players pass sequentially, the mission will resolve)
 - press TAB to skip selecting a target for, or cancel, a non-mandatory triggered ability (the chat log will indicate which abilities can be skipped)
 - CTRL+Q to activate a card's ability if it has one
 - CTRL+C on a card in your hand to play it as a complication (as the villain player only)

The chat log will notify you of important information as the game progresses.  When a card ability is triggered or a game rule or card effect requires you to choose one or more cards in play, legal card choices will become highlighted in either red or blue.  Blue highlights are choices that the HERO player must make, while red highlights are for the VILLAIN player.  Unless mentioned in the chat log, these are MANDATORY effects and a target MUST be selected by the specified player.

## DEBUGGING THE GAME

Since it is still in development, you may encounter bugs which break the game engine or rules enforcement.  If encountered, you can enable DEBUG MODE in-game to override the game rules enforcement and access functions which allow you to perform game actions such as stopping, assigning, readying, destroying, or moving cards around on the table and in other zones. To enable debug mode, right-click the table and selecting 'Enable/Disable Debug Mode' in the DEBUG MENU submenu item.

If you restart or start a new game while DEBUG MODE is enabled, OCTGN will automatically load one of the four starter decks, chosen at random.  Ensure that DEBUG MODE is disabled before the game starts if you want to load a deck manually.

## GITHUB REPO INFORMATION

The `DEMO` branch contains the most recent version and is the branch that the game plugin is compiled from.  The `MASTER` branch may be outdated at times and is not recommended for forking.

You are welcome to clone the repo and try the project out at any time as well.  Feel free to open pull requests or submit issue tickets, they will be investigated.
