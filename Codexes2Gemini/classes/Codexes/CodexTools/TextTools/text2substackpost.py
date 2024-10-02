#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com

import argparser
from classes.M

from app.utilities.utilities import statcounter
from classes.Masthead.ManagingEditor.ManagingEditorUtilities import create_substack_content

if __name__ == "__main__":
    argparser = argparser.Parser
    args = argparser.parse_args()
    args.add_argument("--queries", "-Q", type=list,
                      default=['all:Dyson AND all:spheres', 'LK-99', 'all:mass AND all:extinction AND all:events'])
    args.add_argument("--spin", "-S", type=str, default="Inject some humor.")

    substack_result = create_substack_content(queries=args.queries)

statcounter(0, 0
