

# Slot: id


_A unique identifier to this instance of the model element. Example identifiers include UUID, URI, URN, etc._





URI: [schema:identifier](http://schema.org/identifier)
Alias: id

<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Adapter](Adapter.md) | Adapter-based methods add extra trainable parameters after the attention and ... |  no  |
| [IncidentMitigatedclass](IncidentMitigatedclass.md) |  |  no  |
| [Consequence](Consequence.md) |  |  no  |
| [AiModelValidation](AiModelValidation.md) | AI model validation steps that have been performed after the model training t... |  no  |
| [RiskControl](RiskControl.md) | A measure that maintains and/or modifies risk (and risk concepts) |  no  |
| [Question](Question.md) | An evaluation where a question has to be answered |  no  |
| [LLMQuestionPolicy](LLMQuestionPolicy.md) | The policy guides how the language model should answer a diverse set of sensi... |  no  |
| [License](License.md) | The general notion of a license which defines terms and grants permissions to... |  no  |
| [StakeholderGroup](StakeholderGroup.md) | An AI system stakeholder grouping |  no  |
| [Severity](Severity.md) |  |  no  |
| [DataPreprocessing](DataPreprocessing.md) | Data transformations, such as PI filtering, performed to ensure high quality ... |  no  |
| [AiAgent](AiAgent.md) | An artificial intelligence (AI) agent refers to a system or program that is c... |  no  |
| [AiEvalResult](AiEvalResult.md) | The result of an evaluation for a specific AI model |  no  |
| [IncidentHaltedclass](IncidentHaltedclass.md) |  |  no  |
| [IncidentOngoingclass](IncidentOngoingclass.md) |  |  no  |
| [Questionnaire](Questionnaire.md) | A questionnaire groups questions |  no  |
| [AiLifecyclePhase](AiLifecyclePhase.md) | A Phase of AI lifecycle which indicates evolution of the system from concepti... |  no  |
| [RiskGroup](RiskGroup.md) | A group of AI system related risks that are part of a risk taxonomy |  no  |
| [AiEval](AiEval.md) | An AI Evaluation, e |  no  |
| [IncidentNearMissclass](IncidentNearMissclass.md) |  |  no  |
| [Modality](Modality.md) | A modality supported by an Ai component |  no  |
| [RiskTaxonomy](RiskTaxonomy.md) | A taxonomy of AI system related risks |  no  |
| [LLMIntrinsic](LLMIntrinsic.md) | A capability that can be invoked through a well-defined API that is reasonabl... |  no  |
| [AiSystem](AiSystem.md) | A compound AI System composed of one or more AI capablities |  no  |
| [AiProvider](AiProvider.md) | A provider under the AI Act is defined by Article 3(3) as a natural or legal ... |  no  |
| [Obligation](Obligation.md) | A rule describing an obligation for performing an activity |  no  |
| [AiModel](AiModel.md) | A base AI Model class |  no  |
| [Stakeholder](Stakeholder.md) | An AI system stakeholder for Responsible AI governance (e |  no  |
| [Rule](Rule.md) | A rule describing a process or control that directs or determines if and how ... |  no  |
| [Entity](Entity.md) | A generic grouping for any identifiable entity |  no  |
| [Risk](Risk.md) | The state of uncertainty associated with an AI system, that has the potential... |  no  |
| [Impact](Impact.md) |  |  no  |
| [Term](Term.md) | A term and its definitions |  no  |
| [AiOffice](AiOffice.md) | The EU AI Office (https://digital-strategy |  no  |
| [BaseAi](BaseAi.md) | Any type of AI, be it a LLM, RL agent, SVM, etc |  no  |
| [Dataset](Dataset.md) | A body of structured information describing some topic(s) of interest |  no  |
| [Documentation](Documentation.md) | Documented information about a concept or other topic(s) of interest |  no  |
| [Organization](Organization.md) | Any organizational entity such as a corporation, educational institution, con... |  no  |
| [Permission](Permission.md) | A rule describing a permission to perform an activity |  no  |
| [IncidentStatus](IncidentStatus.md) |  |  no  |
| [AiTask](AiTask.md) | A task, such as summarization and classification, performed by an AI |  no  |
| [LargeLanguageModelFamily](LargeLanguageModelFamily.md) | A large language model family is a set of models that are provided by the sam... |  no  |
| [Likelihood](Likelihood.md) |  |  no  |
| [Prohibition](Prohibition.md) | A rule describing a prohibition to perform an activity |  no  |
| [RiskConcept](RiskConcept.md) | An umbrella term for refering to risk, risk source, consequence and impact |  no  |
| [Vocabulary](Vocabulary.md) | A collection of terms, with their definitions and relationships |  no  |
| [Input](Input.md) | Input for which the system or component generates output |  no  |
| [Policy](Policy.md) | A guidance document outlining any of: procedures, plans, principles, decision... |  no  |
| [RiskIncident](RiskIncident.md) | An event occuring or occured which is a realised or materialised risk |  no  |
| [BenchmarkMetadataCard](BenchmarkMetadataCard.md) | Benchmark metadata cards offer a standardized way to document LLM benchmarks ... |  no  |
| [Action](Action.md) | Action to remediate a risk |  no  |
| [LargeLanguageModel](LargeLanguageModel.md) | A large language model (LLM) is an AI model which supports a range of languag... |  no  |
| [IncidentConcludedclass](IncidentConcludedclass.md) |  |  no  |







## Properties

* Range: [String](String.md)

* Required: True





## Identifier and Mapping Information







### Schema Source


* from schema: https://ibm.github.io/risk-atlas-nexus/ontology/ai-risk-ontology




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | schema:identifier |
| native | nexus:id |




## LinkML Source

<details>
```yaml
name: id
description: A unique identifier to this instance of the model element. Example identifiers
  include UUID, URI, URN, etc.
from_schema: https://ibm.github.io/risk-atlas-nexus/ontology/ai-risk-ontology
rank: 1000
slot_uri: schema:identifier
identifier: true
alias: id
domain_of:
- Entity
range: string
required: true

```
</details>
