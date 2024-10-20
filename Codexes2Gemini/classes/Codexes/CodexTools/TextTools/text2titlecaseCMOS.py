#!/usr/bin/env python3
import spacy

nlp = spacy.load('en_core_web_sm')

TO_CAPITALIZE = {
    # nouns
    'NN',  # common noun, singular or mass
    'NNS',  # common noun, plural
    'NNP',  # proper noun, singular
    'NNPS',  # proper noun, plural
    # pronouns
    'PRP',  # pronoun, personal
    'PRP$',  # pronoun, possessive
    'WP',  # wh-pronoun, personal
    'WP$',  # wh-pronoun, possessive
    # adjectives
    'JJ',  # adjective
    'JJR',  # adjective, comparative
    'JJS',  # adjective, superlative
    # verbs
    'MD',  # verb, modal
    'VB',  # verb, base form
    'VBD',  # verb, past tense
    'VBG',  # verb, gerund or present participle
    'VBN',  # verb, past participle
    'VBP',  # verb, present tense, other than third person singular
    'VBZ',  # verb, present tense, third person singular
    # adverbs
    'RB',  # adverb
    'RBR',  # adverb, comparative
    'RBS',  # adverb, superlative
    'RP',  # adverb, particle
    'WRB',  # wh-adverb
}


def capitalize_token(arg, idx):
    tok = arg[idx]
    return (
        # token is first or last
            (idx == 0 or idx == len(arg) - 1) or
            # token is a type that should always be capitalized
            (tok.tag_ in TO_CAPITALIZE) or
            # token is a subordinating conjunction
            # the IN tag represents a preposition (if followed by a noun or
            # prepositional phrase), or a subordinating conjunction (if
            # followed by a clause)
            # if this token is related to its syntactic parent as either
            # a MARK (for an adverbial clause modifier) or a COMPLM
            # (complementary clause), then we treat it as a subordinating
            # conjunction and capitalize it
            (tok.tag_ == 'IN' and tok.dep_ in {'mark', 'complm'}) or
            # token is the first in a hyphenated sequence
            (idx > 0 and idx < len(arg) - 1 and arg[idx + 1].tag_ == 'HYPH' and arg[idx - 1].tag_ != 'HYPH')
    )


def titlecase_tokens(arg):
    ret = []

    for idx, tok in enumerate(arg):
        ret.append(tok.orth_.capitalize() if capitalize_token(arg, idx) else tok.orth_)
        ret.append(tok.whitespace_)

    return ret


def text2words(text):
    words = text.split()
    return words


def words2titlecaseCMOS(words):
    title = []
    for word in words:
        output = titlecase_tokens(nlp(word.lower()))
        title.append(''.join(output))
    return title


def text2titlecaseCMOS(text):
    words = text2words(text)
    titlelist = words2titlecaseCMOS(words)
    titlestring = ' '.join(titlelist)
    return titlestring, titlelist
