# OBM Python Version

This repository contains a Python port of an atmospheric chemistry box model (OBM), originally derived from the Matlab/F0AM workflow. It keeps three application shapes:

- `offline_test/`: local development and testing scripts for EKMA and RIR.
- `online_app/`: Linux/server gRPC service used by backend systems.
- `desktop_app/`: PyQt6 desktop application wrapper.

During this cleanup, large `txt` and `m` mechanism files under `CB05/` and `MCMv331/` were intentionally not inspected. No packages or libraries were installed.

## Repository Layout

| Path | Purpose |
| --- | --- |
| `core/` | Model core: chemistry initialization, EKMA/RIR orchestration, F0AM-style solver wrapping, ODE/Jacobian code, and core physical quantities such as number density and humidity conversion. |
| `CB05/` | CB05 mechanism code, reactions, rate constants, and species transformation. |
| `MCMv331/` | MCM v3.3.1 Python mechanism modules. Mostly preserved; normal workflows default to CB05. |
| `tool/` | Non-core utilities: IOA, averaging, file conversion, progress display, path/hash helpers, and optional UI helper features. |
| `photolysis/` | Photolysis-rate calculation and interpolation helpers. |
| `post_process/` | Plotting for EKMA, ozone production, OH reactivity, and photolysis rates. |
| `offline_test/` | Local script entry points. |
| `online_app/` | gRPC server and test client. |
| `desktop_app/` | PyQt6 UI and desktop wrappers. |
| `media/` | Image assets used by the desktop UI. |

## Entry Points

### Offline Testing

- EKMA: `offline_test/OBM_EKMA_1day.py`
- RIR: `offline_test/OBM_RIR.py`

These scripts still contain local hard-coded paths for input data, comparison tables, logs, and output folders. Update `main_path`, `data_file`, `compound_name_file`, and related variables before running them on a new machine.

### Online Service

- Server: `online_app/OBM_grpc.py`
- Test client: `online_app/OBM_grpc_client.py`

The gRPC service listens on port `8769` by default. Requests and responses are string payloads, normally JSON strings. The request field `model` controls routing:

- `model == 1`: EKMA workflow.
- `model == 2`: RIR workflow.

### Desktop Application

- UI entry point: `desktop_app/UI.py`
- Desktop EKMA wrapper: `desktop_app/OBM_EKMA_1day2.py`
- Desktop RIR wrapper: `desktop_app/OBM_RIR2.py`

The desktop application requires PyQt6. Image assets are stored in `media/`.

## Dependencies

There is no dependency lock file in this repository. Based on static imports, the main dependencies are:

- Data and numerics: `numpy`, `pandas`, `scipy`
- Plotting: `matplotlib`, `pylab`
- High-performance solver path: `jitcode`, `symengine`
- Online service: `grpcio`
- Desktop UI: `PyQt6`
- Optional/helper features: `pyaudio`, `pygame`, `diffeqpy`, `numba`

No dependencies were installed as part of this cleanup. Before running the model, install the appropriate dependencies in the target environment and verify that `core/solver.so`, `core/solver2.so`, `core/solver.pyd`, and `core/solver2.pyd` match the platform, Python version, and mechanism settings.

## Main Workflows

EKMA workflow:

1. The entry script reads monitored data and the species comparison table.
2. `tool.data_average` computes daily averages and VOCs/NOx means.
3. `CB05.CB05_transfrom` maps monitored compounds to CB05 species.
4. `core.data_run` builds the NOx/VOCs scenario matrix.
5. `core.F0AM_ModelCore2` initializes chemistry and integrates each scenario.
6. `core.jit_solver.solver3` calls the compiled solver module.
7. `post_process.plot` renders the EKMA plot.

RIR workflow:

1. The entry script reads monitored data and the comparison table.
2. `core.RIR_data_process` prepares daily or hourly input data.
3. `core.RIR_data_run2.initialize` warms up the model and writes intermediate `result.json`.
4. `core.RIR_data_run2.update` builds reduction scenarios and computes RIR, ozone production/loss, OH reactivity, and photolysis outputs.
5. `post_process.plot_ozone`, `plot_OH`, and `plot_photolysis` render figures.

See [ARCHITECTURE_EN.md](ARCHITECTURE_EN.md) for the English architecture document, [ARCHITECTURE.md](ARCHITECTURE.md) for the Chinese version, and [CHEMICAL_REACTIONS.md](CHEMICAL_REACTIONS.md) for the core chemical equations.

## Fixes and Structure Updates Applied

- Fixed package imports for `InitializeChemistry` in `core/F0AM_ModelCore.py` and `core/F0AM_ModelCore2.py`.
- Fixed a Python runtime error in `core/InitializeChemistry.py` where `dict_keys` was used like a list.
- Made gRPC imports under `online_app/` work both as package imports and local script imports.
- Added the missing `online_app/receiver_pb2.py` with the string messages used by the current gRPC service.
- Fixed desktop UI references to image assets in `media/` and to the desktop RIR module.
- Fixed EKMA victory-sound paths so they point to `tool/ffVII_victory.wav`.
- Moved core solver and chemistry-initialization files from `tool/` to `core/`: `AddSpecies.py`, `CovertHumidity.py`, `NumberDensity.py`, `dydt_eval.py`, `Jac_eval.py`, `ode15s.py`, `jit_solver.py`, `julia_solver.py`, and the compiled solver binaries.

## Lightweight Verification

The following syntax-only check was run:

```bash
python3 - <<'PY'
import pathlib, py_compile
for p in sorted(pathlib.Path('.').rglob('*.py')):
    if any(part in {'.git', '__pycache__'} for part in p.parts):
        continue
    py_compile.compile(str(p), doraise=True)
PY
```

Result: all Python files passed compilation.

## Notes

- Several scripts still use historical hard-coded local paths and should be configured before deployment.
- The online gRPC server contains a hardware hash check. Update it using `tool/hash.py` when moving to a new server.
- MCM is much larger than CB05. The current compiled-solver path is mainly practical for CB05; switching to MCM requires a separate performance and solver-build review.
- `core/julia_solver.py` is an experimental solver path; `tool/funny.py` and similar modules are optional helper features and are not required for the main workflows.
