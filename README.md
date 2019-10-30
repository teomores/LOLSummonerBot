<p align="center">
  <img height="300" width="300" src="logo.jpg">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.7.4-blue">
  <img src="https://img.shields.io/badge/Neo4j-3.5.11-lightgrey">
</p>

# LOLSummonerBot
This is the code of my Telegram Bot for tracking friends' activity on [League of Legends](https://euw.leagueoflegends.com/).
The idea is the following: you subscribe to a set of League summoners and the bot will send you notifications everytime that one of the summoner that you are subscribed to enters a game and an other notification when the game is finished as well.
The purpose is both to give you push notification for famous streamers or league players that you'd like to follow as well as to receive a message everytime that a friend of yours is playing, so that you can join.
The bot is not live because right now I can't afford a Raspberry Pi to host it, but I hope to make it live in a few weeks with a lot of new features :)

# Beta
This is only the first release, in the future I'll had some interesting features about previous games and champion scores for each summoner.

# Database
The LOLSummonerBot uses [Neo4j](https://neo4j.com/), a graph based database that fits very well to my data structure, in which what matters is primarly the relationship between Telegram users and LoL summoners.

# License
The software is distributed under the MIT License.
