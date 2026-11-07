from dotenv import load_dotenv
load_dotenv()

from tinyfish import TinyFish

c = TinyFish()
r = c.fetch.get_contents(["https://example.com"])
print(r.results[0] if r.results else r.errors)
