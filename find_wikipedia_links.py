# Find all Wikipedia pages that link to legislink.org using the
# https://en.wikipedia.org/wiki/Template:USStat or https://en.wikipedia.org/wiki/Template:USPL
# templates.

import urllib.request, urllib.parse, urllib.error, json, re
import mwparserfromhell

# FUNCTIONS

import shelve
cache = shelve.open("find_wikipedia_links.cache", flag='c')

def query(url):
	url = "https://en.wikipedia.org/w/api.php?format=json&" + url
	if url in cache:
		return cache[url]
	response = urllib.request.urlopen(url)
	data = json.loads(response.read().decode("utf8"))
	cache[url] = data
	return data

def get_pages_that_embed(template_name):
	continue_arg = None
	while True:
		# Construct next page for query results.
		url = "action=query&list=embeddedin&einamespace=0&eifilterredir=nonredirects&eilimit=500"
		url += "&eititle="  + urllib.parse.quote(template_name)
		if continue_arg:
			# every iteration but the first
			url += "&eicontinue=" + continue_arg

		# Fetch.
		results = query(url)
		for page in results["query"]["embeddedin"]:
			yield page

		# Iterate by getting the next 'eicontinue' parameter
		# from the response body.
		try:
			continue_arg = results["continue"]["eicontinue"]
		except KeyError:
			# No more results. Don't iterate more.
			break

def get_page_content(pages, params, limit, extractfunc):
	# Go in chunks.
	pages = list(pages) # clone
	while len(pages) > 0:
		# Shift off items.
		this_batch = pages[:limit]
		del pages[:limit]

		# Query.
		url = "action=query"
		url += "&" + params
		url += "&pageids=" + "|".join(str(page["pageid"]) for page in this_batch)
		contents = query(url)
		page_data = contents["query"]["pages"]
		assert len(page_data) == len(this_batch)

		# Update the dicts given in the pages argument with the
		# information we just queried.
		for page in this_batch:
			queried_page_data = page_data[str(page["pageid"])]
			page.update(extractfunc(queried_page_data))

def get_legislink_links(page):
	for template in mwparserfromhell.parse(page["text"]).filter_templates():
		if template.name.strip().lower() == "uspl":
			yield "us-law/public/{}/{}".format(*(s.strip() for s in template.params))
		if template.name.strip().lower() == "usstat":
			yield "stat/{}/{}".format(*(s.strip() for s in template.params))
		if template.name.strip().lower() == "usstatute":
			if len(template.params) >= 2:
				yield "us-law/public/{}/{}".format(template.params[0], template.params[1])
			if len(template.params) >= 4:
				yield "stat/{}/{}".format(template.params[2], template.params[3])


# Query for matching pages.
pages =  list(get_pages_that_embed("Template: USPL"))
pages += list(get_pages_that_embed("Template: USStat"))
pages += list(get_pages_that_embed("Template: USStatute"))

# Uniqueify.
pages = [ { "pageid": pageid } for pageid in set(p["pageid"] for p in pages) ]

# Fetch wikitext for each page.
get_page_content(pages, "prop=revisions&rvprop=content", 50, lambda page : { "text": page["revisions"][0]["*"] })

# Look for template usage.
for page in pages:
	for item in get_legislink_links(page):
		print(item)
