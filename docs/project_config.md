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

# Common item configs

- name - required
- uid - required
- parents
- parents_validation: ["minimum-one", "minimum-one-each-type"]
- relation:
  - values: m-to-n or 1-to-n or n-to-1

# Links

- name - required
- uid - required
- from-uids - list of uid's from where items the link is created
- to-uids - list of uid's to which items the link is created
- from-name - shows the arrow and the name of the direction from->to.
- to-name - shows the arrow and the name of the direction to->from
- require-full-traceability: true - means every Item from either side must have at least one link to other elements.

## additional LINKS information [ TO BE IMPROVED]

Because the percentage is a sloppy way of defining completeness due to the fact that most of TC's linked to a req overlap
in coverage. For ex: so if one Req has two TC's and both TC's cover 70% of the req you still don't know if the req is
covered, because you do not know how TC's overlap, it can be 100% overlap and then the req has 70% coverage, or it can
20% overlap then the req is 100% covered, so the percentage alone is a bad indicator or coverage of a requirement.

- require-link-completeness-percentage: true - add object in the link like

A better solution will be to mark what text parts of a req that is covered by a TC.
