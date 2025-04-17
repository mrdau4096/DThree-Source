import discord, datetime, os, subprocess

def getTime(dateOnly=False):
	#Gets current date/time, returns as a nicely formatted string.
	FULL_TIME = str(datetime.datetime.now())
	UNFORMATTED_DATE, TIME = FULL_TIME[:10], FULL_TIME[11:-7]
	DATE = f"{UNFORMATTED_DATE[8:]}-{UNFORMATTED_DATE[5:7]}-{UNFORMATTED_DATE[:4]}"
	return f"{TIME}, {DATE}" if not dateOnly else DATE

def formatNumber(num, seperator=",", delimiter="."):
	formatted = ""
	if isinstance(num, float):
		formatted = f"{num:,.2f}"
	else:
		formatted = f"{num:,}"

	return formatted.replace(",", "__TMP__").replace(".", delimiter).replace("__TMP__", seperator)

async def sendMessage(message, messageText):
	with open("data/log.txt", "a", encoding="utf-8") as logFile:
		if "*An error occurred;*" not in messageText:
			logFile.write("\n" + f"{getTime()} // {message.guild} // SEND {message.author} // {messageText}".replace('\n', ';'))

	await message.channel.send(messageText)

async def replyMessage(message, messageText, ping=False):
	with open("data/log.txt", "a", encoding="utf-8") as logFile:
		if "*An error occurred;*" not in messageText:
			logFile.write("\n" + f"{getTime()} // {message.guild} // REPLY {message.author} // {messageText.strip()}")

	await message.reply(messageText, mention_author=ping)

async def updateRepo(message=None):
	os.chdir("C:/Users/User/Documents/GitHub/DThree")
	subprocess.run(["git", "fetch", "--all"])  #Fetch all branches
	subprocess.run(["git", "reset", "--hard", "origin/main"])  #Reset local branch
	subprocess.run(["git", "pull", "origin", "main"])  #Pull changes
	
	if message is not None:
		await sendMessage(message, "Files are now up to date.")
	else:
		print("Files are now up to date.")

def removeNonASCII(text):
	return ''.join(char for char in text if ord(char) < 128)