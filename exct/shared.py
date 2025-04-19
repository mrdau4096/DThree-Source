import discord, datetime, os, subprocess

global channelDict
channelDict = {}


def addChannelDict(newDict):
	global channelDict
	channelDict = newDict


def getTime(dateOnly=False):
	#Gets current date/time, returns as a nicely formatted string.
	fullTime = str(datetime.datetime.now())
	unformattedDate, time = fullTime[:10], fullTime[11:-7]
	date = f"{unformattedDate[8:]}-{unformattedDate[5:7]}-{unformattedDate[:4]}"
	return f"{time}, {date}" if not dateOnly else date

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

async def replyMessage(message, messageText, ping=True):
	with open("data/log.txt", "a", encoding="utf-8") as logFile:
		if "*An error occurred;*" not in messageText:
			logFile.write("\n" + f"{getTime()} // {message.guild} // REPLY {message.author} // {messageText.strip()}")

	await message.reply(messageText, mention_author=ping)

async def updateRepo(message=None):
	os.chdir("textFiles")
	subprocess.run(["git", "fetch", "--all"])  #Fetch all branches
	subprocess.run(["git", "reset", "--hard", "origin/main"])  #Reset local branch
	subprocess.run(["git", "pull", "origin", "main"])  #Pull changes
	
	if message is not None:
		await sendMessage(message, "Files are now up to date.")
	else:
		print("Files are now up to date.")

def removeNonASCII(text):
	return ''.join(char for char in text if ord(char) < 128)


def backupData():
	githubToken = os.getenv("GITHUB_TOKEN")
	url = f"https://{githubToken}@github.com/mrdau4096/DThree-Data-Backups.git"
	cloneDir = "data-backups"

	subprocess.run(["git", "clone", url, cloneDir])
	subprocess.run(["cp", "-r", "data/", os.path.join(cloneDir, "data")])

	subprocess.run(["git", "-C", cloneDir, "config", "user.email", "d3@render.com"])
	subprocess.run(["git", "-C", cloneDir, "config", "user.name", "DThree"])


	subprocess.run(["git", "-C", cloneDir, "add", "."])
	subprocess.run(["git", "-C", cloneDir, "commit", "-m", f"{datetime.datetime.now()}"])
	subprocess.run(["git", "-C", cloneDir, "branch", "-M", "main"])
	subprocess.run(["git", "-C", cloneDir, "push", "-u", "origin", "main"])