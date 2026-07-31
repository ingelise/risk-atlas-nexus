---
search:
  boost: 5.0
---

# Slot: producer

_A relationship to the Organization instance which produces this instance._

<div data-search-exclude markdown="1">

URI: [nexus:producer](https://w3id.org/ai-atlas-nexus/producer)
Alias: producer

<!-- no inheritance hierarchy -->

## Applicable Classes

| Name                                        | Description                                                                      | Modifies Slot |
| ------------------------------------------- | -------------------------------------------------------------------------------- | ------------- |
| [BaseAi](BaseAi.md)                         | Any type of AI, be it a LLM, RL agent, SVM, etc                                  | no            |
| [AiSystem](AiSystem.md)                     | A compound AI System composed of one or more AI capablities                      | no            |
| [AiAgent](AiAgent.md)                       | An artificial intelligence (AI) agent refers to a system or program that is c... | no            |
| [Adapter](Adapter.md)                       | Adapter-based methods add extra trainable parameters after the attention and ... | no            |
| [AiModel](AiModel.md)                       | A base AI Model class                                                            | no            |
| [LargeLanguageModel](LargeLanguageModel.md) | A large language model (LLM) is an AI model which supports a range of languag... | no            |

## Properties

### Type and Range

| Property  | Value                           |
| --------- | ------------------------------- |
| Range     | [Organization](Organization.md) |
| Domain Of | [BaseAi](BaseAi.md)             |

### Cardinality and Requirements

| Property | Value |
| -------- | ----- |

## Identifier and Mapping Information

### Schema Source

- from schema: https://w3id.org/ai-atlas-nexus/ai-risk-ontology

## Mappings

| Mapping Type | Mapped Value   |
| ------------ | -------------- |
| self         | nexus:producer |
| native       | nexus:producer |

## LinkML Source

<details>
```yaml
name: producer
description: A relationship to the Organization instance which produces this instance.
from_schema: https://w3id.org/ai-atlas-nexus/ai-risk-ontology
rank: 1000
alias: producer
domain_of:
- BaseAi
range: Organization

```
</details></div>
```
