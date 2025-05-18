import discord, asyncio, random, importlib, os, subprocess, datetime, time
from games.chess import checkChessGames, testImage
from games.noughtsAndCrosses import checkNoughtsAndCrossesGames
from exct.responses import checkReplies
from exct.memeBrowse import browseMemes
from exct.webSearch import lookUp
from exct.shared import removeNonASCII, getTime, sendMessage, replyMessage, timeSinceStr, sendMessageInChannel
from exct.shared import pullData, backupData, updateRepo
import games.economy

global D3StartTime, DTHREE_PUBLIC, client


#Use for testing the bot on Dau's Repository.
DTHREE_PUBLIC = True

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.presences = True
client = discord.Client(intents=intents)



#Background Tasks.
async def backgroundActions(client: discord.Client) -> None:
	global D3StartTime
	D3StartTime = time.time()
	try:
		pullData() #Get latest datafiles.
		while True:
			await asyncio.sleep(3600) #60*60s, 1 hour.
			backupData() #Backup /project/src/disk/data/
	except Exception as e:
		#Send background errors to testing server.
		await sendMessageInChannel(
			client,
			f"# Error occurred in background actions: {e}\n-# @663451560465924097", #Pings __dau__
			"Dau's Repository",
			"bot-testing"
		)
		print(e)






@client.event
async def on_ready() -> None:
	#Should it do something when deployed?
	pass


async def otherTasks(message: discord.Message, messageData: str) -> None:
	global D3StartTime, DTHREE_PUBLIC

	"""Handles all other asynchronous tasks."""
	spainFilePath = "/project/src/disk/data/wordsSinceSpanishInquisition.txt"
	if os.path.exists(spainFilePath):
		with open(spainFilePath, "r") as spainFile:
			lines = spainFile.readlines()
			if len(lines) > 0:
				wordsSinceSpanishInquisition = int(lines[0].strip())
				wordsSinceSpanishInquisition += 1
				if wordsSinceSpanishInquisition > 1023:
					if (random.randint(0, 1023) == 127) or (wordsSinceSpanishInquisition > 2047):
						await message.reply(file=discord.File("/project/src/disk/data/Inquisition.gif"), mention_author=True)
						wordsSinceSpanishInquisition = 0
			else:
				#If file gets OBLITERATED again, repopulate it.
				wordsSinceSpanishInquisition = 0

		with open(spainFilePath, "w") as spainFile:
			spainFile.write(str(wordsSinceSpanishInquisition))

	else:
		#If file gets OBLITERATED again, remake it.
		with open(spainFilePath, "x") as spainFile:
			spainFile.write("0")



	if messageData.startswith("/updaterepo"): #Update textfiles repo (pull)
		await updateRepo(message=message)
		return

	elif messageData.startswith("/backupdata"): #Push data files to git repo
		backupData()
		await replyMessage(message, "Successfully pushed data to repo.", ping=True)
		return

	elif messageData.startswith("/pulldata"): #Pull data files from git repo
		pullData()
		await replyMessage(message, "Successfully pulled data from repo.", ping=True)
		return



	elif messageData.startswith("/econ force-reload"): #Force-reload econ.
		importlib.reload(games.economy)
		return



	elif messageData.startswith("/uptime"): #Time DThree has been online for.
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
		return
	

	elif messageData.startswith("/whatis"): #Search with DDG.
		#Youtube results can embed; Others cannot.
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
			return



	await checkReplies(messageData, message) #"/" Commands and such.
	await games.economy.econIterate(message, messageData) #/econ and related functions.
	await checkNoughtsAndCrossesGames(messageData, message) #Checks active ttt games.
	#await checkChessGames(userDisplayName, messageData, message) #Checks active chess games. Disabled as chess is still unfinished after 9 months (18/05/2025).
	#await testImage(message) #Debug chess function, probably unnecessary.
	await browseMemes(messageData, message) #Functions for "/browse".




@client.event
async def on_message(message: discord.Message) -> None:
	if message.author == client.user:
		return
	if (not DTHREE_PUBLIC) and message.guild.name != "Dau's Repository":
		#Stop replies in non-testing server if [not DTHREE_PUBLIC].
		return

	try:
		messageData = message.author.display_name, removeNonASCII(message.content.strip().lower())
		await otherTasks(message, messageData)
	
	except Exception as E:
		#Handle errors gracefully.
		print(f"\a\n{E}\n")
		await replyMessage(message, f"## *An error occurred;*\n{str(E)}\n-# *Please wait.*", ping=True)



async def main(token: str) -> None:
	bgTask = asyncio.create_task(backgroundActions(client))
	DThreeTask = asyncio.create_task(client.start(token))
	await asyncio.gather(bgTask, DThreeTask)

# Start everything
if __name__ == "__main__":
	token = os.getenv("BOT_TOKEN")
	asyncio.run(main(token))
