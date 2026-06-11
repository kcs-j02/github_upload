import network
from time import sleep

SSID = "----"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

print("scan:")
print(wlan.scan())

print("connect start")
wlan.connect(SSID)

for i in range(30):
    print("connecting", i, wlan.status())
    if wlan.isconnected():
        print("WiFi OK")
        print(wlan.ifconfig())
        break
    sleep(1)

if not wlan.isconnected():
    print("WiFi failed")
    print("status:", wlan.status())