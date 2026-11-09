import langid
import lxml.etree
import lxml.html
from itertools import islice
from collections import deque
import re
import bisect
from dataclasses import dataclass

ns = {'root': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'}

@dataclass
class UnclearSpan:
    source:str
    offset: int
    length: int

    @staticmethod
    def unserialize(unclear_str):
        # remove whitespace
        unclear_str = "".join(c for c in unclear_str if not c.isspace())
        REGEX = re.compile(r"{offset:(\d+);length:(\d+);}")
        match_result = re.match(REGEX, unclear_str)
        if not match_result:
            return None
        offset, length = int(match_result.group(1)), int(match_result.group(2))
        return offset, length

    def merge(self, other):
        # check for overlap
        
        # self.start in other.interval
        if other.start <= self.start <= other.end:
            return UnclearSpan(self.source, other.start, max(self.end, other.end) - other.start)

        # self.end in other.interval
        if other.start <= self.end <= other.end:
            return UnclearSpan(self.source, min(self.start, other.start), other.end - min(self.start, other.start))

        # self surrounds other
        if self.start <= other.start <= other.end <= self.end:
            return self
        return None
    @property
    def start(self):
        return self.offset
    
    @property
    def end(self):
        return self.offset + self.length
    
    def serialize(self):
        return f"unclear {{offset:{self.offset};length:{self.length}}}"

    def __str__(self):
        return self.source[self.offset: self.offset + self.length]

@dataclass
class UnclearSpanCollection:
    source: str
    offsets: list[UnclearSpan]


    @classmethod
    def from_element(cls, element):
        text = element.xpath(".//root:Unicode/text()", namespaces = ns)
        if isinstance(text, list):
            text = text[0]

        spans = []
        custom_str  = element.get("custom")

        tokens = iter(custom_str.split())
        for token in tokens:
            if token == "unclear":
                token_data = next(tokens)
                #print(token_data)
                result = UnclearSpan.unserialize(token_data)
                if result is None:
                    continue
                offset, length = result
                spans.append(UnclearSpan(text, offset, length))

        #spans.sort(key = lambda x: x.offset)
        return cls(text, spans)

    def add(self, span: UnclearSpan):
        self.offsets.append(span)
        self.offsets.sort(key=lambda x: x.offset)
        i = 1
        offsets = self.offsets
        while i < len(self.offsets):
            base = offsets[i - 1]
            cur = offsets[i]
            if (result:= base.merge(cur)) is not None:
                offsets[i-1] = result
                del offsets[i]
                continue
            else:
                i += 1

    def serialize(self):
        return " ".join(x.serialize() for x in self.offsets)
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


def update_element(element, span_collection):
    props = element.get("custom")
    start_index = props.find("unclear")
    if start_index == -1:
        props += span_collection.serialize()
    else:
        props = props[:start_index] + span_collection.serialize()

    text_element.set("custom", props)
    

#print(tree)

textlines = tree.xpath("//root:TextLine", namespaces = ns)
#for element in textlines:
#    offsets = UnclearSpanCollection.from_element(element).offsets
#    for offset in offsets:
#        print(offset.serialize(), offset)

#text = tree.xpath("//root:Unicode/text()", namespaces = ns)
#for sentence in text:
#    result = langid.classify(sentence)
#    print(result[0])
#print(text)

numbers = r"[0-9]+"
roman_numerals = r"[IVXLCDM]+" # we do not care if number is valid, just that it looks like a roman number


window_size = 5
stride_count = 3

# hallo mein name ist ojas. ich arbeite am bibliotek
#iterable = text.split()
#tree = lxml.html.parse("wiki.html").getroot()
#text = "".join(tree.itertext()).split()

def serialize_detected_span(span, base_offset = 0):
    offset = base_offset + span[0]
    length = span[1] - span[0]
    return f" unclear {{offset:{offset};length:{length}}}"

for text_element in textlines:
    collection = UnclearSpanCollection.from_element(text_element)
    sentence = text_element.xpath(".//root:Unicode/text()", namespaces = ns)[0]
    print("\n" + sentence)
    output_str = ""
    number_substr = re.finditer(fr"\W{numbers}\W", sentence)
    roman_substr = re.finditer(rf"\W{roman_numerals}\W", sentence)
    for match in number_substr:
        start, end = match.span()
        collection.add(UnclearSpan(sentence, start, end - start + 1))
        #output_str += serialize_detected_span(match.span())

    for match in roman_substr:
        start, end = match.span()
        collection.add(UnclearSpan(sentence, start, end - start + 1))
        #output_str += serialize_detected_span(match.span())
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
            collection.add(UnclearSpan(sentence, window_start, len(sentence_part)))
            output_str += serialize_detected_span((window_start, window_start + len(sentence_part)))
            #print(window, langid.classify(sentence_part))

    for offset in collection.offsets:
        print(offset.serialize(), offset)
    update_element(text_element, collection)
    #custom_str = text_element.get("custom")
    #text_element.set("custom", custom_str + output_str)
    #print(output_str)

tree.write(output_file)