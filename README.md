<p align="center">
  <img height="300" width="300" src="logo.jpg">
</p>

# LOLSummonerBot
This is the code of my Telegram Bot for tracking friends' activity on League of Legends.
The idea is the following: you subscribe to a set of League summoners and the bot will send you a notifications everytime that one of the summoner that you are subscribed to will enter in a game and an other notification when the game is finished as well.
The purpose is both to give you push notification for famous streamers or league players that you'd like to follow as well as to receive a message everytime that a friend of yours is playing so that you can join :)

# Beta
This is only the first release, in the future I'll had some interesting features about games and champions for each summoner.

# Database
The LOLSummonerBot uses [Neo4j](https://neo4j.com/), a graph based database that fits very well to my data structure, in which what matters is primarly the relationship between Telegram users and LoL summoners.
