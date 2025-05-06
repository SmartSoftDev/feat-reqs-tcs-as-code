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
- relation:
  - values: m-to-n or 1-to-n or n-to-1

# links

- name - required
- uid - required
- from-uids - list of uid's from where items the link is created
- to-uids - list of uid's to which items the link is created
- from-name - shows the arrow and the name of the direction from->to.
- to-name - shows the arrow and the name of the direction to->from
- require-link-completeness-percentage: true
