import langid
import lxml.etree
import lxml.html
from itertools import islice
from collections import deque
import re

input_file = "export.xml"
output_file = "export.out.xml"
def sliding_window(iterable, n):
    "Collect data into overlapping fixed-length chunks or blocks."
    # sliding_window('ABCDEFG', 3) → ABC BCD CDE DEF EFG
    iterator = iter(iterable)
    window = deque(islice(iterator, n - 1), maxlen=n)
    for x in iterator:
        window.append(x)
        yield tuple(window)

tree = lxml.etree.parse(input_file)



#print(tree)
ns = {'root': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'}
textlines = tree.xpath("//root:TextLine", namespaces = ns)
#text = tree.xpath("//root:Unicode/text()", namespaces = ns)
#for sentence in text:
#    result = langid.classify(sentence)
#    print(result[0])
#print(text)

numbers = r"[0-9]+"
roman_numerals = r"[IVXLCDM]+" # we do not care if number is valid, just that it looks like a roman number


window_size = 5
stride_count = 3
#iterable = text.split()
#tree = lxml.html.parse("wiki.html").getroot()
#text = "".join(tree.itertext()).split()

def serialize_detected_span(span, base_offset = 0):
    offset = base_offset + span[0]
    length = span[1] - span[0]
    return f" unclear {{offset:{offset};length:{length}}}"

for text_element in textlines:
    sentence = text_element.xpath(".//root:Unicode/text()", namespaces = ns)[0]
    output_str = ""
    number_substr = re.finditer(fr"\W{numbers}\W", sentence)
    roman_substr = re.finditer(rf"\W{roman_numerals}\W", sentence)
    for match in number_substr:
        output_str += serialize_detected_span(match.span())

    for match in roman_substr:
        output_str += serialize_detected_span(match.span())
    #print(output_str)
    
    
    for i, window in enumerate(list(sliding_window(sentence.split(), window_size))[::stride_count]):
        window_start = stride_count*i
        sentence_part = " ".join(window)
        
        has_number = re.search(fr"\W{numbers}\W", sentence)
        has_roman = re.search(rf"\W{roman_numerals}\W", sentence)
        
        if has_number or has_roman:
            #print(sentence_part)
            continue
        result = langid.classify(sentence_part)
        if result[0] != 'de':
            output_str += serialize_detected_span((window_start, window_start + len(sentence_part)))
            print(window, langid.classify(sentence_part))


    custom_str = text_element.get("custom")
    text_element.set("custom", custom_str + output_str)
    #print(output_str)

tree.write(output_file)