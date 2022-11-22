import requests
import sys
import argparse
import subprocess

# Returns a function that tests if a relay 'r' is of type 't'
isType = lambda t: (lambda r: "type" in r and r["type"] == t)

# Returns a function that tests if a relay 'r' has country code 'c'
inCountry = lambda c: (lambda r: "country_code" in r and r["country_code"] == c)

# Returns a function that given a relay 'r', tests if it fits at least one of the conditions in 'filters'
filterOr = lambda filters: (lambda r: [f(r) for f in filters].count(True) > 0)

# Tests if a relay is not a bridge
notBridge = lambda r: not isType("bridge")(r)

def perror(err):
    print(err, file = sys.stderr)

def failure(err):
    perror(err)
    sys.exit(1)

def getRelays():
    try:
        relays = requests.get("https://api.mullvad.net/www/relays/all/").json()
    except:
        failure("Could not get relays")

    return relays

def parsePing(pingOutput):
    resultsLine = pingOutput.splitlines()[pingOutput.count("\n") - 1]

    if not resultsLine.startswith("rtt"):
        return None, None, None

    rtts = [float(v) for v in resultsLine.split(" ")[3].split("/")]

    return rtts[0], rtts[1], rtts[2]

def ping(addr, count):
    try:
        pingProcess = subprocess.run(["ping", addr, "-nqc", str(count)], capture_output = True)
    except:
        failure("The `ping` program could not be called")
    
    if pingProcess.returncode != 0:
        return None, None, None

    return parsePing(pingProcess.stdout.decode())

parser = argparse.ArgumentParser(
    prog = "mulping",
    description = "Batch pings utility for Mullvad VPN (not affiliated)",
)

relayConditions = [notBridge]

parser.add_argument("-c", "--country", action = "store", help = "Filter by country", nargs = "+", required = False)
parser.add_argument("-w", "--wireguard", action = "store_true", help = "Only select WireGuard servers")
parser.add_argument("-o", "--openvpn", action = "store_true", help = "Only select OpenVPN servers")

args = parser.parse_args()

if args.country != None:
	countryConditions = list(map(inCountry, args.country))

	countryFilter = filterOr(countryConditions)	
	relayConditions.append(countryFilter)

if args.openvpn: relayConditions.append(isType("openvpn"))
if args.wireguard: relayConditions.append(isType("wireguard"))

relays = getRelays()

relayCount = 0
latencies = []
for r in relays:
    skip = False
    for condition in relayConditions:
        if not condition(r):
            skip = True
            break
    if skip: continue
    
    relayCount += 1

    host = r["hostname"]
    address = r["ipv4_addr_in"]

    if not r["active"]:
        print(f"{host:15} -> inactive")
        continue

    _, rtt, _ = ping(address, 1)
    if rtt == None:
        perror(f"{host:15} -> error")
        continue

    print(f"{host:15} -> {rtt:.3f}ms")

    latencies.append((host, rtt))

if relayCount == 0:
    failure("The conditions specified resulted in no relays")

lowestLatency = min(latencies, key = lambda e: e[1])
maxLatency = max(latencies, key = lambda e: e[1])

print(f"\nHighest latency host: {maxLatency[0]} ({maxLatency[1]}ms)")
print(f"Lowest latency host: {lowestLatency[0]} ({lowestLatency[1]}ms)")
