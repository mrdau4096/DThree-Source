import discord, os, time
import math as maths

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame as PG


"""
0-Empty
1-Pawn
2-Knight
3-Rook
4-Bishop
5-Queen
6-King
"""
initialBoard = (
	(3, 1, 0, 0, 0, 0, 1, 3),
	(2, 1, 0, 0, 0, 0, 1, 2),
	(4, 1, 0, 0, 0, 0, 1, 4),
	(6, 1, 0, 0, 0, 0, 1, 6),
	(5, 1, 0, 0, 0, 0, 1, 5),
	(4, 1, 0, 0, 0, 0, 1, 4),
	(2, 1, 0, 0, 0, 0, 1, 2),
	(3, 1, 0, 0, 0, 0, 1, 3)
)


pending_challenges = {}
activeBoards = {}

def forceEndAllChess():
	IDs = list(activeBoards.keys())
	for ID in IDs:
		del activeBoards[ID]
	print(f"Ended {len(IDs)} games.")


surface = PG.display.set_mode((1024, 1024), PG.HIDDEN)

def clamp(x, lower, upper):
	return min(max(lower, x), upper)

def inRange(x, lower, upper):
	return lower <= x <= upper

sign = lambda x: maths.copysign(1, x)


class ChessBoard:
	def __init__(self):
		self.grid = [[None for _ in range(8)] for _ in range(8)]
		self.populate_board()

	def populate_board(self):
		# Add all pieces to the board in their initial positions
		for i in range(8):
			self.grid[i][1] = pawn(coord(i, 1), "white")
			self.grid[i][6] = pawn(coord(i, 6), "black")
		# Place rooks, knights, bishops, etc.
		# Example: self.grid[0][0] = rook(coord(0, 0), "white")

	def get_piece_at(self, position):
		return self.grid[position.x][position.y]

	def update_piece_position(self, piece, startPos, endPos):
		self.grid[startPos.x][startPos.y] = None
		self.grid[endPos.x][endPos.y] = piece


class coord:
	def __init__(self, x, y):
		self.x = x
		self.y = y

	def __add__(self, other):
		self.x += other.x
		self.y += other.y

	def __sub__(self, other):
		self.x -= other.x
		self.y -= other.y

	def __mul__(self, scalar):
		self.x *= scalar
		self.y *= scalar

	def __rmul__(self, scalar):
		return self * scalar

	def __truediv__(self, scalar):
		self.x /= scalar
		self.y /= scalar

	def __rtruediv__(self, scalar):
		return self / scalar

	def __eq__(self, other):
		return (self.x == other.x) and (self.y == other.y)

	def __repr__(self):
		return f"<coord [X:{self.x}, Y:{self.y}]>"

	def clamp(self, xBounds=None, yBounds=None):
		if xBounds is not None:
			self.x = clamp(self.x, xBounds[0], xBounds[1])
		if yBounds is not None:
			self.y = clamp(self.y, yBounds[0], yBounds[1])



class chessPiece:
	def __init__(self, pos, team):
		self.pos = pos
		self.team = team
		self.direction = 1 if team == "black" else -1

	def checkSquare(self, grid, pos):
		if not (inRange(pos.x, 0, 7) or inRange(pos.y, 0, 7)):
			return None
		return grid[pos.x][pos.y]

	def checkLine(self, grid, startPos, endPos):
		lastEmptyTile = 0
		if startPos.x == endPos.x:
			#Vertical Line.
			checkDir = sign(startPos.y - endPos.y)
			for I in range(abs(startPos.y - endPos.y)):
				squareData = self.checkSquare(grid, coord(startPos.x, startPos.y + (checkDir*I)))
				if squareData is not None:
					lastEmptyTile = I - 1
					break
			return coord(startPos.x, startPos.y + (checkDir*lastEmptyTile)) if lastEmptyTile > 0 else startPos

		elif startPos.y == endPos.y:
			#Horizontal Line.
			checkDir = sign(startPos.x - endPos.x)
			for I in range(abs(startPos.x - endPos.x)):
				squareData = self.checkSquare(grid, coord(startPos.x + (checkDir*I), startPos.y))
				if squareData is not None:
					lastEmptyTile = I - 1
					break
			return coord(startPos.x + (checkDir*lastEmptyTile), startPos.y) if lastEmptyTile > 0 else startPos

		elif abs(startPos.x - endPos.x) == abs(startPos.y - endPos.y):
			#Diagonal Line.	
			xCheckDir = sign(startPos.x - endPos.x)
			yCheckDir = sign(startPos.y - endPos.y)
			for I in range(abs(startPos.x - endPos.x)):
				squareData = self.checkSquare(grid, coord(startPos.x + (xCheckDir*I), startPos.y + (yCheckDir*I)))
				if squareData is not None:
					lastEmptyTile = I - 1
					break
			return coord(startPos.x + (xCheckDir*lastEmptyTile), startPos.y + (yCheckDir*lastEmptyTile)) if lastEmptyTile > 0 else startPos


class pawn(chessPiece):
	def __init__(self, pos, team):
		super().__init__(pos, team)
		self.moves = (self.direction, 2*self.direction)

	def move(self, newPos):
		if (newPos == self.pos + self.moves[0]) or (newPos == self.pos + self.moves[1]):
			furthestPoint = self.checkLine(self.pos, newPos)
			if furthestPoint != self.pos:
				self.pos = furthestPoint


	def __repr__(self):
		return f"<pawn [X:{self.x}, Y:{self.y}, Team:{self.team}, Direction: {self.direction}]>"

class rook(chessPiece):
	def __init__(self, pos, team):
		super().__init__(pos, team)

	def move(self, newPos, grid):
		# Rooks move in straight lines (horizontal or vertical)
		if self.pos.x == newPos.x or self.pos.y == newPos.y:
			furthestPoint = self.checkLine(grid, self.pos, newPos)
			if furthestPoint != self.pos:
				self.pos = furthestPoint

class knight(chessPiece):
	def __init__(self, pos, team):
		super().__init__(pos, team)
		
	def move(self, newPos, grid):
		# Knights move in an L-shape: 2 squares in one direction, then 1 square perpendicular
		dx = abs(newPos.x - self.pos.x)
		dy = abs(newPos.y - self.pos.y)
		if (dx, dy) in [(1, 2), (2, 1)]:
			self.pos = newPos

class bishop(chessPiece):
	def __init__(self, pos, team):
		super().__init__(pos, team)
		
	def move(self, newPos, grid):
		# Bishops move diagonally
		if abs(self.pos.x - newPos.x) == abs(self.pos.y - newPos.y):
			furthestPoint = self.checkLine(grid, self.pos, newPos)
			if furthestPoint != self.pos:
				self.pos = furthestPoint

class queen(chessPiece):
	def __init__(self, pos, team):
		super().__init__(pos, team)
		
	def move(self, newPos, grid):
		# Queens move like a rook or a bishop
		if self.pos.x == newPos.x or self.pos.y == newPos.y or abs(self.pos.x - newPos.x) == abs(self.pos.y - newPos.y):
			furthestPoint = self.checkLine(grid, self.pos, newPos)
			if furthestPoint != self.pos:
				self.pos = furthestPoint

class king(chessPiece):
	def __init__(self, pos, team):
		super().__init__(pos, team)
		
	def move(self, newPos, grid):
		# Kings move one square in any direction
		dx = abs(newPos.x - self.pos.x)
		dy = abs(newPos.y - self.pos.y)
		if dx <= 1 and dy <= 1:
			self.pos = newPos



async def checkChessGames(userDisplayName, messageData, message):
	global pending_challenges, activeBoards

	# Check /move command
	if messageData.lower().startswith("/move"):
		try:
			_, start, end = messageData.split()
			startX, startY = map(int, start.split(','))
			endX, endY = map(int, end.split(','))

			startPos = coord(startX, startY)
			endPos = coord(endX, endY)

			board = activeBoards.get(message.channel.id)
			if not board:
				await message.channel.send("No active game in this channel.")
				return

			piece = board.get_piece_at(startPos)
			if not piece:
				await message.channel.send(f"No piece at {startX},{startY}.")
				return

			if piece.team != get_user_team(userDisplayName):
				await message.channel.send(f"You can only move your own pieces.")
				return

			piece.move(endPos, board.grid)
			board.update_piece_position(piece, startPos, endPos)

			await message.channel.send(f"Moved piece to {endX},{endY}.")
			await display_board(message.channel, board)

		except ValueError:
			await message.channel.send("Invalid command format. Use /move X,Y Z,W")

def get_user_team(userDisplayName):
	# Determine user's team based on their role in the game.
	# Placeholder function; you'll need to implement team assignment.
	pass


async def testImage(message):
	global initialBoard
	messageData = message.content.strip().lower()
	if messageData.startswith("/testimg"):
		surface.fill((255, 255, 255))
		drawBoard(surface)

		if "fullboard" in messageData:
			for Y, row in enumerate(initialBoard):
				for X, tile in enumerate(row):
					if tile != 0:
						team = 0 if False else 1 #Add teams later
						drawImg(surface, "sheet-1.png", (X*128, Y*128), (128, 128), sheetPos=f"{team}{tile}")
			PG.display.flip()
			PG.image.save(surface, "C:\\Users\\User\\Documents\\code\\.py\\discord\\imgs\\board.png")
			await message.channel.send(file=discord.File("C:\\Users\\User\\Documents\\code\\.py\\discord\\imgs\\board.png"))




		else:
			drawImg(surface, "test.png", (0, 0), (128, 128))
			drawImg(surface, "sheet-1.png", (128, 0), (128, 128), sheetPos="15")
			PG.display.flip()
			PG.image.save(surface, "C:\\Users\\User\\Documents\\code\\.py\\discord\\imgs\\board.png")
			await message.channel.send(file=discord.File("C:\\Users\\User\\Documents\\code\\.py\\discord\\imgs\\board.png"))




def drawBoard(surface):
	for X in range(8):
		for Y in range(8):
			black, white = (61, 43, 31), (227, 218, 201)
			colour = white if (X%2==0) != (Y%2==0) else black

			PG.draw.rect(surface, colour, (X*128,Y*128,(X+1)*128,(Y+1)*128))



def drawText(SCREEN, TEXT, POSITION, FONT_SIZE, COLOUR=(255, 255, 255)):
	raise ValueError("No font in filepath.")
	#Draws text on a given surface, with colour, size and position.
	FONT = PG.font.Font('C:\\Users\\User\\Documents\\code\\.py\\discord\\data\\PressStart2P-Regular.ttf', FONT_SIZE)
	text_surface = FONT.render(str(TEXT), True, COLOUR)
	SCREEN.blit(text_surface, POSITION)

def drawImg(surface, filename, position, scale, sheetPos=None):
	#Draws an image loaded from the file structure (in \src\imgs\) to a position and with scale.
	img = PG.image.load(f"imgs\\{filename}")
	w,h = img.get_width(), img.get_height()

	if sheetPos is not None:
		Y, X = list(sheetPos)
		sheetRect = (
			w * (int(X, 16) / 16),
			h * (int(Y, 16) / 16),
			w/16, h/16
		)

		# Extract the image section using subsurface
		imgSection = img.subsurface(sheetRect)


	else:
		imgSection=img

	scaledImg = PG.transform.scale(imgSection, scale)
	surface.blit(scaledImg, position)
