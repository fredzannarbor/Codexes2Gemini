#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com

from classes.Codexes.Tools.DocxCodex2Objects import DocxCodex2Objects
from classes.Codexes.Tools.Docxdfs2Tools import Docxdfs2Tools as dcdt

dcdx = DocxCodex2Objects()

# docxfiles = ['test/docx/lorem.docx', 'test/docx/szy2.docx', 'working/contracted/active_copyedit/WATF_revised.docx']
docxfiles = ['test/docx/szy2.docx']

output_dir = 'output'
test = dcdx.docx2dfs(docxfiles, output_dir, 'text', 20)

presets = ['Proofread', 'ELI5']
dcdt = dcdt(test[0][0], test[0][1], test[0][2])
# print(dcdt.combined_df.head(5))
completions = dcdt.docxdfs2presets([dcdt.combined_df], presets, rows=3, beginning_row=0, ending_row=10)
print('made it to completions')
# print(completions)
completions[0].to_csv('output/completions.csv')
