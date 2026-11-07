from dotenv import load_dotenv
load_dotenv()
from tinyfish import TinyFish

c = TinyFish()
print(c.monitors.list())
