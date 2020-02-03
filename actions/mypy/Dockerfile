FROM python:3.7

ENV MYPYPATH=./core/src:./codegen/src:./util/src

RUN python -m pip install mypy

ENTRYPOINT entrypoint.sh