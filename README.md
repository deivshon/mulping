# mulping

Self contained utility wrapper script for pinging and filtering Mullvad VPN servers

## Requirements
+ Linux
+ Python 3.7+
+ [requests](https://requests.readthedocs.io) (if possible, one should install the relative distribution package, such as the [following](https://packages.debian.org/bullseye/python3-requests) in the case of Debian)

## Usage

By default, the script will ping all Mullvad servers and return live results. Using arguments the servers that are pinged can be filtered, and how they are pinged and the output format can be changed

## Arguments

### Filtering
| Argument | Long           | Content          | Effect                                                                                                                                                       | Example usage                     |
|----------|----------------|------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------|
| -c       | --country      | country ids      | Only servers in the countries specified will be selected                                                                                                     | `-c de ch at`                     |
| -cn      | --country-not  | country ids      | Exclude servers in the countries specified from being selected                                                                                               | `-cn no se fi`                    |
| -C       | --city         | city ids         | Only servers in the cities specified will be selected                                                                                                        | `-C de fra ch zrh`                |
| -Cn      | --city-not     | city ids         | Exclude servers in the cities specified from being selected                                                                                                  | `-Cn se sto fi hel`               |
| -H       | --hostname     | server hostnames | Only the specified servers will be selected                                                                                                                  | `-H de-fra-wg-101 ch-zrh-wg-401`  |
| -Hn      | --hostname-not | server hostnames | Exclude the specified servers from being selected                                                                                                            | `-Hn se-sto-wg-001 fi-hel-wg-101` |
| -p       | --provider     | providers' names | Only servers using the specified providers will be selected                                                                                                  | `-p 31137 DataPacket`             |
| -pn      | --provider-not | providers' names | Exclude servers using the specified providers from being selected                                                                                            | `-pn M247 Intergrid`              |
| -b       | --bandwidth    | Gbps amount      | Only server that have at least the provided bandwidth will be selected                                                                                       | `-b 10`                           |
| -w       | --wireguard    | /                | Only WireGuard servers will be selected                                                                                                                      | `-w`                              |
| -o       | --openvpn      | /                | Only OpenVPN servers will be selected                                                                                                                        | `-o`                              |
| -s       | --stboot       | /                | Only [stboot](https://mullvad.net/en/blog/2022/1/12/diskless-infrastructure-beta-system-transparency-stboot/) servers will be selected | `-s`                              |
| -O       | --owned        | /                | Only servers directly owned by Mullvad will be selected                                                                                                      | `-O`                              |

### Output
| Argument | Long         | Content              | Effect                                                                                                           | Example usage      |
|----------|--------------|----------------------|------------------------------------------------------------------------------------------------------------------|--------------------|
| -f       | --format     | property identifiers | Specify a custom format for the output table using server properties' ids<sup>1</sup>                            | `-f h l cf Cf p b` |
| -v       | --verbose    | /                    | Show more server properties in the output table                                                                  | `-v`               |
| -q       | --quiet      | /                    | Don't show the output table, only the final results (lowest and highest latency, if latency test was performed)  | `-q`               |
| -d       | --descending | /                    | Show the servers in the output table in descending order based on their latency (this will disable live results) | `-d`               |

<sup>1</sup> Property identifiers are defined as following:
| Id            | Property                 |
|---------------|--------------------------|
| h             | Hostname                 |
| 4             | IPv4 address             |
| 6             | IPv6 address             |
| c             | Country identifier       |
| C             | City identifier          |
| cf            | Country name             |
| Cf            | City name                |
| p             | Provider                 |
| l<sup>2</sup> | Latency                  |
| O             | Ownership                |
| b             | Bandwidth                |
| s             | Stboot status            |
| t             | Type (WireGuard/OpenVPN) |

<sup>2</sup> If in a custom format the latency property is omitted, no latency test will be performed

### Ping
| Argument | Long      | Content             | Effect                                                       | Example usage |
|----------|-----------|---------------------|--------------------------------------------------------------|---------------|
| -np      | --no-ping | /                   | Don't perform latency tests                                  | `-np`         |
| -6       | --ipv6    | /                   | Ping using IPv6                                              | `-6`          |
| -t       | --timeout | Milliseconds amount | Set custom timeout for latency tests (default is 10 seconds) | `-t 2500`     |

### Mullvad<sup>3</sup>
| Argument | Long     | Effect                                                                         | Example usage |
|----------|----------|--------------------------------------------------------------------------------|---------------|
| -u       | --use    | Set the lowest latency server tested as the selected Mullvad VPN relay         | `-u`          |
| -r       | --random | Set a random server within the ones selected as the selected Mullvad VPN relay | `-r`          |

<sup>3</sup> Requires the Mullvad VPN app installed
