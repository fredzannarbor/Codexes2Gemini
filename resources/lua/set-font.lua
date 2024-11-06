function Preprocess(doc)
    if FORMAT:match("latex") then
        pandoc.RawBlock('latex', '\\usepackage{fontspec}\n\\setmainfont{Miller Text}[SizeFeatures={Size=9}]')
        -- Assuming your body text uses the \normalsize command:
        pandoc.RawBlock('latex', '\\renewcommand{\\normalsize}{\\fontsize{9pt}{11pt}\\selectfont}')
    end
    return doc
end