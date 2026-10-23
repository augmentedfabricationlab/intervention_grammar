# Installation

Intervention Grammar needs Python 3.9 or newer,
[COMPAS](https://compas.dev) 2.15.1 or newer and
[compas_model](https://github.com/blockresearchgroup/compas_model) 0.9.2 or newer, below 0.10.
compas_timber 2.2 requires compas_model 0.9.2, so the two packages share one environment.

## User

Clone the repository and install it into your environment:

```bash
git clone https://github.com/augmentedfabricationlab/intervention_grammar.git
pip install -e intervention_grammar
```

Check the installation:

```bash
python -c "import intervention_grammar; print(intervention_grammar.__version__)"
```

## Rhino 8 and Grasshopper

Rhino 8 runs Python 3.9. Find its Python with

```bash
python -m compas_rhino.print_python_path
```

and install the package there as well:

```bash
path/to/rhino/python -m pip install -e intervention_grammar
```

Or open any Python 3 script in Rhino 8, go to *Tools, Options* in the script
editor and add the `src` folder of the repository to the Python path.
compas_model has to be installed in Rhino's Python in that case.

`rhino/run_program.py` is the body of a Python 3 Script component in
Grasshopper. It runs a program on a model and outputs every state, one chosen
state, the log and the error. The program is a list of operation objects or
of text such as `Prosthesis("post_3", span=[0, 0.4])`.

## Developer

The repository follows the template of the Augmented Fabrication Lab. Install
the development dependencies, which include the tools for this documentation,
and make the project available in Rhino 8:

```bash
pip install -r requirements-dev.txt
invoke add-to-rhino
```

Recurring tasks run with [invoke](https://www.pyinvoke.org):

| Task | |
|---|---|
| `invoke test` | all checks and all tests |
| `invoke check` | README, flake8, import order and MANIFEST.in |
| `invoke docs` | this documentation, into `dist/docs` |
| `invoke clean` | remove generated files |
| `invoke release patch` | raise the version, test, build and upload |
| `invoke add-to-rhino` | install the project into the Python of Rhino 8 |

`mkdocs serve` shows the documentation while you write it. Every push to
master runs the tests and publishes the documentation to GitHub Pages.
