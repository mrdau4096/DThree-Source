from duckduckgo_search import DDGS

def lookUp(query):
	results_dict = {}
	results = DDGS().text(query, max_results=50)

	headers = {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
	}

	accepted=0
	for result in results:
		try:
			url, title = result["href"], result["title"]
			if title is None or title.lower() == "access denied": title = "[Title Unavailable]"

			disallowed = False
			#Filted blocked words/phrases.
			with open("textFiles/bannedTitles.txt", "r") as badTitles:
				badTitleWords = badTitles.readlines()
			with open("textFiles/bannedURLs.txt", "r") as badURLs:
				badURLWords = badURLs.readlines()
			if any(banned.strip() in title.lower() for banned in badTitleWords):
				continue
			if any(banned.strip() in url.lower() for banned in badURLWords):
				continue

			accepted += 1
			results_dict[title] = url
			if accepted >= 3: break

		except Exception as e:
			print(e)
			pass

	return results_dict