# Project level configuration file

Each project has a configuration file located in root directory of the project (it might not be root of the repository).

Items types:

- group
- requirement
- test-case
- test-suite
- test-plan
- epic
- feature

## Path configuration

- root-dir - path to the project root. can be absolute path or relative to this file. default = "."

## Item file name convention

'0'PaddedNr-shortDescr.LowerUID.ac.md

## Common item configs

- name - required
- uid - required. Always CAPITAL letters.
- type - defaults to item. can be requirement, test-case, feature. Determines how the 0X-_._.ac.md file will be parsed.
- parents
- parents_validation: ["minimum-one", "minimum-one-each-type", "optional"]
- relation:
  - values: m-to-n or 1-to-n or n-to-1
- stored_externally: true - indicates the item type is managed in another tool.
- id_min_size: int - indicates how many '0' should be padded for item ID. defaults to 4

## Links

- name - required
- uid - required
- from-uids - list of uid's from where items the link is created
- to-uids - list of uid's to which items the link is created
- from-name - shows the arrow and the name of the direction from->to.
- to-name - shows the arrow and the name of the direction to->from
- require-full-traceability: true - means every Item from either side must have at least one link to other elements.
- require-coverage-at-to: require-coverage-at-from: true - will require HTML tagging
  `<link-uid-itemID> ... </link-uid-itemID>` for showing the coverage.

### additional LINKS information [ NOGO ]

Because the percentage is a sloppy way of defining completeness due to the fact that most of TC's linked to a req overlap
in coverage. For ex: so if one Req has two TC's and both TC's cover 70% of the req you still don't know if the req is
covered, because you do not know how TC's overlap, it can be 100% overlap and then the req has 70% coverage, or it can
20% overlap then the req is 100% covered, so the percentage alone is a bad indicator or coverage of a requirement.

- require-link-completeness-percentage: true - add object in the link like

A better solution will be to mark what text parts of a req that is covered by a TC.

## Configuring duration limitations

"duration" field can be configured as integer number of "s,m,h,d" (seconds, minutes, hours, days) in metadata of any element (TC, Req, etc). The meaning of duration field can be different depending of item type it applies to. Usually it is added for TC's to indicate how much time the TC is running.
But to be able to detect and inform users for bad values for duration the following configuraiton options to be added to the respective Item for duration:

- duration-wrn-min: 5m
- duration-wrn-max: 45m
- duration-err-min: 2m
- duration-err-max: 4h
