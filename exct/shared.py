import discord, datetime, os, subprocess
from dateutil.relativedelta import relativedelta



def getTime(dateOnly=False):
	#Gets current date/time, returns as a nicely formatted string.
	FULL_TIME = str(datetime.datetime.now())
	UNFORMATTED_DATE, TIME = FULL_TIME[:10], FULL_TIME[11:-7]
	DATE = f"{UNFORMATTED_DATE[8:]}-{UNFORMATTED_DATE[5:7]}-{UNFORMATTED_DATE[:4]}"
	return f"{TIME}, {DATE}" if not dateOnly else DATE



def timeSinceStr(dateStr: str, onlyDate=False) -> str:
	#Takes YYYY-MM-DD HH:MM:SS
	then = datetime.datetime.strptime(dateStr, "%Y-%m-%d %H:%M:%S")
	now = datetime.datetime.now()
	delta = relativedelta(now, then)
	parts = []
	if delta.years:
		parts.append(f"{delta.years} year{'s' if delta.years != 1 else ''}")
	if delta.months:
		parts.append(f"{delta.months} month{'s' if delta.months != 1 else ''}")
	if delta.days:
		parts.append(f"{delta.days} day{'s' if delta.days != 1 else ''}")
	if delta.hours and not onlyDate:
		parts.append(f"{delta.hours} hour{'s' if delta.hours != 1 else ''}")
	if delta.minutes and not onlyDate:
		parts.append(f"{delta.minutes} minute{'s' if delta.minutes != 1 else ''}")
	if delta.seconds and not onlyDate and not parts:
		parts.append(f"{delta.seconds} second{'s' if delta.seconds != 1 else ''}")

	return ', '.join(parts[:-1]) + (' and ' if len(parts) > 1 else '') + parts[-1] + ' ago' if parts else 'Undetermined'


def secondsSince(dateStr: str) -> int:
	then = datetime.datetime.strptime(dateStr, "%Y-%m-%d %H:%M:%S")
	now = datetime.datetime.now()
	return int((now - then).total_seconds())



def formatNumber(num, seperator=",", delimiter="."):
	formatted = ""
	if isinstance(num, float):
		formatted = f"{num:,.2f}"
	else:
		formatted = f"{num:,}"

	return formatted.replace(",", "__TMP__").replace(".", delimiter).replace("__TMP__", seperator)



async def sendMessage(message, messageText):
	with open("/project/src/disk/data/log.txt", "a", encoding="utf-8") as logFile:
		if "*An error occurred;*" not in messageText:
			logFile.write("\n" + f"{getTime()} // {message.guild} // SEND {message.author} // {messageText}".replace('\n', ';'))

	await message.channel.send(messageText)



async def replyMessage(message, messageText, ping=True):
	with open("/project/src/disk/data/log.txt", "a", encoding="utf-8") as logFile:
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



async def sendMessageInChannel(client, text, guild, channel):
	guildList = dict([(g.name, g) for g in client.guilds])
	guild = guildList[guild]

	if guild is not None:
		channelList = dict([(ch.name, ch) for ch in guild.text_channels])
		channel = list(channelList.values())[channel]

		if channel is not None:
			await channel.send(text) #Ping Dau#7446
		else:
			raise ValueError("Invalid Channel")

	else:
		raise ValueError("Invalid Guild")