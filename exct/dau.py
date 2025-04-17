import discord, aioconsole, time, sys, shutil, os, importlib, win32api, asyncio
from tkinter import messagebox
from exct.shared import sendMessage, replyMessage, updateRepo
from games.economy import writeCSV, createFakeCompany, forceUnBusyFunc, grantMoney
from exct.responses import showInvalidData
from games.noughtsAndCrosses import forceEndAllTTT
from games.chess import forceEndAllChess

global ready, client
ready = False
client = None

def pingDau(message, messageData):
	if len(message.mentions) >= 1:
		for mention in message.mentions:
			if str(mention) == "__dau__":
				print("\a", end="")


def findInList(guildName, guilds):
	for guild in guilds:
		if str(guild.name) == guildName:
			return guild
	return None


def onTerminalClose(signalType):
	global client
	print("Terminal Exit event triggered, saving CSV and safely closing.")
	if client is not None: asyncio.run(client.close)
	writeCSV("C:/Users/User/Documents/code/.py/discord/data/econ.csv")
	return True



async def dauDebug(cli):
	global client
	client = cli
	win32api.SetConsoleCtrlHandler(onTerminalClose, True)
	D3StartTime = time.time()

	#Set D3's status to be from the status file.
	"""
	if client is not None:
		with open("C:/Users/User/Documents/code/.py/discord/data/status.txt", "r") as statusFile:
			await client.change_presence(activity=discord.Game(name=statusFile.readline().strip()))
	"""

	while True:
		try:
			terminalInput = await aioconsole.ainput("\n> ")
			commandSections = terminalInput.strip().split("; ")
			match commandSections[0].lower():
				case "close" | "quit" | "exit":
					#TKinter Messagebox provided by Shabbr.
					if (len(commandSections) > 1 and commandSections[1].lower() == "-y") or messagebox.askyesno("DThree", "Are you sure you want to exit?"):
						await client.close()
						writeCSV("C:/Users/User/Documents/code/.py/discord/data/econ.csv")
						sys.exit()


				case "echo":
					serverName = "SW - the group chat"
					if len(commandSections) == 3:
						channelName = commandSections[1]
						echoMessage = commandSections[2].replace("¬","\n")
					elif len(commandSections) == 4:
						serverName = commandSections[1]
						channelName = commandSections[2]
						echoMessage = commandSections[3].replace("¬","\n")
					else:
						print(f"Data not recognised: {terminalInput}")
						continue

					server = findInList(serverName, client.guilds)
					mentions = {}
					for word in echoMessage.split(" "):
						if word.startswith("@"):
							attemptedMention = word.replace("@", "")
							for member in server.members:
								if str(member) == attemptedMention:
									mentions[f"@{attemptedMention}"] = member
					
					for word, member in mentions.items():
						echoMessage = echoMessage.replace(word, f"<@{member.id}>")


					
					channel = discord.utils.get(client.get_all_channels(), guild__name=serverName, name=channelName)
					if channel:
						await channel.send(echoMessage)
					else:
						print(f"Channel not recognised: {channelName}")
						continue


				case "list" | "view":
					if len(commandSections) < 2:
						print(f"Data not recognised: {terminalInput}")
						continue
					else:
						serverName = commandSections[1]

					server = findInList(serverName, client.guilds)
					if server:
						print(f"Found {len(server.channels)} channels in {serverName};\n")
						I = 0
						for channel in server.channels:
							if isinstance(channel, discord.TextChannel):
								print(f"{I}:	{channel}")
								I += 1
						print()

						for member in server.members:
							print(f"{member} -> @{member.id}")


				case "update-repo":
					await updateRepo()


				case "uptime":
					uptime = time.time() - D3StartTime
					if uptime < 60:
						print(f"D3 has been online for: {round(uptime)}s.")
					elif uptime < 3600:
						print(f"D3 has been online for: {uptime//60} minutes and {round(uptime)%60}s.")
					else:
						print(f"D3 has been online for: {uptime//3600} hours, {(uptime%3600)//60} minutes and {round(uptime)%60}s.")


				case "check-log":
					with open("C:/Users/User/Documents/code/.py/discord/data/log.txt", "r", encoding="utf-8") as logFile:
						logs = logFile.readlines()

					logsRequested = []
					if len(commandSections) > 1:
						logsRequested = logs[-int(commandSections[1]):]
					else:
						logsRequested = logs[-1:]

					for line in logsRequested:
						data = line.split(" // ")
						try:
							action, user = data[2].split(" ")
							print(f"Time: {data[0]}, Location: {data[1]}, {'SENT' if action == 'SEND' else action} to {user}: {data[3]}")

						except IndexError:
							print(f"Unable to read log (Malformed): {line}")


				case "end-game":
					match commandSections[2].lower():
						case "ttt" | "tictactoe" | "noughtsandcrosses" | "n&c":
							forceEndAllTTT()

						case "chess":
							forceEndAllChess()

						case _:
							print(f"Data not recognised: {terminalInput}")
							continue


				case "set-status" | "status":
					if len(commandSections) < 3:
							print(f"Data not recognised: {terminalInput}")
							continue

					elif commandSections[2].lower() == "-f":
						with open("C:/Users/User/Documents/code/.py/discord/data/status.txt", "r") as statusFile:
							newStatus = statusFile.readline().strip()

					else:
						newStatus = commandSections[2].strip()

					await client.change_presence(activity=discord.Game(name=newStatus))


				case "econ":
					if len(commandSections) < 2:
						print(f"Data not recognised: {terminalInput}")
						continue
					match commandSections[1].lower():
						case "save":
							writeCSV("C:/Users/User/Documents/code/.py/discord/data/econ.csv")


						case "force-unbusy":
							forceUnBusyFunc()


						case "restart" | "reload":
							importlib.reload(games.economy)


						case "grant":
							if len(commandSections) >= 3:
								grantMoney(float(commandSections[2]), commandSections[3]=="-user", commandSections[3]=="-company")

							else:
								print(f"Data not recognised: {terminalInput}")
								continue


						case _:
							print(f"Data not recognised: {terminalInput}")
							continue


				case "backup":
					if messagebox.askyesno("DThree", "Are you sure you want to backup datafiles?"):
						files = (
							"econ.csv",
							"bannedTitles.txt",
							"bannedURLs.txt",
							"fish.csv",
							"log.txt",
							"status.txt",
							"wordOccurrences.csv",
							"wordsSinceSpanishInquisition",
						)
						src = "C:/Users/User/Documents/code/.py/discord/data"
						dest = "E:/D3 Backup"

						for fileName in files:
							srcFile = os.path.join(src, fileName)
							destFile = os.path.join(dest, fileName)
							if os.path.exists(srcFile):
								shutil.copy2(srcFile, destFile)
								print(f"Successfully copied: {fileName}")
							else:
								print(f"File not found: {fileName}")


				case _:
					print(f"Data not recognised: {terminalInput}")
					continue
		
		except Exception as E:
			print(f"\a\n{E}\n")