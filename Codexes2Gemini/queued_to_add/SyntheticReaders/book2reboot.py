#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com


'''converts a public domain book to a rebooted novel
1.  Loop over a directory or list of public domain books
2.  For each book, create summaries, vector, list, and graph indexes using llama-index.
3.  For each book, generate 5-10 ideas for how to reboot as a modern novel.
4.  Evaluate the ideas using ReaderPanels.
5.  Select the best idea for each novel.
6.  Using each idea, generate drafts of a rebooted novel.
7.  Evaluate the rebooted drafts using ReaderPanels.
8.  Select the best rebooted draft for each novel.
9.  Human collaborator edits the selected draft.
10.  Evaluate the edited draft using ReaderPanels.

'''
l