To use stanford parser download the following files from our CS540 github:

stanford_parser.py
englishPCFG.ser.gz

then mkdir named stanford-parser-full-2018-10-17
cd to stanford-parser-full-2018-10-17

and download the jar files from my google drive:

https://drive.google.com/open?id=1gkBFbAHUZ9aGu1VdBCRwHvPdq54BPLVD
https://drive.google.com/open?id=1amk91rboJzt7vZu4JmVCoBYe4jqC0VvO

then cd ..
and edit stanford_parser.py by putting your current directory path into string dir_path on line 4

example:
dir_path = '/s/chopin/d/sarmst'

you should be able to run stanford_parser.py by
python3 stanford_parser.py

and if you want to input sentences:
python3 stanford_parser.py "This is an example sentence."
python3 stanford_parser.py "This is an example sentence." "This is another example sentence."