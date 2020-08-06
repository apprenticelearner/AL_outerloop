**********************************************
Apprentice Learner Architecture / AL_Outerloop
**********************************************

.. image:: https://travis-ci.org/apprenticelearner/AL_outerloop.svg?branch=master
    :target: https://travis-ci.org/apprenticelearner/AL_outerloop

.. image:: https://coveralls.io/repos/github/apprenticelearner/AL_outerloop/badge.svg
	:target: https://coveralls.io/github/apprenticelearner/AL_outerloop


.. image:: https://readthedocs.org/projects/al-outerloop/badge/?version=latest
	:target: https://al-core.readthedocs.io/projects/AL_Outerloop/en/latest/?badge=latest
	:alt: Documentation Status

The Apprentice Learner Architecture provides a framework for modeling and simulating learners working educational technologies. There are three general GitHub repositories for the AL Project: 

1. **AL_Core** (https://github.com/apprenticelearner/AL_Core), which is the core library for learner modeling used to configure and instantiate agents and author their background knowledge. 
2. **AL_Train** (https://github.com/apprenticelearner/AL_Train), which contains code for interfacing AL agents with CTAT-HTML tutors and running training experiments.
3. **AL_Outerloop** (this repository), which provides additional functionality to AL_Train simulating adaptive curricula.


This repository does the following:

1. Provides functionality to the `altrain` script to use adaptive sequencing controllers for learner simulations.

Installation
============

To install the AL_Outerloop library, first follow the installation instructions for the `AL_Core <https://github.com/apprenticelearner/AL_Core>`_ and `AL_Train <https://github.com/apprenticelearner/AL_Train>`_ Libraries. Next, `clone the respository <https://help.github.com/en/articles/cloning-a-repository>`_ to your machine using the GitHub deskptop application or by running the following command in a terminal / command line:

.. code-block:: bash

	git clone https://github.com/apprenticelearner/AL_Outerloop


Navigate to the directory where you cloned AL_Outerloop in a terminal / command line and run:

.. code-block:: bash

	python -m pip install -e .

Everything should now be fully installed and ready.

Important Links
===============

* Source code: https://github.com/apprenticelearner/AL_Outerloop
* Documentation: https://al-core.readthedocs.io/en/latest/

Examples
========

We have created a number of examples to demonstrate basic usage of the Appentice Learner that make use of this repository as well as the `AL_Core <https://github.com/apprenticelearner/AL_Core>`_ and `AL_Train <https://github.com/apprenticelearner/AL_Train>`_ Libraries. These can be found on the `examples page <https://github.com/apprenticelearner/AL_Core/wiki/Examples>`_ of the AL_Core wiki.

Citing this Software
====================

If you use the broader Apprentice Learner Architecture in a scientific publication, then we would appreciate a citation of the following paper:

Christopher J MacLellan, Erik Harpstead, Rony Patel, and Kenneth R Koedinger. 2016. The Apprentice Learner Architecture: Closing the loop between learning theory and educational data. In Proceedings of the 9th International Conference on Educational Data Mining - EDM ’16, 151–158. Retrieved from http://www.educationaldatamining.org/EDM2016/proceedings/paper_118.pdf

Bibtex entry::

	@inproceedings{MacLellan2016a,
	author = {MacLellan, Christopher J and Harpstead, Erik and Patel, Rony and Koedinger, Kenneth R},
	booktitle = {Proceedings of the 9th International Conference on Educational Data Mining - EDM '16},
	pages = {151--158},
	title = {{The Apprentice Learner Architecture: Closing the loop between learning theory and educational data}},
	url = {http://www.educationaldatamining.org/EDM2016/proceedings/paper{\_}118.pdf},
	year = {2016}
	}
