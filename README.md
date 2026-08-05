## Proof of Concept

This repository is a proof of concept to detect 
sparse instances of a particular language within
a largely monolingual text. 

## Steps to Run
```
git clone "<REPO_URL>" 
python -m venv .venv && source .venv/bin/activate # Optional
pip install .
python use_lang.py
```

## Purpose

One of the projects that we are working on, is 
OCR transcription of Handwritten German Shorthand text into Latin
german script, such that historical texts that were
written in German shorthand become accessible.

One of the issues with this task is that many shorthand writers don't exclusively write in German
Shorthand, but will often use English for proper nouns, and other loan words. 

This leads to the task being multilingual character recognition. Therefore one way to improve performance of our OCR model would be to annotate the places where
Latin Script (for english) or Arabic Script (for numerals) is being used (this is a hypothesis). 
