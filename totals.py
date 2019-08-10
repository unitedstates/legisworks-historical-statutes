# Compute some totals by volume.

import glob, rtyaml, collections

volumes = collections.defaultdict(lambda : {
	"pages": 0,
	"congress": set(),
	"types": collections.defaultdict(lambda : 0),
})
types = collections.defaultdict(lambda : 0)

for f in sorted(glob.glob("data/*.yaml")):
	D = rtyaml.load(open(f))
	for d in D:
		if "congress" in d:
			volumes[d["volume"]]["congress"].add(d["congress"])
		if "npages" in d:
			volumes[d["volume"]]["pages"] += d["npages"]
		if "type" in d and ("private" not in d["type"]):
			types[d["type"]] += 1
			volumes[d["volume"]]["types"][d["type"]] += 1

# Put entry types in an order. Only take top types.
types = sorted(types, key = lambda k : -types[k])
types = types[:6]

# Output a table.
print("|" + "|".join(["Volume", "Congress", "Pages"] + types) + "|")
print("|" + "|".join(("-"*(len(c)-1)+":") for c in ["Volume", "Congress", "Pages"] + types) + "|")
for volume in sorted(volumes):
	print("|" + "|".join(
		[str(volume),
		 ",".join(str(c) for c in sorted(volumes[volume]["congress"])),
		 '{:,}'.format(volumes[volume]["pages"])
	    ]
	    + ['{:,}'.format(volumes[volume]["types"][t]) for t in types]
	    )
		+ "|")