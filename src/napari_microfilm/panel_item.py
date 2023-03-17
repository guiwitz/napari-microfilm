from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from napari.utils.events import SelectableEventedList

from .utils import make_thumbnail

if TYPE_CHECKING:
    import napari


@dataclass(frozen=True)
class ViewerState:
    """The state of the viewer camera, dims, and layers.
    Parameters
    ----------
    camera : dict
        The state of the `napari.components.Camera` in the viewer.
    dims : dict
        The state of the `napari.components.Dims` in the viewer.
    layers : dict
        A map of layer.name -> _base_state for each layer in the viewer
        (excluding metadata).
    """

    camera: dict
    dims: dict
    layers: dict

    @classmethod
    def from_viewer(cls, viewer: napari.viewer.Viewer):
        """Create a ViewerState from a viewer instance."""
        layers = {
            layer.name: layer._get_base_state() for layer in viewer.layers
        }
        for d in layers.values():
            d.pop("metadata")
        return cls(
            camera=viewer.camera.dict(), dims=viewer.dims.dict(), layers=layers
        )

    def apply(self, viewer: napari.viewer.Viewer):
        """Update `viewer` to match this ViewerState.
        Parameters
        ----------
        viewer : napari.viewer.Viewer
            A napari viewer. (viewer state will be directly modified)
        """

        viewer.camera.update(self.camera)
        viewer.dims.update(self.dims)

        for layer_name, layer_state in self.layers.items():
            layer = viewer.layers[layer_name]
            for key, value in layer_state.items():
                original_value = getattr(layer, key)
                # Only set if value differs to avoid expensive redraws
                if not np.array_equal(original_value, value):
                    setattr(layer, key, value)

    def render(
        self, viewer: napari.viewer.Viewer, canvas_only=True
    ) -> np.ndarray:
        """Render this ViewerState to an image.
        Parameters
        ----------
        viewer : napari.viewer.Viewer
            A napari viewer to render screenshots from.
        canvas_only : bool, optional
            Whether to include only the canvas (and exclude the napari
            gui), by default True
        Returns
        -------
        np.ndarray
            An RGBA image of shape (h, w, 4).
        """
        self.apply(viewer)
        return viewer.screenshot(canvas_only=canvas_only)

    def __eq__(self, other):
        if isinstance(other, ViewerState):
            return (
                self.camera == other.camera
                and self.dims == other.dims
                and self.layers == other.layers
            )
        else:
            return False


# @dataclass(frozen=True)
@dataclass  # we want to modify steps and ease from the widget for instance
class PanelElement:
    """A single keyframe in the animation.
    Parameters
    ----------
    viewer_state : ViewerState
        The state of the viewer at this keyframe.
    thumbnail : np.ndarray
        A thumbnail representing this keyframe.
    snapshot: np.ndarray
        The snapshot corresponding to the view
    name : str
        A name for the keyframe.
    """

    viewer_state: ViewerState
    thumbnail: np.ndarray
    snapshot: np.ndarray
    name: str = "PanelElement"

    def __str__(self):
        return self.name

    @classmethod
    def from_viewer(
        cls, viewer: napari.viewer.Viewer
    ):
        """Create a PanelElement from a viewer instance."""
        return cls(
            viewer_state=ViewerState.from_viewer(viewer),
            thumbnail=make_thumbnail(viewer.screenshot(canvas_only=True)),
            snapshot=viewer.screenshot(canvas_only=True),
        )

    def __repr__(self) -> str:
        return f"<PanelElement: {self.name}>"

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other):
        if isinstance(other, PanelElement):
            return (
                self.__hash__() == other.__hash__()
                and self.viewer_state == other.viewer_state
                and (self.thumbnail == other.thumbnail).all()
                and (self.snapshot == other.snapshot).all()
            )
        else:
            return False


class PanelElementList(SelectableEventedList[PanelElement]):
    def __init__(self) -> None:
        super().__init__(basetype=PanelElement)