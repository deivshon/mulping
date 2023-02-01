import unittest

from mulping import parsePing

linuxPingOutput1 ="""PING 89.45.224.119 (89.45.224.119): 56 data bytes

--- 89.45.224.119 ping statistics --- 1 packets transmitted, 1 packets received, 0.0% packet loss round-trip min/avg/max/stddev = 156.910/156.910/156.910/0.000 ms
"""
expectedLinux1 = (156.910, 156.910, 156.910)

linuxPingOutput2 = """PING 89.45.224.119 (89.45.224.119) 56(84) bytes of data.

--- 89.45.224.119 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 104.553/104.553/104.553/0.000 ms
"""
expectedLinux2 = (104.553, 104.553, 104.553)

linuxPingOutput3 = """PING 89.45.224.119 (89.45.224.119) 56(84) bytes of data.

--- 89.45.224.119 ping statistics ---
8 packets transmitted, 8 received, 0% packet loss, time 7009ms
rtt min/avg/max/mdev = 100.131/111.721/163.633/20.372 ms
"""
expectedLinux3 = (100.131, 111.721, 163.633)

class PingParseTest(unittest.TestCase):
    def testLinux(self):
        self.assertEqual(parsePing(linuxPingOutput1), expectedLinux1)
        self.assertEqual(parsePing(linuxPingOutput2), expectedLinux2)
        self.assertEqual(parsePing(linuxPingOutput3), expectedLinux3)
