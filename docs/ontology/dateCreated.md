

# Slot: dateCreated


_The date on which the entity was created._





URI: [schema:dateCreated](http://schema.org/dateCreated)
Alias: dateCreated

<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [AiModelValidation](AiModelValidation.md) | AI model validation steps that have been performed after the model training t... |  no  |
| [AiAgent](AiAgent.md) | An artificial intelligence (AI) agent refers to a system or program that is c... |  no  |
| [IncidentStatus](IncidentStatus.md) |  |  no  |
| [RiskTaxonomy](RiskTaxonomy.md) | A taxonomy of AI system related risks |  no  |
| [Permission](Permission.md) | A rule describing a permission to perform an activity |  no  |
| [Risk](Risk.md) | The state of uncertainty associated with an AI system, that has the potential... |  no  |
| [Impact](Impact.md) |  |  no  |
| [Consequence](Consequence.md) |  |  no  |
| [AiTask](AiTask.md) | A task, such as summarization and classification, performed by an AI |  no  |
| [AiEval](AiEval.md) | An AI Evaluation, e |  no  |
| [Dataset](Dataset.md) | A body of structured information describing some topic(s) of interest |  no  |
| [RiskControl](RiskControl.md) | A measure that maintains and/or modifies risk (and risk concepts) |  no  |
| [LargeLanguageModel](LargeLanguageModel.md) | A large language model (LLM) is an AI model which supports a range of languag... |  no  |
| [StakeholderGroup](StakeholderGroup.md) | An AI system stakeholder grouping |  no  |
| [IncidentConcludedclass](IncidentConcludedclass.md) |  |  no  |
| [IncidentMitigatedclass](IncidentMitigatedclass.md) |  |  no  |
| [Likelihood](Likelihood.md) |  |  no  |
| [BenchmarkMetadataCard](BenchmarkMetadataCard.md) | Benchmark metadata cards offer a standardized way to document LLM benchmarks ... |  no  |
| [Term](Term.md) | A term and its definitions |  no  |
| [Obligation](Obligation.md) | A rule describing an obligation for performing an activity |  no  |
| [AiSystem](AiSystem.md) | A compound AI System composed of one or more AI capablities |  no  |
| [IncidentHaltedclass](IncidentHaltedclass.md) |  |  no  |
| [Severity](Severity.md) |  |  no  |
| [IncidentOngoingclass](IncidentOngoingclass.md) |  |  no  |
| [IncidentNearMissclass](IncidentNearMissclass.md) |  |  no  |
| [RiskGroup](RiskGroup.md) | A group of AI system related risks that are part of a risk taxonomy |  no  |
| [LLMQuestionPolicy](LLMQuestionPolicy.md) | The policy guides how the language model should answer a diverse set of sensi... |  no  |
| [RiskConcept](RiskConcept.md) | An umbrella term for refering to risk, risk source, consequence and impact |  no  |
| [Organization](Organization.md) | Any organizational entity such as a corporation, educational institution, con... |  no  |
| [DataPreprocessing](DataPreprocessing.md) | Data transformations, such as PI filtering, performed to ensure high quality ... |  no  |
| [Input](Input.md) | Input for which the system or component generates output |  no  |
| [LargeLanguageModelFamily](LargeLanguageModelFamily.md) | A large language model family is a set of models that are provided by the sam... |  no  |
| [AiProvider](AiProvider.md) | A provider under the AI Act is defined by Article 3(3) as a natural or legal ... |  no  |
| [BaseAi](BaseAi.md) | Any type of AI, be it a LLM, RL agent, SVM, etc |  no  |
| [Action](Action.md) | Action to remediate a risk |  no  |
| [Stakeholder](Stakeholder.md) | An AI system stakeholder for Responsible AI governance (e |  no  |
| [Rule](Rule.md) | A rule describing a process or control that directs or determines if and how ... |  no  |
| [AiLifecyclePhase](AiLifecyclePhase.md) | A Phase of AI lifecycle which indicates evolution of the system from concepti... |  no  |
| [Entity](Entity.md) | A generic grouping for any identifiable entity |  no  |
| [Prohibition](Prohibition.md) | A rule describing a prohibition to perform an activity |  no  |
| [License](License.md) | The general notion of a license which defines terms and grants permissions to... |  no  |
| [Vocabulary](Vocabulary.md) | A collection of terms, with their definitions and relationships |  no  |
| [AiEvalResult](AiEvalResult.md) | The result of an evaluation for a specific AI model |  no  |
| [Questionnaire](Questionnaire.md) | A questionnaire groups questions |  no  |
| [Adapter](Adapter.md) | Adapter-based methods add extra trainable parameters after the attention and ... |  no  |
| [RiskIncident](RiskIncident.md) | An event occuring or occured which is a realised or materialised risk |  no  |
| [Policy](Policy.md) | A guidance document outlining any of: procedures, plans, principles, decision... |  no  |
| [AiOffice](AiOffice.md) | The EU AI Office (https://digital-strategy |  no  |
| [Modality](Modality.md) | A modality supported by an Ai component |  no  |
| [LLMIntrinsic](LLMIntrinsic.md) | A capability that can be invoked through a well-defined API that is reasonabl... |  no  |
| [AiModel](AiModel.md) | A base AI Model class |  no  |
| [Question](Question.md) | An evaluation where a question has to be answered |  no  |
| [Documentation](Documentation.md) | Documented information about a concept or other topic(s) of interest |  no  |







## Properties

* Range: [Date](Date.md)





## Identifier and Mapping Information







### Schema Source


* from schema: https://ibm.github.io/risk-atlas-nexus/ontology/ai-risk-ontology




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | schema:dateCreated |
| native | nexus:dateCreated |




## LinkML Source

<details>
```yaml
name: dateCreated
description: The date on which the entity was created.
from_schema: https://ibm.github.io/risk-atlas-nexus/ontology/ai-risk-ontology
rank: 1000
slot_uri: schema:dateCreated
alias: dateCreated
domain_of:
- Entity
range: date
required: false

```
</details>
