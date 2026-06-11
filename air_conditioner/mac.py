import network

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

mac = wlan.config('mac')

print(':'.join('{:02X}'.format(b) for b in mac))