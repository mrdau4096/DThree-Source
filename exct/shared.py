import discord, datetime, os, subprocess
from dateutil.relativedelta import relativedelta

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



def timeSinceStr(dateStr: str) -> str:
	#Takes YYYY-MM-DD HH:MM:SS
	then = datetime.strptime(dateStr, "%Y-%m-%d %H:%M:%S")
	now = datetime.now()
	delta = relativedelta(now, then)
	parts = []
    if delta.years:   parts.append(f"{delta.years} year{'s' if delta.years != 1 else ''}")
    if delta.months:  parts.append(f"{delta.months} month{'s' if delta.months != 1 else ''}")
    if delta.days:    parts.append(f"{delta.days} day{'s' if delta.days != 1 else ''}")
    if delta.hours:   parts.append(f"{delta.hours} hour{'s' if delta.hours != 1 else ''}")
    if delta.minutes: parts.append(f"{delta.minutes} minute{'s' if delta.minutes != 1 else ''}")
    if delta.seconds and not parts:
        parts.append(f"{delta.seconds} second{'s' if delta.seconds != 1 else ''}")

    return ', '.join(parts[:-1]) + (' and ' if len(parts) > 1 else '') + parts[-1] + ' ago' if parts else 'Undetermined'



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