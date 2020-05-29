import numpy as np


class SpaceConvention:
    """Class for describing an anatomical 3D space convention.
    Drops the infinitely confusing (x, y, z) for a more semantic specification
    of the ordering and orientation.

    The space is described with an `origin` tuple that specifies
    "to which anatomical direction the 0 of the stack correspond along each
    of the 3 dimensions".

    E.g., in the Allen Brain (http://help.brain-map.org/display/mousebrain/API):
        0. first axis goes from Anterior to posterior;
        1. second axis goes from Dorsal to ventral;
        2. third axis goes from Left to right.

    Therefore, the Allen space can be described with an instance defined in
    any of the following ways:

    >>> SpaceConvention("ADL")
    >>> SpaceConvention(["a", "d", "l"])
    >>> SpaceConvention(["anterior", "dorsal", "left"])

    This can be convenient for quickly reorient a stack to match different
    axes convention.

    Transformations generate with this class ARE NOT proper transformations from
    space a to space b! They are transformations of space a to a new standard
    orientation matching the convention of space B. This can be very useful
    as a pre-step for an affine transformation but does not implement it.

    Parameters
    ----------
    origin : str or tuple of str or list of str
        Each letter or initial of each string should match a letter in s
        pace_specs
    shape : tuple, optional
        Shape of the bounding box of the space (e.g. shape of a stack)
    """

    # Use sets to avoid any explicit convention definition:
    space_specs = {
        "sagittal": {"p", "a"},
        "vertical": {"s", "i"},
        "frontal": {"l", "r"},
    }

    # Map limits letters to complete names
    lims_labels = {
        "p": "Posterior",
        "a": "Anterior",
        "s": "Superior",
        "i": "Inferior",
        "l": "Left",
        "r": "Right",
    }

    def __init__(self, origin, shape=(None, None, None), resolution=(1, 1, 1)):

        # Reformat to lowercase initial:
        origin = [o[0].lower() for o in origin]

        assert all([o in self.lims_labels.keys() for o in origin])

        axs_description = []

        # Loop over origin specification:
        for lim in origin:

            # Loop over possible axes and origin values:
            for k, possible_lims in self.space_specs.items():

                # If origin specification in possible values:
                if lim in possible_lims:
                    # Define orientation string with set leftout element:
                    axs_description.append(
                        ordered_list_from_set(possible_lims, lim)
                    )

        # Makes sure we have a full orientation:
        assert len(axs_description) == 3
        assert len(axs_description) == len(set(axs_description))

        # Univoke description of the space convention with a tuple of axes lims:
        self.axes_description = tuple(axs_description)

        self.shape = shape
        self.resolution = resolution

    @property
    def axes_order(self):
        """
        Returns
        -------
        tuple
            `self.space_specs` keys specifying axes order.
        """
        order = []
        for lims in self.axes_description:
            order += [
                k for k, val in self.space_specs.items() if lims[0] in val
            ]

        return tuple(order)

    @property
    def origin(self):
        """
        Returns
        -------
        tuple
            Three letters specifying origin position.
        """
        return tuple([lim[0] for lim in self.axes_description])

    def map_to(self, target):
        """Find axes reordering and flips required to go to
        target space convention.

        Parameters
        ----------
        target : SpaceConvention object
            Target space convention.

        Returns
        -------
        tuple
            Axes order to move to target space.
        tuple
            Sequence of flips to move to target space (in target axis order).

        """
        # Get order of matching axes:
        order = tuple([self.axes_order.index(ax) for ax in target.axes_order])

        # Detect required flips:
        flips = tuple(
            [
                self.axes_description[si] != target.axes_description[ti]
                for ti, si in enumerate(order)
            ]
        )

        return order, flips

    def map_stack_to(self, stack, target, copy=False):
        """Transpose and flip stack to move it to target space convention.
        stack : numpy array
            Stack to map from space convention a to space convention b
        target : SpaceConvention object
            Target space convention.
        copy : bool, optional
            If true, stack is copied.

        Returns
        -------

        """

        # Find order swapping and flips:
        order, flips = self.map_to(target)

        # If we want to work on a copy, create:
        if copy:
            stack = stack.copy()

        # Transpose axes:
        stack = np.transpose(stack, order)

        # Flip as required:
        stack = np.flip(stack, [i for i, f in enumerate(flips) if f])

        return stack

    def transformation_matrix_to(self, target):
        """Find transformation matrix going to target space convention.
        Parameters
        ----------
        target : SpaceConvention object
            Target space convention.

        Returns
        -------

        """

        # Find axorder swapping and flips:
        order, flips = self.map_to(target)

        transformation_mat = np.zeros((4, 4))
        transformation_mat[-1, -1] = 1
        for ai, (bi, f) in enumerate(zip(order, flips)):
            transformation_mat[ai, bi] = -1 if f else 1

            transformation_mat[ai, 3] = self.shape[ai] if f else 0

        return transformation_mat

    def map_points_to(self, pts, target):
        """Map points to target space convention.
        Parameters
        ----------
        pts : (n, 3) numpy array with the points to be mapped.
        target : SpaceConvention object
            Target space convention.

        Returns
        -------

        """


def ordered_list_from_set(input_set, first):
    """
    Parameters
    ----------
    input_set : set
        2-elements set
    first :
        First element for the output list

    Returns
    -------

    """
    return first + next(iter(input_set - {first}))