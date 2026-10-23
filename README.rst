============================================================
Intervention Grammar
============================================================

.. start-badges

.. image:: https://img.shields.io/badge/License-MIT-blue.svg
    :target: https://github.com/augmentedfabricationlab/intervention_grammar/blob/master/LICENSE
    :alt: License MIT

.. image:: https://img.shields.io/badge/docs-latest-3070b3.svg
    :target: https://augmentedfabricationlab.github.io/intervention_grammar/latest/
    :alt: Documentation

.. end-badges

.. Write project description

**A grammar of interventions in existing structures.** A structure is a set of
members and their connections; operators change it, and approaches compose
operators into interventions: repairs, reinforcements, additions and
alterations. A program of operations runs on a model step by step, and its
inverse undoes it.


Main features
-------------

* Operators in four layers: structure, joint, process and knowledge
* Fourteen approaches composed of operators, for example Patch, Prosthesis, Replacement and Reinforcement
* ``run`` gives every state of a program and a log of its steps, ``inverse`` the program that undoes it
* Every operation is a COMPAS ``Data`` class and saves and loads as JSON
* The structure is a `compas_model <https://github.com/blockresearchgroup/compas_model>`_ ``Model``,
  so the same operations run on any compas_model element, for example the beams of a compas_timber model

**intervention_grammar** runs on Python 3.9 and newer, including the Python of Rhino 8.


Documentation
-------------

https://augmentedfabricationlab.github.io/intervention_grammar/latest/


Requirements
------------

* Windows 10/11
* Rhino 8 / Grasshopper (Python 3)
* `Anaconda Python <https://www.anaconda.com/download>`_
* `Visual Studio Code <https://code.visualstudio.com/>`_
* `Github Desktop <https://desktop.github.com/>`_

The package needs ``compas>=2.15.1`` and ``compas_model>=0.9.2,<0.10``.


Installation
------------

* Using GitHub Desktop, clone the `intervention_grammar <https://github.com/augmentedfabricationlab/intervention_grammar>`_
  repository into ``C:/Users/your_user_name/workspace/projects``.

* In an Anaconda prompt, create an environment and install the package into it::

    (base) conda create -n your_env_name python=3.9
    (base) conda activate your_env_name
    (your_env_name) pip install -e C:/Users/your_user_name/workspace/projects/intervention_grammar

* Find the Python of Rhino 8::

    (your_env_name) python -m compas_rhino.print_python_path

  It looks like ``C:/Users/your_user_name/.rhinocode/py39-rh8/python.exe``. Install the package there as well::

    (your_env_name) C:/Users/your_user_name/.rhinocode/py39-rh8/python.exe -m pip install -e C:/Users/your_user_name/workspace/projects/intervention_grammar

  ``invoke add-to-rhino`` does the same from the repository folder.


Example
-------

.. code-block:: python

    from intervention_grammar import demo, run, inverse, original_share
    from intervention_grammar import Probe, Prosthesis

    wall = demo.wall()
    program = [
        Probe("post_3", at=0.1, finding="damaged"),
        Prosthesis("post_3", length=0.4, joint={"family": "lap", "length": 0.3}),
    ]
    states = run(wall, program)

    for entry in states[-1].graph.attributes["log"]:
        print(entry["step"], entry["text"])
    print(original_share(states[-1]))
    print(inverse(wall, program))

``python examples/prosthesis.py`` prints the eleven steps, the original share
and the inverse. ``rhino/run_program.py`` is the body of a Grasshopper Python 3
component that runs a program on a model.


Contributing
------------

Make sure you setup your local development environment correctly:

* Clone the `intervention_grammar <https://github.com/augmentedfabricationlab/intervention_grammar>`__ repository.
* Install development dependencies and make the project accessible from Rhino:

::

    pip install -r requirements-dev.txt
    invoke add-to-rhino

During development, use tasks on the
command line to ease recurring operations:

* ``invoke clean``: Clean all generated artifacts.
* ``invoke check``: Run various code and documentation style checks.
* ``invoke docs``: Generate documentation.
* ``invoke test``: Run all tests and checks.
* ``invoke add-to-rhino``: Make the project accessible from Rhino.
* ``invoke``: Show available tasks.

For more details, check the `Contributor's Guide <CONTRIBUTING.rst>`_.

The documentation is published to GitHub Pages on every push to master.


Credits
-------------

This package was created by Tizian Rein <tizian.rein@tum.de> `@tizianrein <https://github.com/tizianrein>`_ at `@augmentedfabricationlab <https://github.com/augmentedfabricationlab>`_
