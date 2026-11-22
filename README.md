# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/helmut-hoffer-von-ankershoffen/heinzel-acme/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                                             |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|--------------------------------------------------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| plugins/heinzel-acme-connectors/src/heinzel\_acme\_connectors/\_\_init\_\_.py    |       38 |        1 |        4 |        1 |     95% |        64 |
| plugins/heinzel-acme-connectors/src/heinzel\_acme\_connectors/\_ai\_models.py    |       30 |        3 |        6 |        0 |     86% |     83-85 |
| plugins/heinzel-acme-connectors/src/heinzel\_acme\_connectors/\_chat\_command.py |      110 |        1 |       32 |        2 |     98% |156, 179-\>178 |
| plugins/heinzel-acme-connectors/src/heinzel\_acme\_connectors/\_dummy.py         |      203 |        2 |       30 |        3 |     98% |439, 560, 595-\>597 |
| plugins/heinzel-acme-connectors/src/heinzel\_acme\_connectors/\_sign\_in.py      |       58 |        2 |       12 |        0 |     97% |   144-145 |
| plugins/heinzel-acme-connectors/src/heinzel\_acme\_connectors/\_standins.py      |      153 |       17 |       32 |        3 |     88% |57, 100-101, 103-104, 110, 151-152, 199-207 |
| plugins/heinzel-acme-connectors/src/heinzel\_acme\_connectors/acme\_chat.py      |       48 |        1 |       16 |        1 |     97% |        42 |
| src/heinzel\_acme/\_service.py                                                   |       51 |        4 |       12 |        2 |     90% |28, 31-32, 104 |
| src/heinzel\_acme/seed/\_render.py                                               |       23 |       17 |        8 |        0 |     19% |     14-30 |
| src/heinzel\_acme/seed/\_runner.py                                               |       38 |        3 |        4 |        0 |     93% |     84-86 |
| src/heinzel\_acme/seed/\_service.py                                              |       78 |        0 |       24 |        2 |     98% |110-\>112, 112-\>114 |
| **TOTAL**                                                                        | **1698** |   **51** |  **298** |   **14** | **96%** |           |

26 files skipped due to complete coverage.


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/helmut-hoffer-von-ankershoffen/heinzel-acme/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/helmut-hoffer-von-ankershoffen/heinzel-acme/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/helmut-hoffer-von-ankershoffen/heinzel-acme/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/helmut-hoffer-von-ankershoffen/heinzel-acme/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fhelmut-hoffer-von-ankershoffen%2Fheinzel-acme%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/helmut-hoffer-von-ankershoffen/heinzel-acme/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.