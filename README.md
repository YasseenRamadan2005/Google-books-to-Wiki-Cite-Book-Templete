# Google-books-to-Wiki-Cite-Book-Templete
This is a simple python script to convert links on google books into Wikipedia's cite book templete. https://en.wikipedia.org/wiki/Template:Cite_book

Usage: python citebook.py <url_or_doi> [--debug]

Simply paste the link in as a command line argument. This is not guaranteed to be 100% accurate, simply to create a simple baseline to avoid the manual work. Known problems are:

1. Books that are republished. For example, if you pass in https://www.google.com/books/edition/A_Nation_of_Immigrants/HYBbDwAAQBAJ , it sets the year to be 2018, not the original data of publishing.

2. Books where each chapter has an author, and there's one editor who ties it all together. For example, if you pass in https://www.google.com/books/edition/Contemporary_Egypt/zu5ynOwsrsAC , it puts Charles Tripp as the sole author. In reality, Tripp was the editor - each chapter was an essay written by a different author (Tripp wrote chapter 3). You'll need to manually set Tripp as the editor and pass in all the authors if you want (use the display-authors parameter to list how many how want).

3. It can only cite the book as a whole, not a specific chapter or range of pages.

4. For books that are translations, the Cite Book templete has the parameters nessary to indicate the original and tranlsated title as well as the authors and translators. You'll need to do that manually.


Try not to spam, or else Google Books might send back a 503. 

