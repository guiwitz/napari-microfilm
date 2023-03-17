from itertools import count
import numpy as np
from .panel_item import PanelElement, PanelElementList


class NapariPanel:
    """Create microfilm panel via napari
    Parameters
    ----------
    viewer : napari.Viewer
        napari viewer.
    Attributes
    ----------
    key_frames : list of dict
        List of viewer state dictionaries.
    """

    def __init__(self, viewer):
        self.viewer = viewer
        self.frame = -1
        self.key_frames = PanelElementList()

        self.key_frames.events.changed.connect(self._on_panelitem_changed)

        self._panelitem_counter = count()  # track number of frames created

    def capture_panelitem(
        self, insert=True, position: int = None, pos_panel: list = None
    ):
        """Record current key-frame
        Parameters
        ----------
        insert : bool
            If captured key-frame should insert into current list or replace the current
            panelitem.
        position : int, optional
            If provided, place new frame at this index. By default, inserts at current
            active frame.
        pos_panel : list, optional
            If provided, name the frame with row and column indices [row, col]
        
        """

        if position is None:
            active_panelitem = self.key_frames.selection.active
            if active_panelitem:
                position = self.key_frames.index(active_panelitem)
            else:
                if insert:
                    position = -1
                else:
                    raise ValueError("No selected panelitem to replace !")

        new_frame = PanelElement.from_viewer(self.viewer)
        if pos_panel is None:
            new_frame.name = f"Key Frame {next(self._panelitem_counter)}"
        else:
            new_frame.name = f"Panel elem. [{pos_panel[0]}, {pos_panel[1]}]"

        if insert:
            self.key_frames.insert(position + 1, new_frame)
        else:
            self.key_frames[position] = new_frame

    def set_to_panelitem(self, frame: int):
        """Set the viewer to a given key-frame
        Parameters
        ----------
        frame : int
            Key-frame index to visualize
        """
        self.key_frames.selection.active = self.key_frames[frame]
        self.update_viewer(frame)
    
    def _on_panelitem_changed(self, event):
        self.key_frames.selection.active = event.value

    def update_viewer(self, panelitem_index):

        self.viewer.camera.update(self.key_frames[panelitem_index].viewer_state.camera)
        self.viewer.dims.update(self.key_frames[panelitem_index].viewer_state.dims)

        for layer_name, layer_state in self.key_frames[panelitem_index].viewer_state.layers.items():
            layer = self.viewer.layers[layer_name]
            for key, value in layer_state.items():
                original_value = getattr(layer, key)
                # Only set if value differs to avoid expensive redraws
                if not np.array_equal(original_value, value):
                    setattr(layer, key, value)



