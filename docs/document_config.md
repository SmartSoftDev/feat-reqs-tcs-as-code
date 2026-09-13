# Generating documents

The FRTac tool will offer a versatile way of generating multiple documents from the project items.

document configuration:

- name: file name and uid of the document.
- composite:
  - git-info: will add a chapter with git information
  - diagram: will add a diagram
    - type: [hierarchy]
    - items: [UR, PR, SWR, HWR]
  - list-of-items:
    - items: [BR, PR, SWR, HWR]
