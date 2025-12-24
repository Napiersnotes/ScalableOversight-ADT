# ScalableOversight-ADT

**Adversarial Deliberation Trees with Mechanistic Verification for scalable LLM oversight**

A full oversight framework combining:
- Recursive adversarial deliberation
- Judge mediation
- Mechanistic verification stub
- Hybrid routing
- Evaluated on 150 MATH + 500 GSM8K problems (~49% MAE reduction)

Built in December 2025.

## Features
- Recursive adversarial debate
- Pessimistic aggregation and judge mediation
- Mechanistic hard-fail-safe (simulated SAE deception detection)
- Hybrid routing (ADT + mechanistic on conflict/high uncertainty)
- Live tracing and node counting

## Quickstart

See `notebooks/demo.ipynb` for a full example.

## Results
- Average 49% MAE reduction vs single overseer
- Mechanistic layer adds +8% improvement
- Tested on MATH and GSM8K

## Paper
See `paper/adt_paper.tex` (preprint in preparation).

## Related Project
[TruthProbe](https://github.com/Napiersnotes/TruthProbe) – lightweight deception detector

## License
MIT – use, modify, share freely.
