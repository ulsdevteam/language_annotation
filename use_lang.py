import langid
import lxml.etree
import lxml.html
from itertools import islice
from collections import deque
def sliding_window(iterable, n):
    "Collect data into overlapping fixed-length chunks or blocks."
    # sliding_window('ABCDEFG', 3) → ABC BCD CDE DEF EFG
    iterator = iter(iterable)
    window = deque(islice(iterator, n - 1), maxlen=n)
    for x in iterator:
        window.append(x)
        yield tuple(window)
text = "Hallo! Mein name ist Ojas. Heute habe ich der Buch. \"The Three Musketeers\" liest"

window_size = 5
skip_count = 3
#iterable = text.split()
tree = lxml.html.parse("wiki.html").getroot()
text = "".join(tree.itertext()).split()

for window in list(sliding_window(text, window_size))[::skip_count]:
    result = langid.classify(" ".join(window))
    if result[0] != 'de':
        print(window, langid.classify(" ".join(window)))