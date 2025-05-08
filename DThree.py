import discord, asyncio, random, importlib, os, subprocess, datetime, time, signal
from games.chess import checkChessGames, testImage
from games.noughtsAndCrosses import checkNoughtsAndCrossesGames
from exct.responses import checkReplies
from exct.memeBrowse import browseMemes
from exct.webSearch import lookUp
from exct.shared import removeNonASCII, getTime, updateRepo, sendMessage, replyMessage, timeSinceStr, sendMessageInChannel
import games.economy

global D3StartTime, DTHREE_PUBLIC, client

#Use for testing the bot on Dau's Repository.
DTHREE_PUBLIC = False

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.presences = True
client = discord.Client(intents=intents)

gameSuffixes = ("o&x", "n&c", "ttt", "tictactoe", "noughtsandcrosses", "chess")



@client.event
async def on_ready():
	print(f"\rSigned in as user: {client.user}\nPlease input a command;\n> ", end="")


async def otherTasks(message, messageData, userDisplayName):
	global D3StartTime, DTHREE_PUBLIC

	#Stop replies outside of Dau's Repository if ENV variable is set.
	if (not DTHREE_PUBLIC) and message.guild.name != "Dau's Repository":
		return

	"""Handles all other asynchronous tasks."""
	with open("/project/src/disk/data/wordsSinceSpanishInquisition.txt", "r") as spainFile:
		wordsSinceSpanishInquisition = int(spainFile.readlines()[0].strip())
		wordsSinceSpanishInquisition += 1
		if wordsSinceSpanishInquisition > 1023:
			if random.randint(0, 1023) == 127:
				await message.reply(file=discord.File("imgs/Inquisition.gif"), mention_author=True)
				wordsSinceSpanishInquisition = 0

	with open("/project/src/disk/data/wordsSinceSpanishInquisition.txt", "w") as spainFile:
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



	elif messageData.startswith("/uptime"):
		currentTime = time.time()
		uptime = currentTime - D3StartTime


		days = int(uptime // 84600 % 365)
		hours = int(uptime // 3600 % 24)
		minutes = int(uptime // 60 % 60)
		seconds = int(uptime % 60)
		uptimeStr = ""
		if days > 0:
			uptimeStr += f"{days} days, "
		if hours > 0 or days > 0:
			uptimeStr += f"{hours} hours, "
		if minutes > 0 or hours > 0 or days > 0:
			uptimeStr += f"{minutes} minutes "
		uptimeStr += f"{seconds} seconds."


		timeSinceCreationStr = timeSinceStr("2024-09-01 08:00:00")

		await replyMessage(message, f"DThree has been online for: {uptimeStr}\nTime since DThree was created: {timeSinceCreationStr}", ping=True)



@client.event
async def on_message(message):
	if message.author == client.user:
		return
	if DTHREE_PUBLIC:
		try:
			userDisplayName, messageData = message.author.display_name, removeNonASCII(message.content.strip().lower())
			await otherTasks(message, messageData, userDisplayName)
		
		except Exception as E:
			print(f"\a\n{E}\n")
			await replyMessage(message, f"## *An error occurred;*\n{str(E)}\n-# *Please wait.*", ping=True)
	
	else:
		userDisplayName, messageData = message.author.display_name, removeNonASCII(message.content.strip().lower())
		await otherTasks(message, messageData, userDisplayName)
		




def backupData():
	dataDir = "/project/src/disk/data"
	github_token = os.getenv("GITHUB_TOKEN")
	repo_url = f"https://{github_token}@github.com/mrdau4096/DThree-Data-Backups.git"

	if not os.path.exists(os.path.join(dataDir, ".git")): #Ensure folder is a valid git repo location
		subprocess.run(["git", "init"], cwd=dataDir)
		subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=dataDir)

	subprocess.run(["git", "config", "user.email", "d3@render.com"], cwd=dataDir)
	subprocess.run(["git", "config", "user.name", "DThree"], cwd=dataDir)

	subprocess.run(["git", "add", "."], cwd=dataDir)
	subprocess.run(["git", "commit", "-m", f"{datetime.datetime.now()}"], cwd=dataDir)
	subprocess.run(["git", "branch", "-M", "main"], cwd=dataDir)
	subprocess.run(["git", "push", "-u", "origin", "main"], cwd=dataDir)

def pullData():
	dataDir = "/project/src/disk/data"
	github_token = os.getenv("GITHUB_TOKEN")
	repo_url = f"https://{github_token}@github.com/mrdau4096/DThree-Data-Backups.git"

	if not os.path.exists(os.path.join(dataDir, ".git")): #Ensure folder is a valid git repo location
		subprocess.run(["git", "init"], cwd=dataDir)
		subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=dataDir)

	subprocess.run(["git", "pull", "origin", "main"], cwd=dataDir)


async def backgroundActions(client):
	global D3StartTime
	D3StartTime = time.time()
	try:
		pullData()	
		while True:
			await asyncio.sleep(3600) #60*60, 1 hour.
			backupData() #Backup /project/src/disk/data/
	except Exception as e:
		await sendMessageInChannel(
			client,
			f"# Error occurred in background actions: {e}\n-# @663451560465924097",
			"Dau's Repository",
			"bot-testing"
		)
		print(e)


"""
async def handleShutdown(signum, frame):
	global client

	#Warn of shutdown.
	await sendMessageInChannel(client, "Shutdown imminent; Either redeploy or manual termination.", "Dau's Repository", "dthree-space")

	sys.exit(0)

signal.signal(signal.SIGINT, handleShutdown)
signal.signal(signal.SIGTERM, handleShutdown)
"""



async def main(token):
	bgTask = asyncio.create_task(backgroundActions(client))
	DThreeTask = asyncio.create_task(client.start(token))
	await asyncio.gather(bgTask, DThreeTask)

# Start everything
if __name__ == "__main__":
	token = os.getenv("BOT_TOKEN")
	asyncio.run(main(token))
