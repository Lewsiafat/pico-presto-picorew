import os, machine
try:
    os.remove('wifi_config.json')
    print("Config deleted.")
except:
    print("Config not found.")
# 選擇性：也可以順便重置機器
machine.reset()
