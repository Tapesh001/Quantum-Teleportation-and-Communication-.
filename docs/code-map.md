# Code by project part

| Project part | Source | Start reading at |
| --- | --- | --- |
| Input preparation, Bell resource and gates | [Numerical engine](../backend/engine.py) | input_state, h_gate, cnot, simulate |
| Measurement and classical communication | [Engine](../backend/engine.py) · [Browser controls](../frontend/app.js) | flip_patterns weights message errors; branches lists each received message and conditional correction |
| Bloch spheres and circuit | [Visual components](../frontend/views.js) | sphere projects the vector and six poles; circuit draws the quantum and classical wires |
| Fidelity and noise sweep | [Engine](../backend/engine.py) · [Experiment controls](../frontend/app.js) | six_state and prediction; sweep evaluates the 101 resource settings |
| Independent and linked errors | [Local service](../backend/server.py) | calculate evaluates both models at equal per-bit error rate |
| History and export | [Local service](../backend/server.py) | record, /api/history and /api/csv; existing journal schema remains compatible |
| Application layout | [HTML](../frontend/index.html) · [Styles](../frontend/styles.css) | Semantic page sections and responsive navigation |
| Optional desktop interface | [Lab](../desktop/teleportation_model.py) · [Spheres](../desktop/bloch_view.py) · [History](../desktop/history_view.py) | launch, BlochPair, History |
| Verification and packaging | [Tests](../tests/test_engine.py) · [Packager](../scripts/package.py) | Verification; run the packager from any directory |

The Windows launcher starts [run.py](../run.py), which serves the frontend and the JSON API from the same loopback address. Only calculated runs are stored in the local journal; on Windows it resides in %LOCALAPPDATA%/QuantumTeleportation/history.sqlite3.
