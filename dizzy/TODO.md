- service yml
  - [ ] auto task discovery

- Tests
  - [x] ServiceManager
  - [ ] EntityManager

# Features
- [ ] Composites: workflows on the fly with a simple DSL for result composition.
- [ ] Datagen (Entities, service folders, task folders - all yml files, etc)
- [ ] Project
## Maybe
- discover all workflows for client 
- allow ctx return from task? (semi-bug - circular ref if return ctx)
- entity yml
  - [ ] broadcast subservice to main controller. "fake common service"
  - [ ] save workflow or composite results to file for later use - project?
# BUGS
- Annoyingly, only dizae server/client logs right now. For some reason logfiles don't work at the right levels either.