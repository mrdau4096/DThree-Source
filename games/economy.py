import discord
import math as maths
import random, time
import csv, json
from exct.shared import removeNonASCII, sendMessage, replyMessage, formatNumber


"""
___
 | /\  |\ /\.
 | \/  |/ \/'

 - Currency class is not used; update instances of formatNumber() to use it.
 - wait-3 seems odd.
 - output seems odd.
 - Assorted others.
"""

global factoryTypes, propertyCosts, companies, pendingRequest, pendingAmount, busy
depreciationRate = 0.95
loanInflation = 1.05
companies = {}
pendingRequest, pendingAmount, busy = None, 0, False
factoryTypes = {
	"goods": {"income": 2000.0, "expenses": 1000.0, "speed": 1.0, "buildCost": 12500.0},
	"food": {"income": 1250.0, "expenses": 2000.0, "speed": 2.5, "buildCost": 27500.0},
	"valuables": {"income": 22500.0, "expenses": 3500.0, "speed": 0.25, "buildCost": 62500.0},
	"millitary": {"income": 12500.0, "expenses": 5000.0, "speed": 0.5, "buildCost": 32000.0},
	"ships": {"income": 50000.0, "expenses": 5000.0, "speed": 0.125, "buildCost": 125000.0},
	"cars": {"income": 15000.0, "expenses": 3000.0, "speed": 0.25, "buildCost": 32000.0},
}
propertyCosts = {
	"hlaford": 8000.0,
	"mostovod": 17000.0,
	"oxelgrund": 9500.0,
	"xnopyt": 16000.0,
	"tungyo": 24000.0,
	"obijwe": 32000.0,
	"qouzl": 42000.0,
	"industrial district": 0.0,
}
locationDesirability = {
	"hlaford": 500.0,
	"mostovod": 900.0,
	"oxelgrund": 800.0,
	"xnopyt": 750.0,
	"tungyo": 1250.0,
	"obijwe": 1500.0,
	"qouzl": 1750.0,
	"industrial district": 0.0,
}



class InvalidTypeException(Exception):
	pass

class NotEnoughMoneyException(Exception):
	pass

class InvalidLocationException(Exception):
	pass


class Currency:
	def __init__(self, symbol, prefix, seperator, delimiter):
		self.symbol = symbol
		self.prefix = prefix
		self.seperator = seperator
		self.delimiter = delimiter

	def format(self, value):
		return f"{self.symbol if self.prefix else ''}{formatNumber(value, seperator=self.seperator, delimiter=self.delimiter)}{'' if self.prefix else self.symbol}"

	def toRow(self):
		return {
			"symbol": self.symbol,
			"prefix": 'T' if self.prefix else 'F',
			"seperator": ord(self.seperator),
			"delimiter": ord(self.delimiter),
		}


class Property:
	def __init__(self, owner, income, expenses, location):
		self.ownedBy = owner
		self.income = income
		self.expenses = expenses
		self.location = location



class Factory(Property):
	def __init__(self, ceo, type, new=True):
		company = companies[ceo]
		if type in factoryTypes.keys():
			income, expenses, speed, buildCost = factoryTypes[type].values()

			if new:
				if buildCost > company.balance:
					raise NotEnoughMoneyException(f"Balance: {company.currency}{company.balance} < Cost: {company.currency}{buildCost}")

				company.balance -= buildCost
				company.equity += buildCost

			self.speed = speed
			self.type = type
			super().__init__(company.owner, income, expenses, "industrial district")
			company.assets.append(self)
			company.income += (self.income * self.speed) - self.expenses

		else:
			raise InvalidTypeException(f"Factory type [{type}] not in list of types.")

	def __repr__(self):
		return f"<Factory: [OWNER: {self.ownedBy}, LOCATION: {self.location}, INCOME: {companies[self.ownedBy].currency}{self.income}, EXPENSES: {companies[self.ownedBy].currency}{self.expenses}, PRODUCES: {self.type.capitalize()}]>"

	def format(self):
		company = companies[self.ownedBy]
		return f"{self.type.capitalize()} factory at {round(self.speed*100)}% efficiency, earning {userCompany.currency.format(self.income)} and costing {userCompany.currency.format(self.expenses)} in maintainance fees."

	def sell(self, refund=True):
		company = companies[self.ownedBy]
		company.assets.remove(self)
		_, _, _, buildCost = factoryTypes[self.type].values()
		if refund: company.balance += buildCost
		company.income -= (self.income * self.speed) - self.expenses



class Estate(Property):
	def __init__(self, ceo, location, new=True):
		company = companies[ceo]
		if location in propertyCosts and location in locationDesirability:
			buildCost = propertyCosts[location]
			income = locationDesirability[location]
			expenses = income * random.randint(1, 7) // 5

			if new:
				if buildCost > company.balance:
						raise NotEnoughMoneyException(f"Balance: {company.currency.format(company.balance)} < Cost: {company.currency.format(buildCost)}")

				company.balance -= buildCost

			super().__init__(company.owner, income, expenses, location)
			company.assets.append(self)
			company.income += self.income - self.expenses

		else:
			raise InvalidLocationException(f"Location [{location}] not in list of locations.")

	def __repr__(self):
		company = companies[self.ownedBy]
		return f"<Estate: [OWNER: {self.ownedBy}, LOCATION: {self.location}, INCOME: {company.currency}{self.income}, EXPENSES: {company.currency}{self.expenses}]>"

	def format(self):
		company = companies[self.ownedBy]
		return f"Estate located in {self.location.capitalize()}, earning {company.currency.format(self.income)} in rent and costing {company.currency.format(self.expenses)} in maintainance fees."

	def sell(self, refund=True):
		company = companies[self.ownedBy]
		company.assets.remove(self)
		buildCost = propertyCosts[self.location]
		if refund: company.balance += buildCost
		company.income -= self.income - self.expenses



class Vehicle:
	def __init__(self, ceo, price, new=True):
		company = companies[ceo]
		if new:
			if company.balance < price:
				raise NotEnoughMoneyException(f"Balance: {company.currency.format(company.balance)} < Cost: {company.currency.format(price)}")
			company.balance -= price
		self.ownedBy = company.owner
		self.value = price
		self.age = 0
		company.assets.append(self)
		company.equity += self.value

	def __repr__(self):
		return f"<Vehicle: [OWNER: {self.ownedBy}, VALUE: {self.value}, AGE: {self.age}yrs]"

	def format(self):
		company = companies[self.ownedBy]
		return f"Car worth {company.currency.format(self.value)} that is {self.age} Year{'s' if self.age != 1 else ''} old."

	def sell(self, refund=True):
		company = companies[self.ownedBy]
		company.assets.remove(self)
		if refund: company.balance += self.value



class Company:
	def __init__(self, user, name, real=False):
		self.owner = user
		self.name = name
		self.balance = 15000.0
		self.assets = []
		self.age = 0
		randC = random.randint(0, 4)
		self.currency = Currency(("£","€","$","kr","CAD")[randC], (True, True, True, False, True)[randC], (",",".",","," ",",")[randC], (".",",",".",",",".")[randC])
		self.real = real
		self.debts = {}
		self.loans = {}
		self.income = 0.0

		self.equity = self.balance
		self.liability = 0.0

	def __repr__(self):
		return f"<Company: [CEO: {self.owner}, NAME: {self.name}, BALANCE: {self.currency}{self.balance}, NUM-ASSETS: {len(self.assets)}, REAL: {self.real}]>"

	def format(self):
		return f"{self.name} is owned by {self.owner if self.real else 'DThree'}, with {self.currency.format(self.balance)} in the bank, {len(self.assets)} assets, {len(self.debts)} incoming loans and {len(self.loans)} outgoing loans."

	def toRow(self):
		return {
			"owner": self.owner,
			"name": self.name,
			"balance": self.balance,
			"assets": json.dumps([prop.__dict__ for prop in self.assets]),
			"debts": json.dumps(self.debts),
			"loans": json.dumps(self.loans),
			"age": self.age,
			"currency": json.dumps(self.currency.toRow()),
			"real": 'T' if self.real else 'F',
		}


	

def rowToCompany(row):
	company = Company(row["owner"], row["name"], real=row["real"]=="T")
	companies[row["owner"]] = company
	company.balance = float(row["balance"])

	assetsData = json.loads(row["assets"].replace('""', '"').strip('"'))
	currencyData = json.loads(row["currency"])
	sep = currencyData.get("seperator", 44)  #, Default
	delim = currencyData.get("delimiter", 46)  #. Default
	company.currency = Currency(currencyData["symbol"], currencyData["prefix"]=="T", chr(sep), chr(delim)) #Seperator and Delimiter are saved as ASCII codes to prevent , from interfering, for example.

	company.debts = json.loads(row["debts"])
	company.loans = json.loads(row["loans"])

	company.age = int(row["age"])

	for assetData in assetsData:
		if "speed" in assetData:  #Only factories have speed.
			factory = Factory(row["owner"], assetData["type"], new=False)
			factory.income = assetData["income"]
			factory.expenses = assetData["expenses"]

		elif "location" in assetData:  #Estates have location.
			estate = Estate(row["owner"], assetData["location"], new=False)
			estate.income = assetData["income"]
			estate.expenses = assetData["expenses"]

		else: #Vehicles have neither.
			vehicle = Vehicle(row["owner"], assetData["value"], new=False)




def readCSV(file_path):
	global companies
	companies = {}
	with open(file_path, mode="r") as file:
		reader = csv.DictReader(file)
		for row in reader:
			rowToCompany(row)
			



def writeCSV(file_path):
	global companies
	with open(file_path, mode="w", newline="") as file:
		fieldnames = ["owner", "name", "balance", "assets", "debts", "loans", "age", "currency", "real"]
		writer = csv.DictWriter(file, fieldnames=fieldnames)
		writer.writeheader()
		for user, company in companies.items():
			writer.writerow(company.toRow())



def createFakeCompany():
	fakeCEOName = f"_{round(time.time()*1000)}"
	with open("textFiles/fakeCompanyNames.txt", "r") as nameFile:
		randomName = random.choice(nameFile.readlines())
	fakeCompany = Company(fakeCEOName, randomName.strip())

	rand1 = random.randint(-5000,250000)
	fakeCompany.balance += rand1

	companies[fakeCEOName] = fakeCompany

	#Randomised Assets
	for _ in range(random.randint(2,5)):
		try:
			Factory(fakeCEOName, random.choice(list(factoryTypes.keys())))
		except NotEnoughMoneyException:
			break
	for _ in range(random.randint(0,3)):
		try:
			Estate(fakeCEOName, random.choice(list(locationDesirability.keys())))
		except NotEnoughMoneyException:
			break
	for _ in range(random.randint(0,1)):
		try:
			Vehicle(fakeCEOName, random.randint(250, 15000))
		except NotEnoughMoneyException:
			break

	rand2 = random.randint(0, 5000)
	fakeCompany.balance += rand2
	fakeCompany.equity += rand1 + rand2

	return fakeCompany


def forceUnBusyFunc():
	global busy
	print(f"ECON Is currently {'Busy' if busy else 'Not Busy'}, set to Not Busy")
	busy = False


def grantMoney(who, amount, ceo=True, company=False):
	global companies
	if ceo and who in list(companies.keys()):
		companies[who].balance += amount
		companies[who].equity += amount
		print(f"Granted {companies[who].name} {companies[who].currency.format(amount)}.")
	elif company:
		found = False
		for ceo, thisCompany in companies:
			if thisCompany.name.lower() == who:
				thisCompany.balance += amount
				thisCompany.equity += amount
				found = True
				print(f"Granted {thisCompany.name} {thisCompany.currency.format(amount)}.")

		if not found:
			print(f"Could not find company called {who}")
	elif not (ceo or company):
		print(f"Unknown: {who}")
	else:
		print(f"Could not find user called {who}")




readCSV("data/econ.csv")


async def econIterate(message, messageData, forceRandomEvent=False, output=True, forceUnBusy=False):
	global pendingRequest, pendingAmount, busy

	if not messageData.startswith("/econ"): return

	user = str(message.author)
	if messageData.startswith("/econ save"):
		writeCSV("data/econ.csv")
		replyMessage(message, "Successfully saved to econ.csv")
		return

	if busy and not forceUnBusy:
		if output:
			await replyMessage(message, "ECON is currently busy; Please try again shortly.", ping=True)
		return


	try:

		if not forceUnBusy: busy = True

		commandSections = messageData.split(" ")[1:]
		status = ""

		if user in companies.keys(): #User already has a company.
			updateTime = True
			userCompany = companies[user]

			if (pendingRequest is not None) and (commandSections[0] in ("accept", "deny", "yes", "no")):
				if commandSections[0] in ("accept", "yes"): #Accepted
					relevantCompany = companies[pendingRequest]
					if pendingAmount > 0: #Add to debts
						status += f"Accepted loan from {relevantCompany.name}, with value {relevantCompany.currency.format(pendingAmount)}"
						userCompany.debts[pendingRequest] = pendingAmount
						userCompany.balance += pendingAmount
						relevantCompany.balance -= pendingAmount
						pendingAmount, pendingRequest = 0, None
						userCompany.liability += pendingAmount

					elif pendingAmount < 0: #Add to loans
						status += f"Granted loan to {relevantCompany.name}, with value {userCompany.currency.format(-pendingAmount)}"
						userCompany.loans[pendingRequest] = pendingAmount
						userCompany.balance -= pendingAmount
						relevantCompany.balance += pendingAmount
						pendingAmount, pendingRequest = 0, None
						userCompany.liability -= pendingAmount

				else:
					status += f"Request was denied!"


			elif pendingRequest is None:
				try:
					match commandSections[0]:
						case "buy" | "new": #Buy a new property if valid. (/econ buy industry valuables)
							match commandSections[1]:
								case "factory" | "industry":
									newAsset = Factory(user, commandSections[2])

								case "estate" | "house":
									newAsset = Estate(user, commandSections[2])

								case "vehicle" | "car":
									newAsset = Vehicle(user, round(float(commandSections[2]),2))

								case _:
									newAsset = None


							if newAsset != None:
								status += f"## ***New {userCompany.currency.format(commandSections[2]) if isinstance(newAsset, Vehicle) else str(commandSections[2]).capitalize()} {commandSections[1].capitalize()} was bought!***\n"


						case "sell" | "remove": #Sell one of a property, if present. (/econ sell factory goods) for example.
							assetType = None
							match commandSections[1]:
								case "factory" | "industry":
									if commandSections[2] in factoryTypes:
										assetType = Factory

								case "estate" | "house":
									if commandSections[2] in locationDesirability:
										assetType = Estate

								case "vehicle" | "car":
									assetType = Vehicle

										
							if assetType != None:
								for prop in userCompany.assets:
									if isinstance(prop, assetType):
										prop.sell()
										status += f"## ***Sold one {commandSections[1]}!***\n"
										break
										#Only sell 1.


						case "view" | "list": #View company assets. (/econ view all) shows all assets.
							updateTime = False
							if commandSections[1] in ("loans", "debts", "debt"): #Show current loans and debts.
								status += f"{userCompany.name}'s debts & loans;"
								for otherCEO, debt in userCompany.debts.items():
									status += f"- {companies[otherCEO].name}: {userCompany.currency.format(debt)}"

								for otherCEO, loan in userCompany.loans.items():
									status += f"- {companies[otherCEO].name}: {userCompany.currency.format(loan)}"


							elif commandSections[1] in ("others", "companies", "market"): #Show all companies.
								for ceo, company in companies.items():
									status += f"- {company.format()}\n"


							elif commandSections[1] in ("leaderboard", "leaders", "scores", "score", "top"): #Pseudo-Leaderboard by stats.
								companyList = list(companies.values())
								status += f"## Companies ranked by {commandSections[2]}:\n"
								match commandSections[2]:
									case "balance":
										companyList.sort(key=lambda x: x.balance)
									case "age":
										companyList.sort(key=lambda x: x.age)
									case "assets":
										companyList.sort(key=lambda x: len(x.assets))
								companyList.reverse()
								for Idx, company in enumerate(companyList):
									status += f"{Idx+1}: {company.format()}\n"



							else: #Show company assets.
								status += f"{userCompany.name}'s assets;\n"
								assetsFound = False
								userCompany.equity = userCompany.balance
								for prop in userCompany.assets:
									if isinstance(prop, Factory) and commandSections[1] in ("factories", "production", "manufacturing", "industry", "properties", "all"):
										status += f"- {prop.format()}\n"
										userCompany.equity += prop.value

									if isinstance(prop, Estate) and commandSections[1] in ("estates", "houses", "homes", "properties", "all"):
										status += f"- {prop.format()}\n"
										userCompany.equity += prop.value

									if isinstance(prop, Vehicle) and commandSections[1] in ("vehicles", "cars", "all"):
										status += f"- {prop.format()}\n"
										userCompany.equity += prop.value


						case "forfeit" | "bankruptcy" | "restart": #Completely remake company. (/econ forfeit) completely clears your company and restarts you at 0.
							updateTime = False
							newCompany = Company(user, removeNonASCII(message.content.strip()).replace("/econ forfeit ", "") .replace("/econ bankruptcy ", "").replace("/econ restart ", ""), True)
							companies[user] = newCompany


						case "currency":
							updateTime = False
							if len(commandSections) < 5:
								status += "You need to use `/econ currency [new symbol(s)] [start/end] [seperator (i.e. ',')] [decimal marker (i.e. '.')]`"


							else:
								newCurrency = removeNonASCII(commandSections[1])
								if newCurrency == "":
									status += "Your new currency cannot be blank, or use non-ASCII characters."


								else:
									prefix = False
									if commandSections[2] not in ("start", "end", "pre", "post"):
										status += "You need to use 'start'/'pre' or 'end'/'post' to specify where the currency symbol is placed."


									else:
										prefix = commandSections[2] in ("start", "pre")
										seperator = removeNonASCII(commandSections[3]).replace("_", " ")
										if newCurrency == "":
											status += "Your seperator cannot be blank, or use non-ASCII characters."


										else:
											decimalMarker = removeNonASCII(commandSections[4]).replace("_", " ")
											if newCurrency == "":
												status += "Your decimal marker cannot be blank, or use non-ASCII characters."
											

											else:
												status += f"Successfully set {userCompany.name}'s currency to use {'prefix' if prefix else 'postfix'} {newCurrency}.\nExample: {newCurrency if prefix else ''}16{seperator}777{seperator}213{decimalMarker}00{'' if prefix else newCurrency}"
												userCompany.currency = Currency(newCurrency, prefix, seperator, decimalMarker)





						case "rename":
							updateTime = False
							newName = removeNonASCII(message.content.strip()).replace("/econ rename ", "")
							if newName != None and newName != "":
								status += f"{userCompany.name} was successfully changed to {newName}."
								userCompany.name = newName
							else:
								status += f"Something went wrong, {userCompany.name}'s name was not changed. Only use ASCII characters, and remember the syntax is `/econ rename [new name]`"


						case "wait3" | "wait-3":
							output = False
							for i in range(3):
								await econIterate(message, "/econ wait", output=i==2, forceUnBusy=True)


						case "loan" | "debt":
							match commandSections[1]:
								case "repay":
									if len(userCompany.debts.keys()) > 0:
										for otherCEO, debt in userCompany.debts.items():
											if companies[otherCEO].name.lower() == commandSections[2] and userCompany.balance > debt:
												userCompany.balance -= debt
												del userCompany.debts[otherCEO]
												userCompany.liability += debt

									else:
										status += "You do not have any new debts to pay."

								case "request":
									if len(userCompany.loans.keys()) > 0:
										for otherCEO, loan in userCompany.loans.items():
											if companies[otherCEO].name.lower() == commandSections[2] and companies[otherCEO].balance > loan:
												userCompany.balance += loan
												status += f"Loan of value {userCompany.currency}{loan} was repaid by {companies[otherCEO].name}"
												del userCompany.loans[otherCEO]
												userCompany.liability -= loan

									else:
										status += "You do not have any pending loans."

								case "view" | "list":
									if commandSections[1] in ("loans", "debts", "debt"):
										status += "Debts: (You owe money)"
										for otherCEO, debt in userCompany.debts.items():
											status += f"- {companies[otherCEO].name}: {userCompany.currency}{debt}"

										status += "Loans: (You are owed money)"
										for otherCEO, loan in userCompany.loans.items():
											status += f"- {companies[otherCEO].name}: {companies[otherCEO].currency}{loan}"



						case "help": #Help page of some sort around definitions and commands.
							updateTime = False
							helpMSG = f"""
For help with commands, use `/econ help commands`.
For help with buying new assets, use `/econ help buy`
For help with the data shown each turn, use `/econ help data`
For help with random events, use `/econ help events`
For further questions, please ask \_\_dau\_\_ directly.

-# *Economy simulation is isolated from other users at this time. No personal information is stored.*
								"""
							if len(commandSections) == 1:
								pass

							elif commandSections[1] in ("buy",):
									helpMSG = f"""
There are multiple options to buy.
Industries/Factories can be one of multiple types, and provide income on a steady basis depending on what they produce.
Homes/Estates can be in one of multiple locations, which each have their own desirability and build costs associated.
Cars/Vehicles are bought for a set price, and depreciate in value over time.

Further information on each of these types can be found via `/help [type]` (for example, `/help cars`)
The general command for buying is formatted like so;
- Factories: `/econ buy factory [type of factory]`
- Estates: `/econ buy estate [location to build at]`
- Vehicles: `/econ buy car [Price of car to buy]`
										"""

							elif commandSections[1] in ("sell",):
									helpMSG = f"""
Selling an asset returns its value to your company's balance, and removes it from your available assets.
I.e. selling a factory returns the build costs to you, and it will not provide further income to you or be listed.
Cars depreciate as they age, but generate no expenses so can be used as short-term money sinks.

The general format for selling an asset is as seen below;
- Factories: `/econ sell factory [type of factory]`
- Estates: `/econ sell estate [location of estate]`
- Vehicles: `/econ sell car`

This will sell 1 (one) instance of an asset that matches this description.
										"""

							elif commandSections[1] in ("currency",):
									helpMSG = f"""
You may change the currency your company uses via `/econ currency [New symbol]`
The default is £, but any UTF-8 compliant symbol (or word) is accepted.
Be reasonable with your choice of currency, as it is shown often.
										"""

							elif commandSections[1] in ("loans", "debts"):
									helpMSG = f"""
Your loans and debts are listed here.
You can pay them back: `/econ debts repay [Other Company's Name]` (If you have the balance)
You can request they pay it back: `/econ loans request [Other Company's Name]` (If they have the balance)
You can view all active loans/Debts: `/econ debts view` or `/econ loans view` (Shows all of both)
										"""

							elif commandSections[1] in ("random", "events", "events"):
									helpMSG = f"""
Random events start occurring after 10 years. They have a small chance of occurring each turn.
There are multiple random events, of which the most notable are;
- A Location burns down: All estates at that location will be lost, and funds are lost in any value kept there.
- A Factory collapes: A factory collapses, losing that factory, its income and any costs associated with it.
- A Factory becomes more/less efficient: Earns more or less each turn due to this. Stacks over time. Applies to 1 factory at a time.
- Another company offers you a loan: You will be in debt to them, your balance will increase, and must pay it back - Interest applies.
- Another company requests a loan from you: They will be in debt to you, your balance will decrease, and interest applies.
										"""

							elif commandSections[1] in ("data",):
									helpMSG = f"""
CEO: User who owns this company
Name: Name of the company
Balance: How much money the company has in the bank
Net Worth: Balance + all value of assets
Number of Assets, Number of Debts & Number of Loans: Shows how many of each if more than 0.
										"""

							elif commandSections[1] in ("factory", "factories", "industry", "industries"):
									helpMSG = f"""
Types of factory:
										"""
									for facType, data in factoryTypes.items():
										helpMSG += f"- {facType.capitalize()}: Income = {userCompany.currency.format(data['income'])}, Expenses = {userCompany.currency.format(data['expenses'])}, Efficiency = {round(100*data['speed'])}%, Construction Cost: {userCompany.currency.format(data['buildCost'])}\n"
									helpMSG += f"""
Each have their own speeds, incomes, and so on. A Factory can only have 1 type at any time.
Factories can be bought using `/econ buy factory [type]`
									"""

							elif commandSections[1] in ("estate", "estates", "homes", "houses"):
									helpMSG = f"""
Locations for estates:
										"""
									for location, desirability in locationDesirability.items():
										if location == "industrial district": continue
										helpMSG += f"- {location.capitalize()}: Rent: {userCompany.currency.format(desirability)}, Construction costs: {userCompany.currency.format(propertyCosts[location])}\n"
									helpMSG += f"""
Each have their own rents, expenses, and so on. An estate can only be in 1 location.
Estates can be bought using `/econ buy estate [location]`
									"""

							elif commandSections[1] in ("vehicle", "vehicles", "car", "cars"):
									helpMSG = f"""
Cars have a value in which they are purchased for, and depreciate at a fixed rate (-{100-round(100*depreciationRate)}%/Year)
Every year they lose value slowly, and can be sold for this value at any time.
Cars can be bought using `/econ buy car [value]`
										"""

							elif commandSections[1] in ("command", "commands", "cmd", "cmds"):
									helpMSG = f"""
Main commands;
- `/econ buy`: Buy new assets
- `/econ sell`: Sell assets for money
- `/econ view`: View some sub-set of your assets
- `/econ currency`: Change your company's currency
- `/econ loan` or `/econ debt`: View your current loans and debts. Pay them from here.
- `/econ forfeit` or `/econ bankruptcy`: Start again from 0, clear your company, etc. Requires new name as end of command.
- `/econ help`: Get help with a specific category
										"""


							if output: await replyMessage(message, helpMSG, ping=True)


							


					if updateTime:
						toDelete = []
						for owner, thisCompany in companies.items():
							if thisCompany.real and owner != user: continue
							thisCompany.age += 1

							thisCompany.balance += thisCompany.income

							thisCompany.balance = round(thisCompany.balance, 2)
							if thisCompany.balance < -15000 and not thisCompany.real:
								toDelete.append(thisCompany.owner)
								status += f"## ***{thisCompany.name} has gone bankrupt! All loans and debts to them have been cancelled!\n***"
								continue

						for ceo in toDelete:
							del companies[ceo]

						for otherCEO, debt in userCompany.debts.items():
							userCompany.debts[otherCEO] = debt * loanInflation
						for otherCEO, loan in userCompany.loans.items():
							userCompany.loans[otherCEO] = loan * loanInflation



						if userCompany.age > 10 or forceRandomEvent:
							if random.randint(0, 5) == 0 or forceRandomEvent: #Random event!
								eventType = random.randint(0, 8)
								match eventType:
									case 0: #Factory is destroyed
										factories = []
										for prop in userCompany.assets:
											if isinstance(prop, Factory):
												factories.append(prop)

										if len(factories) != 0:
											burnedFactory = random.choice(factories)
											status += f"## ***A {burnedFactory.type} factory you own has burned down!\n"
											burnedFactory.sell(refund=False)
										del factories

									case 1: #Estate location is destroyed
										locations = list(locationDesirability.keys())
										locations.remove("industrial district") #Don't destroy industrial district.
										burnedLocation = random.choice(locations)
										status += f"## ***{burnedLocation.capitalize()} has burned down! All assets in {burnedLocation.capitalize()} were lost!***\n"
										for prop in userCompany.assets:
											if isinstance(prop, Estate):
												if prop.location == burnedLocation:
													prop.sell(refund=False)

									case 2: #Fake company collapses
										fakeCompanies = []
										for company in companies.values():
											if not company.real:
												fakeCompanies.append(company)

										if len(fakeCompanies) != 0:
											fakeCompanies.sort(key=lambda x: x.balance)
											status += f"## ***{fakeCompanies[0].name} has collapsed! All loans and debts to them have been cancelled!***\n"
											del companies[fakeCompanies[0].owner]


									case 3: #New fake company is created
										newCompany = createFakeCompany()
										status += f"## ***{newCompany.name} was founded!***\n"

									case 4: #Factory is less efficient
										factories = []
										multiplier = 0.85 + (random.randint(0, 10) / 100) #0.85 - 0.95x
										for prop in userCompany.assets:
											if isinstance(prop, Factory):
												factories.append(prop)

										if len(factories) != 0:
											nerfedFactory = random.choice(factories)
											userCompany.income -= (nerfedFactory.income * nerfedFactory.speed) - nerfedFactory.expenses
											status += f"## ***A {nerfedFactory.type} factory you own has decreased in efficiency by {multiplier}x!***\n"
											idx = userCompany.assets.index(nerfedFactory)
											userCompany.assets[idx].speed *= multiplier
											userCompany.income += (nerfedFactory.income * nerfedFactory.speed * multiplier) - nerfedFactory.expenses
										del factories

									case 5: #Factory becomes more efficient
										factories = []
										multiplier = 1.05 + (random.randint(0, 10) / 100) #1.05 - 1.15x
										for prop in userCompany.assets:
											if isinstance(prop, Factory):
												factories.append(prop)

										if len(factories) != 0:
											improvedFactory = random.choice(factories)
											userCompany.income -= (improvedFactory.income * improvedFactory.speed) - improvedFactory.expenses
											status += f"## ***A {improvedFactory.type} factory you own has increased in efficiency by {multiplier}x!***\n"
											idx = userCompany.assets.index(improvedFactory)
											userCompany.assets[idx].speed *= multiplier
											userCompany.income += (improvedFactory.income * improvedFactory.speed * multiplier) - improvedFactory.expenses
										del factories

									case 6: #Car gets destroyed
										cars = []
										for prop in userCompany.assets:
											if isinstance(prop, Vehicle):
												cars.append(prop)

										if len(cars) != 0:
											destroyedCar = random.choice(cars)
											status += f"## ***A {destroyedCar.age} year old car you own has crashed! Value lost: {userCompany.currency.format(destroyedCar.value)}***\n"
											userCompany.equity -= destroyedCar.value
											destroyedCar.sell(refund=False)
										del cars

									case 7: #Random offer to GIVE money (added to debts)
										fakeCompanies = []
										for company in companies.values():
											if not company.real:
												fakeCompanies.append(company)

										if len(fakeCompanies) != 0:
											loaner = random.choice(fakeCompanies)
											loanAmount = round(loaner.balance / random.randint(2, 5), 2)
											status += f"## ***{loaner.name} is offering you {loaner.currency.format(loanAmount)}.***\n  - Reply with `/econ accept` or `/econ deny` to clear offer.\n"
											pendingRequest = loaner.owner
											pendingAmount = loanAmount #Added to debts.
										del fakeCompanies
										


									case 8: #Random request to TAKE money (added to loans)
										fakeCompanies = []
										for company in companies.values():
											if not company.real:
												fakeCompanies.append(company)

										if len(fakeCompanies) != 0:
											requestor = random.choice(fakeCompanies)
											loanAmount = round(userCompany.balance / (random.randint(2, 5)), 2)
											status += f"## ***{requestor.name} is requesting a loan of {userCompany.currency.format(loanAmount)}.***\n  - Reply with `/econ accept` or `/econ deny` to clear offer.\n"
											pendingRequest = requestor.owner
											pendingAmount = -loanAmount #Added to loans.
										del fakeCompanies

						
						status += f"""
	# Company Stats for [Year {userCompany.age // 12}, Month {userCompany.age % 12}];
	```- CEO: {message.author.display_name}
– Name: {userCompany.name}
– Balance: {userCompany.currency.format(userCompany.balance)}
– Equity: {userCompany.currency.format(userCompany.equity)}
– Liability: {userCompany.currency.format(userCompany.liability)}
– Number of assets: {len(userCompany.assets)}
						""".strip()
						factories, estates, vehicles = 0, 0, 0

						if len(userCompany.assets) > 0:
							for prop in userCompany.assets:
								if isinstance(prop, Factory): factories += 1
								elif isinstance(prop, Estate): estates += 1
								elif isinstance(prop, Vehicle):
									userCompany.equity -= prop.value
									prop.value *= depreciationRate
									userCompany.equity += prop.value
									vehicles += 1


						if factories > 0:
							status += f"""\n└ {factories} {'factory' if factories == 1 else 'factories'}"""
						if estates > 0:
							status += f"""\n└ {estates} {'estate' if estates == 1 else 'estates'}"""
						if vehicles > 0:
							status += f"""\n└ {vehicles} {'car' if vehicles == 1 else 'cars'}"""
						status += f"""\n- Number of debts active: {len(userCompany.debts.keys())}"""
						if len(userCompany.debts) > 0:
							for coName, debt in userCompany.debts.items():
								status += f"""\n└ {coName}: {userCompany.currency.format(debt)}\n"""
						status += f"""\n- Number of loans active: {len(userCompany.loans.keys())}"""
						if len(userCompany.loans) > 0:
							for coName, loan in userCompany.loans.items():
								status += f"""\n└ {coName}: {userCompany.currency.format(loan)}\n"""
						status += "```\n\n"

					if len(status) > 0:
						if output: await replyMessage(message, status, ping=True)


				except NotEnoughMoneyException:
					errorMessage = f"You do not have enough money (Current: {userCompany.currency.format(userCompany.balance)}) to {commandSections[0]} {'an' if commandSections[1] == 'estate' else 'a'} {commandSections[1]}."
					if output: await replyMessage(message, errorMessage, ping=True)
					if not forceUnBusy: busy = False

				except InvalidTypeException:
					errorMessage = f"{commandSections[2]} was not a valid type of factory. Options;\n"
					for validType in factoryTypes.keys():
						errorMessage += f"- {validType}\n"
					if output: await replyMessage(message, errorMessage, ping=True)
					if not forceUnBusy: busy = False

				except InvalidLocationException:
					errorMessage = f"{commandSections[2]} was not a valid location. Options;\n"
					for validLocation in locationDesirability.keys():
						errorMessage += f"- {validLocation}\n"
					if output: await replyMessage(message, errorMessage, ping=True)
					if not forceUnBusy: busy = False


		else: #Create new company.

			if commandSections[0] == "create":
				newCompany = Company(user, removeNonASCII(message.content.strip()).lower().replace("/econ create ", ""), True)
				companies[user] = newCompany
				if output: await replyMessage(message, f"""
{message.author.display_name}, you now own {newCompany.name}
– Your starting balance is {newCompany.currency.format(newCompany.balance)}
– You start with 0 loans, debts or assets.
– To change your currency, use `/econ currency [symbol(s) (ASCII only.)] [start/end (e.g. £10 vs 130kr)] [seperator (e.g. ',')] [decimal marker (e.g. '.')]`
└ To use a space for seperator or delimiter, use an underscore (e.g. _)
*Use `/econ help` if needed.*
					""", ping=True)


			elif commandSections[0] == "view":
				status = ""
				if commandSections[1] in ("others", "companies", "market"): #Show all companies.
					for ceo, company in companies.items():
						status += f"- {company.format()}\n"


				elif commandSections[1] in ("leaderboard", "leaders", "scores", "score", "top"): #Pseudo-Leaderboard by balance.
					companyList = list(companies.values())
					status += f"## Companies ranked by {commandSections[2]}:\n"
					match commandSections[2]:
						case "balance":
							companyList.sort(key=lambda x: x.balance)
						case "age":
							companyList.sort(key=lambda x: x.age)
						case "assets":
							companyList.sort(key=lambda x: len(x.assets))
						case "equity":
							companyList.sort(key=lambda x: x.equity)
					companyList.reverse()
					for Idx, company in enumerate(companyList):
						status += f"{Idx+1}: {company.format()}\n"

				if output: await replyMessage(message, status, ping=True)


			else:
				helpMSG = f"""
You currently do not have a company. To create one, send the following command;
`/econ create [Name of your Company]`
The name of your company can be any word, phrase or otherwise set of characters contained within ASCII.
Spaces are allowed, linebreaks are not.
					"""
				if output: await replyMessage(message, helpMSG, ping=True)


		if not forceUnBusy: busy = False

	except Exception as E:
		print(f"\a\n{E}\n")
		if not forceUnBusy: busy = False
		await replyMessage(message, f"## *An error occurred;*\n{str(E)}\n-# *Please wait.*", ping=True)


### Setup ###
"""
writeCSV("data/econ.csv", {}) #Clear CSV for testing.

for _ in range(3):
	createFakeCompany()
	time.sleep(0.05)
writeCSV("data/econ.csv", companies)
"""