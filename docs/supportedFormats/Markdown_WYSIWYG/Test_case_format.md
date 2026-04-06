# Markdown

One requirement one file with following name format {text}.ac.md
chapters like metadata are allowed and they associate YML or JSON data to the parent item.

# metadata

```yml
id: TC-3
tags: [be]
parent: [TS-1]
links-to:
  tc-to-reqs: [UR-4, PR-1, SWR-1]
```

# Title of the TC

description of the TC

# Preconditions

## Precondition1 title

Precondition1 description

## Precondition2 title

Precondition1 description

# Steps

## Step1 title

### metadata

```yml
duration: 10m
```

action description executed for this step

### Expected results

descriptionfor expected results

## Step2 title

### metadata

```yml
duration: 1h
```

step2.action description executed for this step

### Expected results

step2.expected_results description for expected results
