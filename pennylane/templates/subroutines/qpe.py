# Copyright 2018-2021 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Contains the ``QuantumPhaseEstimation`` template.
"""
from numpy.linalg import eig

import pennylane as qml
from pennylane.templates.decorator import template
from pennylane.wires import Wires


@template
def QuantumPhaseEstimation(unitary, target_wires, estimation_wires):
    r"""Performs the
    `quantum phase estimation <https://en.wikipedia.org/wiki/Quantum_phase_estimation_algorithm>`__
    circuit.

    Given a unitary matrix :math:`U`, this template applies the circuit for quantum phase
    estimation. The unitary is applied to the qubits specified by ``target_wires`` and :math:`n`
    qubits are used for phase estimation as specified by ``estimation_wires``.

    .. figure:: ../../_static/templates/subroutines/qpe.svg
        :align: center
        :width: 60%
        :target: javascript:void(0);

    This circuit can be used to perform the standard quantum phase estimation algorithm, consisting
    of the following steps:

    #. Prepare ``target_wires`` in an eigenstate of :math:`U`. If that eigenstate has a
       corresponding eigenvalue :math:`e^{2 \pi i \theta}` with phase :math:`\theta \in [0, 1)`,
       this algorithm will measure :math:`\theta`.
    #. Apply the ``QuantumPhaseEstimation`` circuit.
    #. Measure ``estimation_wires`` using :func:`~.probs`, giving a probability distribution over
       measurement outcomes in the computational basis.
    #. Find the index of the largest value in the probability distribution and divide that number by
       :math:`2^{n}`. This number will be an estimate of :math:`\theta` with an error that decreases
       exponentially with the number of qubits :math:`n`.

    Note that if :math:`\theta \in (-1, 0]`, we can estimate the phase by again finding the index
    :math:`i` found in step 4 and calculating :math:`\theta \approx \frac{1 - i}{2^{n}}`. The
    usage details below give an example of this case.

    Args:
        unitary (array): the phase estimation unitary, specified as a matrix
        target_wires (Union[Wires, Sequence[int], or int]): the target wires to apply the unitary
        estimation_wires (Union[Wires, Sequence[int], or int]): the wires to be used for phase
            estimation

    Raises:
        QuantumFunctionError: if the ``target_wires`` and ``estimation_wires`` share a common
            element

    .. UsageDetails::

        Consider the matrix corresponding to a rotation from an :class:`~.RX` gate:

        .. code-block:: python

            import pennylane as qml
            from pennylane.templates import QuantumPhaseEstimation
            from pennylane import numpy as np

            phase = 5
            target_wires = [0]
            u = qml.RX(phase, wires=0).matrix

        The ``phase`` parameter can be estimated using ``QuantumPhaseEstimation``. An example is
        shown below using a register of five phase-estimation qubits:

        .. code-block:: python

            n_estimation_wires = 5
            estimation_wires = range(1, n_estimation_wires + 1)

            dev = qml.device("default.qubit", wires=n_estimation_wires + 1)

            @qml.qnode(dev)
            def circuit():
                # Start in the |+> eigenstate of the unitary
                qml.Hadamard(wires=target_wires)

                QuantumPhaseEstimation(
                    u,
                    target_wires=target_wires,
                    estimation_wires=estimation_wires,
                )

                return qml.probs(estimation_wires)

            phase_estimated = np.argmax(circuit()) / 2 ** n_estimation_wires

            # Need to rescale phase due to convention of RX gate
            phase_estimated = 4 * np.pi * (1 - phase)
    """

    target_wires = Wires(target_wires)
    estimation_wires = Wires(estimation_wires)

    if len(Wires.shared_wires([target_wires, estimation_wires])) != 0:
        raise qml.QuantumFunctionError("The target wires and estimation wires must be different")

    unitary_powers = [unitary]

    for i in range(len(estimation_wires) - 1):
        new_power = unitary_powers[0] @ unitary_powers[0]
        unitary_powers.insert(0, new_power)

    for wire, u in zip(estimation_wires, unitary_powers):
        qml.Hadamard(wire)
        qml.ControlledQubitUnitary(u, control_wires=wire, wires=target_wires)

    qml.QFT(wires=estimation_wires).inv()
