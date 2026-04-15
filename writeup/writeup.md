### Project Name

GenoBench-learning


### Your Team

Eugenio Rivera Ramos


### Problem Statement

Do frontier models learn, or just recall? Jagged intellegiance of coding is a frequent complain but its often difficult to articulate. models excel at some tasks and fail at structurally similar ones esspecially on genuinely new. Can we measure that gap in practicaly.

Agentic harness systems are essentially multi-step pipelines, where failure mode aren't typically lack of knowledge but the inability effectively use its context and manipulate it to discover proper solutions. In other wrods a model must do two things: externalize its understanding into a context (notes, observations, intermediate reasoning), and then effectively use that context to solve a downstream problem. These are separable skills, and current benchmarks don't measure either.



### Task & benchmark construction
GenoBench-Learning isolates both parts of the <insert>. The benchmark decomposes learning into two scored sub-problems: how well can a model construct a useful learned context from novel stimuli, and how well can it apply that context to solve a new instance? Performance on each is measured independently and baselined against a one-shot approach.

GenoBench-Learning measures in-context learning using a pre/post study paradigm on stimuli designed to fall outside training data.

Each task presents the model with novel stimuli. The model is scored before and after a structured self-study phase in which it must articulate the underlying rule in its own words. Learning gain — the delta between pre- and post-study accuracy — is the primary signal.


### Dataset


### Technical details


### Results, insights, and conclusions
The benchmark reveals what standard evaluations cannot: not just whether a model knows things, but whether it can learn new things on demand, and whether explicit self-generated reasoning aids that learning.



### Organizational affiliations

Blue Origin; University of Washington. All work was completed using personal resources only, with no institutional support or resources.


### References & citations
