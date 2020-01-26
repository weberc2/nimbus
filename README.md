# NIMBUS

Nimbus is an experimental suite of Python 3 bindings for AWS CloudFormation
APIs (definitely not suitable for production). It is inspired by
[Troposphere](https://github.com/cloudtools/tropopshere); however, there are
several important distinctions.

* Nimbus APIs are generated from a formal specification provided by AWS, while
  Troposphere is currently hand-written.
* Nimbus APIs are typed, allowing type checkers to validate the APIs and client
  code that uses them.
* Nimbus aims to be friendly to text editors, making it easy for them to
  provide autocomplete and other features.