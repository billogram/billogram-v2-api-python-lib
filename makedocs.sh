#!/bin/bash

DOCS_DIR=docs

# Because of a bug we need to manually make sure to include all the submodules
echo "Did you remember to comment out the __all__ directive?"

pdoc --html billogram_api.py --html-dir $DOCS_DIR --overwrite --all-submodules
mv $DOCS_DIR/billogram_api.m.html $DOCS_DIR/index.html
ghp-import -m "generate documentation" $DOCS_DIR

