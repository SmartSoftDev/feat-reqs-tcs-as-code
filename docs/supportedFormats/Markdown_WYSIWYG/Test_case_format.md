# Title of the TC

description of the TC

## Description

also description fo the TC

## metadata

```yml
id: TC-3
tags: [be]
parent: [TS-1]
links-to:
  tc-to-reqs: [UR-4, PR-1, SWR-1]
duration: 10m # recommended way of estimating the TC duration
```

## link-description_tc-to-reqs_UR-4

This is a note/description for the link UR-4 link.

## Preconditions

Preconditions description. Do not have subchapters on preconditions.

## Steps

### Step1 title

action description executed for this step.

#### Expected results

Description for expected results.

### Step2 title

#### metadata TBD

```yml
duration: 1h
```

step2 action description executed for this step

#### Expected results

step2 expected_results description for expected results

## Markdown Format Explanation

One requirement one file with following name format {text}.tc.ac.md
chapters like metadata are allowed and they associate YML or JSON data to the parent item.

Below starts the format of a TC
