from flax import struct

from finhjb.structure._grid import Grid
from finhjb.types import ArrayBool, ArrayFloat, ArrayInt


class AbstractSolverState(struct.PyTreeNode):
    """Abstract base class for solver states.

    Attributes
    ----------
    grid : Grid
        The computational grid containing state and value function information.
    best_error : ArrayFloat
        The best error observed during the iterations.
    last_update_step : ArrayFloat
        The iteration step at which the best error was last updated.
    patience_counter : ArrayInt
        Counter for tracking patience in convergence.
    converged : ArrayBool
        Flag indicating whether the solver has converged.
    early_stop : ArrayBool
        Flag indicating whether early stopping criteria have been met.
    iteration : ArrayInt
        The current iteration number.

    Properties
    ----------
    df : pd.DataFrame
        A pandas DataFrame containing the grid and policy information.

    """

    grid: Grid = struct.field(pytree_node=True, repr=False)

    best_error: ArrayFloat
    last_update_step: ArrayFloat

    patience_counter: ArrayInt
    converged: ArrayBool
    early_stop: ArrayBool

    iteration: ArrayInt

    @property
    def df(self):
        """Convert grid and policy to a pandas DataFrame."""
        return self.grid.df
