
import time
print("1234567890", end="\r")
time.sleep(1)
print("\033[2K01234", end="")