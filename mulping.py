#!/bin/env python3

import os
import sys
import json
import argparse
import subprocess

from time import time
from random import randint

UNIX = "UNIX"
WINDOWS = "WINDOWS"

ON_WINDOWS = False
ON_UNIX = False

if "linux" in sys.platform or "darwin" in sys.platform:
  ON_UNIX = True
elif "win" in sys.platform:
  ON_WINDOWS = True
else:
  print("Unknown OS, assuming UNIX based")
  ON_UNIX = True

def failure(err):
    print(err, file = sys.stderr)
    sys.exit(1)

RELAYS_LINK = "https://api.mullvad.net/www/relays/all/"
RELAYS_FILE_UNIX = "/tmp/mulpingData"

if ON_UNIX:
  RELAYS_FILE = RELAYS_FILE_UNIX
  DEFAULT_TIMEOUT = 10
else:
  RELAYS_FILE = "C:\\Users\\" + os.getlogin() + "\\AppData\\Local\\Temp\\mulpingData"
  DEFAULT_TIMEOUT = 10000

TIMESTAMP_INDEX = 0

HOSTNAME = "hostname"
TYPE = "type"
ACTIVE = "active"
COUNTRY_CODE = "country_code"
COUNTRY_NAME = "country_name"
CITY_CODE = "city_code"
CITY_NAME = "city_name"
IPV4 = "ipv4_addr_in"
IPV6 = "ipv6_addr_in"
PROVIDER = "provider"
BANDWIDTH = "network_port_speed"
OWNED = "owned"
STBOOT = "stboot"
RTT = "round_trip_time"

WIREGUARD = "wireguard"
OPENVPN = "openvpn"
BRIDGE = "bridge"


#############################
# Relay filtering utilities #
#############################


# Returns a function that returns a function that tests
# if attribute 'a' in relay 'r' has value 'v'
eqAttr = lambda a: (lambda v: (lambda r: a in r and r[a] == v))

# Analogous
neqAttr = lambda a: (lambda v: (lambda r: a in r and r[a] != v))
geqAttr = lambda a: (lambda v: (lambda r: a in r and r[a] >= v))

# Returns a function that given a relay 'r', tests if it fits at least one of the conditions in 'filters'
filterOr = lambda filters: (lambda r: [f(r) for f in filters].count(True) > 0)

# Returns a function that given a relay 'r', tests if it fits all of the conditions in 'filters'
filterAnd = lambda filters: (lambda r: [f(r) for f in filters].count(False) == 0)

# Generates an aggregate filter with the 'aggregator' function using
# the conditions generated using 'getSubFilter' from the values in 'source' 
# and adds it to 'filters'
def getFilter(source, getSubFilter, aggregator, filters):
    conditions = list(map(getSubFilter, source))
    newFilter = aggregator(conditions)

    filters.append(newFilter)


#########################
# Relays data retrieval #
#########################


def fetchRelays():
    print("Fetching relays... ", end = "")
    sys.stdout.flush()

    # Only import the "requests" module here as it takes
    # significantly longer than the others
    import requests

    try:
        relays = requests.get(f"{RELAYS_LINK}").json()
    except:
        failure("Could not get relays")

    relays.insert(TIMESTAMP_INDEX, time())
    with open(RELAYS_FILE, "w") as f:
        json.dump(relays, f)
    del relays[TIMESTAMP_INDEX]

    print("done!\n")
    return relays

def loadRelays():
    with open(RELAYS_FILE, "r") as f:
        relays = json.loads(f.read())

    if not isinstance(relays[TIMESTAMP_INDEX], (float, int)):
        raise Exception

    # If the data is more than 12 hours old, fetch it again
    if time() - relays[TIMESTAMP_INDEX] >= 43200:
        raise Exception

    # Delete timestamp from final relay list
    del relays[TIMESTAMP_INDEX]

    return relays

def getRelays():
    if os.path.isfile(RELAYS_FILE):
        try:
            relays = loadRelays()
        except:
            relays = fetchRelays()
    else:
        relays = fetchRelays()

    return relays


##################
# Ping utilities #
##################


def parsePing(pingOutput, platform = UNIX):
    lines = pingOutput.splitlines()
    while "" in lines: lines.remove("")

    resultsLine = lines[len(lines) - 1]
    if platform == UNIX:
      try:
          resultsLine = resultsLine[resultsLine.rfind("="):]
          rtts = [float(v) for v in resultsLine.split(" ")[1].split("/")]
      except:
          return None, None, None
    else:
      resultsLine = list(map(lambda l: l[l.index("=") + 2:l.index("ms")], resultsLine.split(",")))
      rtts = [float(v) for v in resultsLine]

    return rtts[0], rtts[1], rtts[2]

def ping(addr, count, timeout = DEFAULT_TIMEOUT, ipv6 = False):
    try:
        if ON_UNIX:
          # e.g.: ping 0.0.0.0 -nqc 1 -W 10
          pingCommand = ["ping", addr, "-nqc", str(count), "-W", str(timeout)]
        else:
          # e.g.: ping 0.0.0.0 -n 1 -w 10
          pingCommand = ["ping", addr, "-n", str(count), "-w", str(timeout)]

        if ipv6: pingCommand.append("-6")
        pingProcess = subprocess.run(pingCommand, capture_output = True)
    except:
        failure("The `ping` program could not be called")

    if pingProcess.returncode != 0:
        return None, None, None

    return parsePing(pingProcess.stdout.decode(), platform = UNIX if ON_UNIX else WINDOWS)


#####################
# Mullvad utilities #
#####################


def mullvadChangeRelay(hostname):
    try:
        mullvadProcess = subprocess.run(["mullvad", "relay", "set", "location", hostname])

        if mullvadProcess.returncode != 0:
            raise Exception
    except:
        failure(f"An error occurred while trying to change the Mullvad relay options to hostname {hostname}")


######################
# Printing utilities #
######################


noFormat = lambda i: i
noPrint = lambda *_: None

relayTypeFormat = {
    WIREGUARD: "WireGuard",
    OPENVPN: "OpenVPN",
    BRIDGE: "Bridge"
}

ITEMS_FORMAT = {
    HOSTNAME: noFormat,
    IPV4: noFormat,
    IPV6: noFormat,
    COUNTRY_CODE: noFormat,
    CITY_CODE: noFormat,
    PROVIDER: noFormat,
    RTT: lambda rtt: f"{rtt:.3f}ms",
    OWNED: lambda o: "Owned" if o else "Rented",
    BANDWIDTH: lambda b: f"{b} Gbps",
    COUNTRY_NAME: noFormat,
    CITY_NAME: noFormat,
    STBOOT: lambda s: "RAM" if s else "Disk",
    TYPE: lambda t: relayTypeFormat[t] if t in relayTypeFormat else "Unknown"
}

ITEMS_IDS = {
    "h": HOSTNAME,
    "4": IPV4,
    "6": IPV6,
    "c": COUNTRY_CODE,
    "C": CITY_CODE,
    "p": PROVIDER,
    "l": RTT,
    "O": OWNED,
    "b": BANDWIDTH,
    "cf": COUNTRY_NAME,
    "Cf": CITY_NAME,
    "s": STBOOT,
    "t": TYPE
}

attributesShort = [HOSTNAME, RTT]
attributesLong = [HOSTNAME, RTT, COUNTRY_NAME, CITY_NAME, PROVIDER, OWNED, STBOOT]

def getAttributes(formatList):
    attributes = []
    for id in formatList:
        if id not in ITEMS_IDS:
            failure(f"Unknown attribute identifier: {id}")

        attributes.append(ITEMS_IDS[id])

    return attributes

def getSpacing(relays, items):
    spaces = {}
    singleItemSpace = lambda i: (lambda r: len(ITEMS_FORMAT[i](r[i])))

    for item in items:
        if item == RTT: continue
        spaces[item] = singleItemSpace(item)(max(relays, key = singleItemSpace(item)))

    spaces[RTT] = 10
    return spaces

getSpacingList = lambda i, spacing: [spacing[item] if item in spacing else None for item in i]

def printBox(items, start, end, middle, regular):
    if items == []: return ""

    box = start
    for i in items:
        box += regular * (i + 2) + middle

    box = box[0:len(box) - 1] + end

    print(box)

def printLine(relay, attributes, itemsSpaces, wall):
    print(f"{wall}", end = "")
    for attribute in attributes:
        if not attribute in itemsSpaces or attribute not in ITEMS_FORMAT:
            failure("Unknown attribute received by printing function")

        if relay[attribute] == None:
            print(f" {'error':{itemsSpaces[attribute]}} {wall}", end = "")
        else:
            print(f" {ITEMS_FORMAT[attribute](relay[attribute]):{itemsSpaces[attribute]}} {wall}", end = "")

    print()


########
# Main #
########

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog = "mulping",
        description = "Batch pings utility for Mullvad VPN (not affiliated)",
    )

    relayConditions = [
        neqAttr(TYPE)(BRIDGE),
        eqAttr(ACTIVE)(True)
    ]

    parser.add_argument("-c", "--country", action = "store", help = "Only select servers located in the countries specified", nargs = "+", metavar = "country_code")
    parser.add_argument("-cn", "--country-not", action = "store", help = "Exclude servers located in the countries specified", nargs = "+", metavar = "country_code")
    parser.add_argument("-C", "--city", action = "store", help = "Only select servers located in the cities specified", nargs = "+", metavar = "city_code")
    parser.add_argument("-Cn", "--city-not", action = "store", help = "Exclude servers located in the cities specified", nargs = "+", metavar = "city_code")
    parser.add_argument("-H", "--hostname", action = "store", help = "Only select the specified servers", nargs = "+", metavar = "hostname")
    parser.add_argument("-Hn", "--hostname-not", action = "store", help = "Exclude the specified servers", nargs = "+", metavar = "hostname")
    parser.add_argument("-p", "--provider", action = "store", help = "Only select servers using the specified providers", nargs = "+", metavar = "provider")
    parser.add_argument("-pn", "--provider-not", action = "store", help = "Exclude servers using the specified providers", nargs = "+", metavar = "provider")
    parser.add_argument("-w", "--wireguard", action = "store_true", help = "Only select WireGuard servers")
    parser.add_argument("-o", "--openvpn", action = "store_true", help = "Only select OpenVPN servers")
    parser.add_argument("-s", "--stboot", action = "store_true", help = "Only select stboot servers")
    parser.add_argument("-O", "--owned", action = "store_true", help = "Only select servers owned by Mullvad")
    parser.add_argument("-b", "--bandwidth", action = "store", help = "Only select servers that have at least this bandwidth speed (Gbps)", metavar = "bandwidth")

    parser.add_argument("-v", "--verbose", action = "store_true", help = "Show more relay attributes in the results")
    parser.add_argument("-f", "--format", action = "store", help = "Specify the relay attributes to print in the results", nargs = "+", metavar = "identifier")
    parser.add_argument("-q", "--quiet", action = "store_true", help = "Don't show relay results box")
    parser.add_argument("-d", "--descending", action = "store_true", help = "Show results in order of descending latency")

    parser.add_argument("-np", "--no-ping", action = "store_true", help = "Don't ping, just show the relays within the ones available based on the other arguments")
    parser.add_argument("-t", "--timeout", action = "store", help = "Maximum time to wait for each ping response", metavar = "timeout")
    parser.add_argument("-6", "--ipv6", action = "store_true", help = "Use IPv6 to ping servers (requires IPv6 connectivity on both ends)")

    parser.add_argument("-u", "--use", action = "store_true", help = "Change Mullvad relay options to use the lowest latency server tested")
    parser.add_argument("-r", "--random", action = "store_true", help = "Change Mullvad relay options to use a random server within the ones available based on the other arguments")

    args = parser.parse_args()

    formatPingError = lambda arg: f"Use a format that contains latency to use the {arg} option"
    flagPingError = lambda arg: f"The '-np/--no-ping' option can't be used with the {arg} option"


    ######################
    # Arguments handling #
    ######################


    if args.format:
        attributes = getAttributes(args.format)
    else:
        attributes = attributesLong if args.verbose else attributesShort

    pingRequested = RTT in attributes

    if not pingRequested:
        if args.use: failure(formatPingError("'-u'/'--use'"))
        if args.descending: failure(formatPingError("'-d'/'--descending'"))

    if args.no_ping:
        if args.use: failure(flagPingError("'-u'/'--use'"))
        if args.descending: failure(flagPingError("'-d'/'--descending'"))

        while RTT in attributes: attributes.remove(RTT)

        pingRequested = False

    if args.country != None: getFilter(args.country, eqAttr(COUNTRY_CODE), filterOr, relayConditions)
    if args.country_not != None: getFilter(args.country_not, neqAttr(COUNTRY_CODE), filterAnd, relayConditions)

    if args.city != None:
        cities = list(zip(args.city[::2], args.city[1::2]))

        # Returns a function that tests if relay 'r' is in the city defined by the (country_code, city_code) tuple 'cityTuple'
        inCity = lambda cityTuple: (lambda r: eqAttr(COUNTRY_CODE)(cityTuple[0])(r) and eqAttr(CITY_CODE)(cityTuple[1])(r))

        getFilter(cities, inCity, filterOr, relayConditions)

    if args.city_not != None:
        notCities = list(zip(args.city_not[::2], args.city_not[1::2]))

        # Symmetrical to inCity
        notInCity = lambda cityTuple: (lambda r: not (eqAttr(COUNTRY_CODE)(cityTuple[0])(r) and eqAttr(CITY_CODE)(cityTuple[1])(r)))

        getFilter(notCities, notInCity, filterAnd, relayConditions)

    if args.hostname != None: getFilter(args.hostname, eqAttr(HOSTNAME), filterOr, relayConditions)
    if args.hostname_not != None: getFilter(args.hostname_not, neqAttr(HOSTNAME), filterAnd, relayConditions)

    if args.provider != None: getFilter(args.provider, eqAttr(PROVIDER), filterOr, relayConditions)
    if args.provider_not != None: getFilter(args.provider_not, neqAttr(PROVIDER), filterAnd, relayConditions)

    if args.bandwidth:
        try:
            relayConditions.append(geqAttr(BANDWIDTH)(float(args.bandwidth)))
        except:
            failure("Error: the bandwidth option must be a number")

    if args.wireguard: relayConditions.append(eqAttr(TYPE)(WIREGUARD))
    if args.openvpn: relayConditions.append(eqAttr(TYPE)(OPENVPN))
    if args.stboot: relayConditions.append(eqAttr(STBOOT)(True))
    if args.owned: relayConditions.append(eqAttr(OWNED)(True))
    if args.ipv6: relayConditions.append(lambda r: IPV6 in r)

    timeout = DEFAULT_TIMEOUT if args.timeout == None else (float(args.timeout) / 1000 if ON_UNIX else float(args.timeout))

    IP = IPV6 if args.ipv6 else IPV4

    # If the '-q'/'--quiet' or the '-d'/'--descending' option was enabled
    # don't print anything live
    boxLivePrint = noPrint if args.quiet or args.descending else printBox
    lineLivePrint = noPrint if args.quiet or args.descending else printLine


    #############
    # Main loop #
    #############


    relays = list(filter(filterAnd(relayConditions), getRelays()))

    if relays == []:
        failure("The conditions specified resulted in no relays")

    itemsSpaces = getSpacing(relays, attributes)

    boxLivePrint(getSpacingList(attributes, itemsSpaces), "┌", "┐", "┬", "─")
    for index, r in enumerate(relays):
        host = r[HOSTNAME]
        address = r[IP]

        if pingRequested:
            _, rtt, _ = ping(address, 1, timeout = timeout, ipv6 = args.ipv6)
            relays[index][RTT] = rtt

        lineLivePrint(r, attributes, itemsSpaces, "│")
    boxLivePrint(getSpacingList(attributes, itemsSpaces), "└", "┘", "┴", "─")
    if not args.quiet and not args.descending: print()


    ####################
    # Final operations #
    ####################


    nonReachableRelays = list(filter(eqAttr(RTT)(None), relays))
    reachableRelays = list(filter(neqAttr(RTT)(None), relays))

    if args.descending:
        # If the '-d'/'--descending' option was enabled, print
        # the results here after having sorted them based on latency
        # results
        descendingRelays = nonReachableRelays + list(sorted(reachableRelays, key = lambda r: r[RTT], reverse = True))

        if descendingRelays != []:
            printBox(getSpacingList(attributes, itemsSpaces), "┌", "┐", "┬", "─")
            for r in descendingRelays:
                printLine(r, attributes, itemsSpaces, "│")
            printBox(getSpacingList(attributes, itemsSpaces), "└", "┘", "┴", "─")
            print()

    if reachableRelays == [] and pingRequested:
        failure("No relay could be reached")

    if pingRequested:
        lowestLatency = min(reachableRelays, key = lambda r: r[RTT])
        maxLatency = max(reachableRelays, key = lambda r: r[RTT])

        print(f"Highest latency host: {maxLatency[HOSTNAME]} ({maxLatency[RTT]}ms)")
        print(f"Lowest latency host: {lowestLatency[HOSTNAME]} ({lowestLatency[RTT]}ms)")

    if args.use:
        print("\nSelecting lowest latency server")
        mullvadChangeRelay(lowestLatency[HOSTNAME])
        sys.exit(0)
    if args.random:
        print("\nSelecting random server")

        # Choose relay pool based on whether latency testing was performed or not
        # This allows to not try to connect to a server that could not be reached
        # in case it was performed
        #
        # If it was not, choose the whole list of filtered relays as the pool
        randomRelayPool = relays if not pingRequested else reachableRelays
        mullvadChangeRelay(randomRelayPool[randint(0, len(randomRelayPool) - 1)][HOSTNAME])
        sys.exit(0)
