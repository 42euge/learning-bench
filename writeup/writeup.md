### Project Name

GenoBench-learning


### Your Team

Eugenio Rivera Ramos


### Problem Statement

Do frontier models learn, or just recall? How do we create a dataset that lies truly out of scope and that actually attempts to measure jaggedness in a real and practical way? The key learning in harness systems, where these systems tend to fail, happens within an agents context. Therefore a model must perform its learning by altering an external context AND effectively use that context. So we have two problems here, how good can a model create a learned context and how good can a model given a context apply those learnings to solve a problem, we then baseline this against a oneshot approach. 

### Task & benchmark construction

This now introduces GenoBench-Learning measures in-context learning using a pre/post study paradigm on stimuli designed to fall outside training data.

Each task presents the model with novel stimuli. The model is scored before and after a structured self-study phase in which it must articulate the underlying rule in its own words. Learning gain — the delta between pre- and post-study accuracy — is the primary signal.


### Dataset


### Technical details


### Results, insights, and conclusions
The benchmark reveals what standard evaluations cannot: not just whether a model knows things, but whether it can learn new things on demand, and whether explicit self-generated reasoning aids that learning.



### Organizational affiliations

Blue Origin; University of Washington. All work was completed using personal resources only, with no institutional support or resources.


### References & citations
