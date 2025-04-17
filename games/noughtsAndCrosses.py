import discord
from exct.shared import sendMessage, replyMessage


def inRange(x, lower, upper):
	return lower <= x <= upper

class Board:
	def __init__(self, blankSquare, xSquare, oSquare):
		self.grid = [[blankSquare for _ in range(3)] for _ in range(3)]
		self.players = {"X": None, "O": None}
		self.styleInfo = {" ": blankSquare, "X": xSquare, "O": oSquare}
		self.lastMove = "O"
		self.won = False

	async def setBoardSquare(self, user, position, message):
		# Determine the user's symbol
		if user == self.players["X"]:
			userTile = self.styleInfo["X"]
			userType = "X"
		elif user == self.players["O"]:
			userTile = self.styleInfo["O"]
			userType = "O"
		else:
			await sendMessage(message, "You are not assigned to a team.")
			return

		# Check if the position is within the grid range
		if inRange(position[0], 1, 3) and inRange(position[1], 1, 3):
			gridLocation = self.grid[position[0] - 1][position[1] - 1]
			if gridLocation == self.styleInfo[" "] and userType != self.lastMove:
				self.grid[position[0] - 1][position[1] - 1] = userTile
				self.lastMove = userType
				reply = f"Placed {userType} at position (X:{position[1]}, Y:{position[0]})"
				winStatus = self.checkForWin()
				if winStatus is not None:
					curGrid = self.strGrid()
					reply = f"{reply}\n{curGrid}\n{winStatus}"
					self.won = True
			elif userType == self.lastMove:
				reply = f"{user.display_name}, it is not your turn"
			else:
				posType = "X" if gridLocation == self.styleInfo["X"] else "O"
				userName = self.players[posType].display_name
				reply = f"Tile (X:{position[1]}, Y:{position[0]}) already claimed by {userName} ({posType})"
		else:
			reply = "Please enter a position value within range (1-3 inclusive)\n*Formatting: [/play X,Y]*"

		# Send the reply back to the channel
		await sendMessage(message, reply)


	def checkForWin(self):
		for column in range(3):
			result = self.checkLine([self.grid[row][column] for row in range(3)])
			if result[1]:
				return result[0]
		
		for row in self.grid:
			result = self.checkLine(row)
			if result[1]:
				return result[0]

		diagonal1 = [self.grid[i][i] for i in range(3)]
		result = self.checkLine(diagonal1)
		if result[1]:
			return result[0]

		diagonal2 = [self.grid[i][2 - i] for i in range(3)]
		result = self.checkLine(diagonal2)
		if result[1]:
			return result[0]

		if all(cell != self.styleInfo[" "] for row in self.grid for cell in row):
			return "It's a draw"

		return None




	def strGrid(self):
		return f"""
`	1   2   3  `
`  ╔═══╦═══╦═══╗`
`A ║ {self.grid[0][0]} ║ {self.grid[0][1]} ║ {self.grid[0][2]} ║`
`  ╠═══╬═══╬═══╣`
`B ║ {self.grid[1][0]} ║ {self.grid[1][1]} ║ {self.grid[1][2]} ║`
`  ╠═══╬═══╬═══╣`
`C ║ {self.grid[2][0]} ║ {self.grid[2][1]} ║ {self.grid[2][2]} ║`
`  ╚═══╩═══╩═══╝`
		"""


	def checkLine(self, line):
		if len(set(line)) == 1 and line[0] != self.styleInfo[" "]:
			winningType = [key for key, value in self.styleInfo.items() if value == line[0]][0]
			return f"{self.players[winningType].mention} ({winningType}) wins", True
		return "", False


pending_challenges = {}
activeBoards = {}


def forceEndAllTTT():
	IDs = list(activeBoards.keys())
	for ID in IDs:
		del activeBoards[ID]
	print(f"Ended {len(IDs)} games.")


async def checkNoughtsAndCrossesGames(userDisplayName, messageData, message):
	global pending_challenges, activeBoards
	
	#Handle challenge command
	if messageData.startswith("/challenge") and (("o&x" in messageData) or ("n&c" in messageData) or ("ttt" in messageData) or ("tictactoe" in messageData) or ("noughtsandcrosses" in messageData)):
		if len(message.mentions) != 1:
			await sendMessage(message, "Please mention one user to challenge")
			return

		opponent = message.mentions[0]
		if opponent == message.author:
			await sendMessage(message, "You cannot challenge yourself")
			return

		pending_challenges[opponent.id] = {
			"challenger": message.author,
			"message": message,
		}
		await sendMessage(message, f"{opponent.display_name}, you have been challenged by {message.author.display_name} to a match of `Noughts & Crosses`/ Type `/accept` to start the game or `/decline` to decline the challenge.")

	#Handle accept command
	if messageData.startswith("/accept"):
		if message.author.id not in pending_challenges:
			await sendMessage(message, "You don't have any pending challenges.")
			return

		challenge = pending_challenges.pop(message.author.id)
		challenger = challenge["challenger"]
		originalMessage = challenge["message"]

		board = Board(" ", "X", "O")
		board.players["X"] = challenger
		board.players["O"] = message.author
		activeBoards[originalMessage.channel.id] = board

		await sendMessage(message, f"Game started between *{challenger.display_name} (X)* and *{message.author.display_name} (O)*\nUse `/play X,Y` to make your moves.\n*{challenger.display_name} (X) plays first*")
		await message.channel.send(board.strGrid())

	#Handle decline command
	if messageData.startswith("/decline"):
		if message.author.id not in pending_challenges:
			await sendMessage(message, "You don't have any pending challenges.")
			return

		challenge = pending_challenges.pop(message.author.id)
		challenger = challenge["challenger"]
		initialMessage = challenge["message"]

		await sendMessage(message, f"{message.author.display_name} has declined the challenge from {challenger.display_name}.")

	#Handle play command
	if messageData.startswith("/play"):
		if message.channel.id not in activeBoards:
			await sendMessage(message, "There are no active games in this channel. Start a new game with `/challenge @user`.")
			return

		board = activeBoards[message.channel.id]
		if message.author not in [board.players["X"], board.players["O"]]:
			print(message.author, board.players["X"], board.players["O"])
			await sendMessage(message, "You are not part of the current game.")
			return

		if board.won:  # Check if the game has already ended
			await sendMessage(message, "The game has already ended. Start a new game with `/challenge @user`.")
			return

		try:
			alpha = ("a", "b", "c")
			position = messageData.replace("/play ","").replace(" ", "").split(",")[:2]
			if position[0] in alpha:
				position = (int(position[1]), alpha.index(position[0])+1)
			elif position[1] in alpha:
				position = (int(position[0]), alpha.index(position[1])+1)
			else:
				raise TypeError("Invalid format")
			position = (position[1], position[0])

			await board.setBoardSquare(message.author, position, message)
			if not board.won:
				await message.channel.send(board.strGrid())
			else:
				# Delete the game from activeBoards once it is won or drawn
				del activeBoards[message.channel.id]

		except (IndexError, ValueError, TypeError):
			await sendMessage(message, "Invalid format. Use `/play X,Y`.")

	if messageData.startswith("/quit"):
		game_found = False
		for channelID, board in list(activeBoards.items()):
			if message.author == board.players["X"] or message.author == board.players["O"]:
				opponent = board.players["O"] if message.author == board.players["X"] else board.players["X"]
				del activeBoards[channelID]
				await sendMessage(message, f"{message.author.display_name} has quit the game/\n{opponent.mention} wins by default.")
				game_found = True
				break

		if not game_found:
			await sendMessage(message, f"{message.author.display_name}, you are not in a game.")

	#Cleanup ended games
	for channelID, board in list(activeBoards.items()):
		if board.won:
			del activeBoards[channelID]