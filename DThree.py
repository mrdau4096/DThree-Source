import discord, asyncio, random, importlib, os, subprocess, datetime, time, threading
from fastapi import FastAPI, APIRouter
from contextlib import asynccontextmanager
from games.chess import checkChessGames, testImage
from games.noughtsAndCrosses import checkNoughtsAndCrossesGames
from exct.responses import checkReplies
from exct.memeBrowse import browseMemes
from exct.webSearch import lookUp
from exct.shared import removeNonASCII, getTime, updateRepo, sendMessage, replyMessage, backupData, addChannelDict
from exct.http import verifyToken, router, setClient
import games.economy


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.presences = True
client = discord.Client(intents=intents)
setClient(client)

gameSuffixes = ("o&x", "n&c", "ttt", "tictactoe", "noughtsandcrosses", "chess")



@client.event
async def onReady():
	print(f"\rSigned in as user: {client.user}")


async def otherTasks(message, messageData, userDisplayName):
	"""Handles all other asynchronous tasks."""
	with open("data/wordsSinceSpanishInquisition.txt", "r") as spainFile:
		wordsSinceSpanishInquisition = int(spainFile.readlines()[0].strip())
		wordsSinceSpanishInquisition += 1
		if wordsSinceSpanishInquisition > 1024:
			if random.randint(0, 1024) == 128:
				await message.reply(file=discord.File("imgs/Inquisition.gif"), mention_author=True)
				wordsSinceSpanishInquisition = 0

	with open("data/wordsSinceSpanishInquisition.txt", "w") as spainFile:
		spainFile.write(str(wordsSinceSpanishInquisition))

	if messageData.startswith("/help"):
		helpMessage = f"""
## DThree Help;
- There is an `/info` command for some basic info about DThree.

### User-given commands
{userCommands}

### `/Browse` lets you browse memes. It sends a random one, when no sub-folders are found.
- `/browse` shows all current files in that directory
- `/browse folder-name` opens the folder, if found
- `/back` goes back one directory level

### Games commands
- You may challenge another user to a game with the format `/challenge @user game`.
- `game` must be replaced by a valid game ID (see list of IDs).
- If you call `/challenge` without a valid game ID, you will be prompted to try again.
- To play noughtsAndCrosses, you must use `/play X,Y` to place your type in the X-Y position.
- In chess, you may use `/move X,Y X,Y` to move a piece from 1 place to another.
- You may also use `/select X,Y` to get more information on a certain tile's occupant.
- `/quit` quits the current game.

### Others
- /echo echoes the user's message (like cmdline)
- The bot only runs when Dau runs the script on [device]. It may be offline.
- The bot may restart for any reason, during testing.
- Any error messages will be formatted clearly. Treat this as a restart, unless the bot indicates otherwise.

*List of game IDs;*
{list(gameSuffixes[:5])} - Noughts & Crosses.
{[gameSuffixes[5],]} - chess.
"""
		await message.channel.send(helpMessage)
		return

	elif messageData.startswith("/info"):
		infoMessage = f"""
## DThree Info;
- DThree can play multiple simple games from commands (see `/help` for more information).
- DThree can automatically respond to messages of a certain type with randomised responses.
- DThree was written entirely in Python, with the discord.py module for API calls.
- DThree has successfully replaced 50% of shabbles#6353's functions (and only increasing).
- ~~DThree uses art created by TornadoTeam (Mr T)#2963 for the chess game.~~ *(unconfirmed)*
- DThree's original Noughts and Crosses game was entirely written in just 3 hours.
- DThree was created by Dau#7446 at 01:30 because they were bored.
		"""
		await message.channel.send(infoMessage)
		return
	elif messageData.startswith("/whatis"):
		await replyMessage(message, "Processing query.", ping=True)
		query = messageData.replace("/whatis","").strip().lower()
		results = lookUp(query)
		if not results: #Empty or None.
			await replyMessage(message, "No meaningful results were found.", ping=True)
		else:
			reply = f"## Query: {query}\n"
			for title, url in results.items():
				if "youtube.com" not in url.lower():
					reply += f"- [{title}](<{url}>)\n"
				else:
					reply += f"- [{title}]({url}) *(YouTube link)*\n"
			reply += "-# *Some results may not be relevant. Results were screened and had SafeSearch enabled while being processed. Please be responsible with your searches.*"
			await replyMessage(message, reply, ping=True)


	#Replace shabbles, handle games, memes, and economy
	await checkReplies(messageData, message)
	await games.economy.econIterate(message, messageData)
	await checkNoughtsAndCrossesGames(userDisplayName, messageData, message)
	await checkChessGames(userDisplayName, messageData, message)
	await testImage(message)
	await browseMemes(userDisplayName, messageData, message)

	if messageData.startswith("/challenge"):
		if not any(gameSuffix in messageData for gameSuffix in gameSuffixes):
			await message.channel.send(
				f"You must pick one of the following games to challenge;\n"
				f"{list(gameSuffixes[:4])} - Noughts & Crosses\n"
				f"{[gameSuffixes[4],]} - chess"
			)

	if messageData.startswith("/updaterepo"):
		await updateRepo(message=message)

	elif messageData.startswith("/econ force-reload"):
		importlib.reload(games.economy)


@client.event
async def onMessage(message):
	if message.author == client.user:
		return
	try:
		userDisplayName, messageData = message.author.display_name, removeNonASCII(message.content.strip().lower())
		await otherTasks(message, messageData, userDisplayName)
	
	except Exception as E:
		print(f"\a\n{E}\n")
		await replyMessage(message, f"## *An error occurred;*\n{str(E)}\n-# *Please wait.*", ping=True)





async def backgroundActions(client):
	D3StartTime = time.time()
	setStartTime(D3StartTime)

	channelDict = {}
	for guild in client.guilds:
		channelDict[guild.name] = {
			"channels": list(guild.text_channels),
			"guild": guild
		}

	addChannelDict(channelDict)

	while True:
		backupData() #Backup /data/
		await asyncio.sleep(3600) #60*60, 1 hour.





async def main(token):
	bgTask = asyncio.create_task(backgroundActions(client))
	DThreeTask = asyncio.create_task(client.start(token))
	await asyncio.gather(bgTask, DThreeTask)


@asynccontextmanager
async def lifespan(app: FastAPI):
    def runBot():
        token = os.getenv("BOT_TOKEN")
        asyncio.run(main(token))

    threading.Thread(target=runBot, daemon=True).start()
    
    yield


    await client.close()
    writeCSV("data/econ.csv")



app = FastAPI(lifespan=lifespan)
app.include_router(router)