import inspect
from dataclasses import dataclass, field
from functools import cached_property
from graphlib import CycleError, TopologicalSorter
from typing import Callable, Generic, Iterable, Optional

from finhjb.interface.parameter import P
from finhjb.structure._boundary import (
    DependencyMethod,
    ImmutableBoundary,
)
from finhjb.structure._grid import Grid
from finhjb.types import BOUNDARY_NAMES, BoundaryName


@dataclass(frozen=True)
class BoundaryConditionTarget:
    """
    This class is used to specify the boundary condition target.

    Attributes
    ----------
    boundary_name : BoundaryName
        The name of the boundary.
    condition_func : Callable[["Grid"], float]
        The condition function.
    low : Optional[float]
        The lower bound of the condition function.
    high : Optional[float]
        The upper bound of the condition function.
    tol : float
        The tolerance of the condition function.
    max_iter : int
        The maximum number of iterations of the condition function.
    """

    boundary_name: BoundaryName
    condition_func: Callable[["Grid"], float]
    # Optional parameters for Bisection method
    low: Optional[float] = None
    high: Optional[float] = None
    tol: float = 1e-6
    max_iter: int = 50


@dataclass
class AbstractBoundary(Generic[P]):
    """
    An intelligent, auto-configuring class for defining HJB problem boundaries.

    This class serves as a configuration object for boundary values.
    It automatically discovers dependencies between boundaries by
    inspecting the signatures of `compute_<boundary_name>` methods defined in subclasses.

    Usage
    -----
    1. Subclass AbstractBoundary.
    2. For boundaries that can be computed from parameters or other boundaries,
       define methods like `compute_v_right(self, s_max: float) -> float`.
       The dependency (`s_max`) is automatically inferred from the signature.
    3. Instantiate the subclass, providing any boundary values that cannot be
       computed as keyword arguments (e.g., `MyBoundary(p=params, s_min=0.0)`).

    Examples
    --------
    ```python
    >>> class MyBoundary(AbstractBoundary):
    ...     def compute_s_max(self) -> float:
    ...         return self.p.x_bar
    ...     def compute_v_right(self, s_max: float) -> float:
    ...         return s_max * 2.0
    >>> boundary = MyBoundary(p=params, s_min=0.0, v_left=0.0)
    >>> frozen_boundary = boundary.frozen_boundary
    ```

    Attributes
    ----------
    p : Parameter
        The parameter object containing model parameters.
    s_min : Optional[float]
        The minimum state boundary value.
    s_max : Optional[float]
        The maximum state boundary value.
    v_left : Optional[float]
        The value function at the left boundary.
    v_right : Optional[float]
        The value function at the right boundary.
    already_boundary : dict[BoundaryName, float]
        A dictionary of boundary values that were provided directly.
    independent_boundary : set[BoundaryName]
        A set of boundary names that were provided directly.
    frozen_boundary : ImmutableBoundary
        The fully computed and immutable boundary object.
    required_boundary : set[BoundaryName]
        A set of all boundary names required to compute the full boundary.
    boundary_dependencies : dict[BoundaryName, set[BoundaryName]]
        A mapping of boundary names to their dependencies.
    graph : list[DependencyMethod]
        A topologically sorted list of methods to compute boundary values.
    """

    p: P = field(repr=False)
    s_min: Optional[float] = None
    s_max: Optional[float] = None
    v_left: Optional[float] = None
    v_right: Optional[float] = None

    already_boundary: dict[BoundaryName, float] = field(init=False, repr=False)
    independent_boundary: set[BoundaryName] = field(init=False, repr=False)

    frozen_boundary: ImmutableBoundary = field(init=False, repr=False)

    def __post_init__(self):
        ...
        # Compute and store the frozen boundary upon initialization
        self.frozen_boundary = self.freeze()

    @cached_property
    def required_boundary(self) -> set[BoundaryName]:
        """All dependencies required to compute boundaries."""
        return {dep for deps in self.boundary_dependencies.values() for dep in deps}

    @cached_property
    def boundary_dependencies(
        self,
    ) -> dict[BoundaryName, set[BoundaryName]]:
        """Dict of compute methods and their dependencies."""
        dependency_dict: dict[BoundaryName, set[BoundaryName]] = {}
        for name in BOUNDARY_NAMES:
            compute_method_name = f"compute_{name}"
            if hasattr(self, compute_method_name):
                method = getattr(self, compute_method_name)
                if getattr(self, name) is not None:
                    raise ValueError(
                        f'Boundary "{name}" and its compute method "{compute_method_name}()" cannot be defined simultaneously!'
                    )
                if not callable(method):
                    raise TypeError(
                        f"Attribute '{compute_method_name}' must be callable."
                    )
                sig = inspect.signature(method)
                dependencies: set[BoundaryName] = set(
                    filter(lambda b: b != "p", sig.parameters.keys())
                )  # pyright: ignore[reportAssignmentType]
                if dependencies:
                    dependency_dict[name] = dependencies  # pyright: ignore[reportArgumentType]
                else:
                    setattr(self, name, method(p=self.p))
        # Store already provided boundary values
        self.already_boundary = {  # pyright: ignore[reportAttributeAccessIssue]
            name: getattr(self, name)
            for name in BOUNDARY_NAMES
            if getattr(self, name) is not None
        }
        self.independent_boundary = set(self.already_boundary.keys())
        return dependency_dict

    @cached_property
    def graph(self) -> list[DependencyMethod]:
        """
        Topologically sorted list of methods to compute boundary values.

        Returns
        -------
        list[DependencyMethod]
            A list of methods with their metadata, sorted in the order they should be executed.

        Raises
        ------
        ValueError
            If there are circular dependencies or missing dependencies.
        """
        try:
            order: Iterable[BoundaryName] = TopologicalSorter(
                self.boundary_dependencies
            ).static_order()
        except CycleError as e:
            raise ValueError(
                f"Circular dependency detected in boundary calculations. "
                f"Dependencies: {self.boundary_dependencies}"
            ) from e
        methods = []
        i = 1
        for name in order:
            if name in self.already_boundary:
                continue
            required_deps = self.boundary_dependencies[name]
            if missing_deps := required_deps - self.already_boundary.keys():
                raise ValueError(
                    f"Cannot compute '{name}': missing dependencies {missing_deps}. "
                    f"These must be either provided in the constructor or have their own compute_* methods."
                )
            methods.append(
                DependencyMethod(
                    order=i,
                    name=name,
                    deps=required_deps,
                    method=getattr(self, f"compute_{name}"),
                )
            )
            i += 1
        return methods

    def freeze(self):
        """
        Computes and returns an ImmutableBoundary with all boundary values set.

        Returns
        -------
        ImmutableBoundary
            The fully computed and validated immutable boundary object.
        """
        if not self.boundary_dependencies:
            return self._create_boundary(self.already_boundary)
        for item in self.graph:
            name = item["name"]
            method = item["method"]
            deps = item["deps"]
            self.already_boundary[name] = method(
                **{dep: self.already_boundary[dep] for dep in deps} | {"p": self.p}
            )
        return self._create_boundary(self.already_boundary)

    def _create_boundary(self, values: dict[BoundaryName, float]) -> ImmutableBoundary:
        """
        Creates an ImmutableBoundary after validating all values are present and valid.

        Parameters
        ----------
        values : dict[BoundaryName, float]
            Dictionary containing all four boundary values.

        Returns
        -------
        ImmutableBoundary
            The validated immutable boundary object.

        Raises
        ------
        ValueError
            If any boundary values are missing or invalid.
        """
        # Validate all boundaries are present
        missing = set(BOUNDARY_NAMES) - values.keys()
        if missing:
            raise ValueError(
                f"Could not determine all boundary values. Missing: {missing}"
            )

        # Semantic validation
        if values["s_min"] >= values["s_max"]:
            raise ValueError(
                f"Invalid boundary: s_min ({values['s_min']}) must be "
                f"strictly less than s_max ({values['s_max']})."
            )

        # print(f"Computed boundary values: {values}")

        return ImmutableBoundary(
            s_min=float(values["s_min"]),
            s_max=float(values["s_max"]),
            v_left=float(values["v_left"]),
            v_right=float(values["v_right"]),
            graph=self.graph,
        )
