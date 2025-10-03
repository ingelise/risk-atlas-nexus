

# Slot: isDefinedByTaxonomy


_A relationship where a risk or a risk group is defined by a risk taxonomy_





URI: [schema:isPartOf](http://schema.org/isPartOf)
Alias: isDefinedByTaxonomy

<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [StakeholderGroup](StakeholderGroup.md) | An AI system stakeholder grouping |  no  |
| [Stakeholder](Stakeholder.md) | An AI system stakeholder for Responsible AI governance (e |  no  |
| [Action](Action.md) | Action to remediate a risk |  no  |
| [Risk](Risk.md) | The state of uncertainty associated with an AI system, that has the potential... |  no  |
| [RiskIncident](RiskIncident.md) | An event occuring or occured which is a realised or materialised risk |  no  |
| [RiskControl](RiskControl.md) | A measure that maintains and/or modifies risk (and risk concepts) |  no  |
| [RiskGroup](RiskGroup.md) | A group of AI system related risks that are part of a risk taxonomy |  no  |







## Properties

* Range: [RiskTaxonomy](RiskTaxonomy.md)





## Identifier and Mapping Information







### Schema Source


* from schema: https://ibm.github.io/risk-atlas-nexus/ontology/ai-risk-ontology




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | schema:isPartOf |
| native | nexus:isDefinedByTaxonomy |




## LinkML Source

<details>
```yaml
name: isDefinedByTaxonomy
description: A relationship where a risk or a risk group is defined by a risk taxonomy
from_schema: https://ibm.github.io/risk-atlas-nexus/ontology/ai-risk-ontology
rank: 1000
slot_uri: schema:isPartOf
alias: isDefinedByTaxonomy
domain_of:
- RiskGroup
- Risk
- RiskControl
- Action
- RiskIncident
- StakeholderGroup
- Stakeholder
range: RiskTaxonomy

```
</details>
