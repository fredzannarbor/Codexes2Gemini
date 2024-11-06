function Header(el)
    -- Reduce baselineskip after headings (adjust the factor as needed)
    if el.text then
        el.text = el.text .. '\\vspace{-0.5\\baselineskip}'
    end
    return el
end