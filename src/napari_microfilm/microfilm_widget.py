"""
This module implements a napari widget to create microfilm images interactively
by capturing views.
"""

import string
from pathlib import Path
from qtpy.QtWidgets import (QWidget, QPushButton, QSpinBox,
QGroupBox, QGridLayout, QVBoxLayout, QLabel, QColorDialog,
QTabWidget, QLineEdit, QCheckBox, QSizePolicy, QFileDialog)
from qtpy.QtGui import QPixmap, QColor
from qtpy.QtCore import Qt
from cmap import Colormap

import microfilm.microplot
from microfilm import colorify
import numpy as np
from .napari_panel import NapariPanel
from .panel_list_control_widget import PanelElementListControlWidget
from .panel_items_widget import PanelItemListWidget


class MicrofilmWidget(QWidget):
    
    def __init__(self, napari_viewer, parent=None):
        super().__init__(parent=parent)
        self.viewer = napari_viewer

        self.napari_panel = NapariPanel(viewer=self.viewer)

        self.panelElementListControlWidget = PanelElementListControlWidget(
            napari_panel=self.napari_panel, parent=self
        )

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)
        self.tabs = QTabWidget()

        # main tab
        self.main = QWidget()
        self._main_layout = QVBoxLayout()
        self.main.setLayout(self._main_layout)
        self.tabs.addTab(self.main, 'main')
        self._layout.addWidget(self.tabs)

        # options tab
        self.options = QWidget()
        self._options_layout = QVBoxLayout()
        self.options.setLayout(self._options_layout)
        self.tabs.addTab(self.options, 'options')
        self._layout.addWidget(self.tabs)

        # add control for panel grid dimensions
        self._initialize_panel_grid_control(self._main_layout)

        self.pixlabel = QLabel()
        # add preview to main view. Not ideal for large panels
        # self._main_layout.addWidget(self.pixlabel)
        #self.pixlabel.setFixedWidth(900)
        self.pixlabel.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding)
        self.pixlabel.resizeEvent = self._on_resize_preview

        # initialize panel element list
        self._init_panel_items_widget(self._main_layout)
        self._main_layout.addWidget(self.panelElementListControlWidget)
        
        # Label options
        self.label_group = QGroupBox('Label')
        self.label_group.setAlignment(Qt.AlignTop)
        self.label_group.setLayout(QGridLayout())
        self._options_layout.addWidget(self.label_group)

        self._label_checkbox = QCheckBox()# QPushButton()
        self._label_checkbox.setText('Add labels')
        self.label_group.layout().addWidget(self._label_checkbox, 0,0,1,2, Qt.AlignTop)

        # label font size
        self.label_group.layout().addWidget(QLabel('Label size'), 1 ,0, Qt.AlignTop)
        self._label_size = QSpinBox()
        self._label_size.setValue(12)
        self.label_group.layout().addWidget(self._label_size, 1, 1, Qt.AlignTop)
        
        # Label Color dialogue
        self._color_dialog()
        self._label_color_button = QPushButton()
        self._label_color_button.setText('Choose label color')
        self.label_group.layout().addWidget(self._label_color_button, 2, 0, 1, 2)
        self._label_color_button.clicked.connect(self._open_color_dialog)

        # Pick labels
        self.label_group.layout().addWidget(QLabel('Custom labels'), 3, 0, Qt.AlignTop)
        self._label_custom = QLineEdit()
        self._label_custom.setText("")
        self.label_group.layout().addWidget(self._label_custom, 3, 1, Qt.AlignTop)

        # channel label options
        self.channellabel_group = QGroupBox('Channel Labels')
        self.channellabel_group.setAlignment(Qt.AlignTop)
        self.channellabel_group.setLayout(QGridLayout())
        self._options_layout.addWidget(self.channellabel_group)

        # initialize controls for adding plot title (not used)
        self._check_channel_labels = QCheckBox()
        self._check_channel_labels.setText('Show channel labels')
        self.channellabel_group.layout().addWidget(self._check_channel_labels, 0, 0, Qt.AlignTop)
        
        self.channellabel_group.layout().addWidget(QLabel('Label size'), 1 ,0, Qt.AlignTop)
        self._channellabel_size = QSpinBox()
        self._channellabel_size.setMaximum(100)
        self._channellabel_size.setMinimum(1)
        self._channellabel_size.setValue(5)
        self.channellabel_group.layout().addWidget(self._channellabel_size, 1, 1, Qt.AlignTop)

        # Saving options
        self.save_group = QGroupBox('Save')
        self.save_group.setAlignment(Qt.AlignTop)
        self.save_form = QGridLayout()
        self.save_group.setLayout(self.save_form)
        self._options_layout.addWidget(self.save_group)

        self._save_button = QPushButton()
        self._save_button.setText('Save panel')
        self.save_form.addWidget(self._save_button, 0,0,1,2, Qt.AlignTop)

        # label font size
        self.save_form.addWidget(QLabel('Save dpi'), 1 ,0, Qt.AlignTop)
        self._save_dpi = QSpinBox()
        self._save_dpi.setRange(1,2000)
        self._save_dpi.setValue(300)
        self.save_form.addWidget(self._save_dpi, 1, 1, Qt.AlignTop)

        # initialize preview controls
        self._show_preview = QPushButton()
        self._show_preview.setText('Show preview')
        self._main_layout.addWidget(self._show_preview)

        # add image as layer
        self.btn_add_image_as_layer = QPushButton()
        self.btn_add_image_as_layer.setText('Add single image as layer')
        self._main_layout.addWidget(self.btn_add_image_as_layer)

        # add callbacks for widgets 
        self._add_callbacks()

    def _initialize_panel_grid_control(self, layout):
        """Create controls for grid size"""
        
        self.numrows = QSpinBox()
        self.numrows.setValue(1)
        self.numcolumns = QSpinBox()
        self.numcolumns.setValue(1)
        sizes_group = QGroupBox('Sizes')
        sizes_form = QGridLayout()
        sizes_form.addWidget(QLabel('Rows'), 0,0)
        sizes_form.addWidget(QLabel('Columns'), 1,0)
        sizes_form.addWidget(self.numrows,0,1)
        sizes_form.addWidget(self.numcolumns,1,1)

        sizes_group.setLayout(sizes_form)
        layout.addWidget(sizes_group)

    def _color_dialog(self):
        """Create color dialog for labels"""
        self._label_color = QColorDialog()
        self._label_color.setOption(QColorDialog.DontUseNativeDialog, True)
        self._label_color.setCurrentColor(QColor(255,255,255))
        self._label_color.colorSelected.connect(self._on_add_label)

    def _open_color_dialog(self):
        """Show label color dialog"""
        
        self._label_color.show()

    def _add_callbacks(self):
        """Add callbacks for all widgets"""

        self.panelElementListControlWidget.deleteButton.clicked.connect(
            self._delete_panelitem_callback
        )
        self.panelElementListControlWidget.captureButton.clicked.connect(
            self._capture_panel_item_callback
        )
        self.numcolumns.valueChanged.connect(self._change_number_rows_cols)
        self.numrows.valueChanged.connect(self._change_number_rows_cols)

        panelitem_list = self.napari_panel.key_frames
        panelitem_list.events.inserted.connect(self._on_panelitems_changed)
        panelitem_list.events.removed.connect(self._on_panelitems_changed)
        panelitem_list.events.changed.connect(self._on_panelitems_changed)
        panelitem_list.events.moved.connect(self._on_panelitems_moved)
        panelitem_list.selection.events.active.connect(
            self._on_active_panelitem_changed
        )

        #self._label_checkbox.clicked.connect(self._on_add_label)
        self._label_checkbox.stateChanged.connect(self._on_add_label)
        self._label_size.valueChanged.connect(self._on_add_label)

        self._channellabel_size.valueChanged.connect(self.reinitialize)

        self._save_button.clicked.connect(self.save_panel)

        self._check_channel_labels.stateChanged.connect(self.reinitialize)
        self._show_preview.clicked.connect(self.show_preview)

        self.btn_add_image_as_layer.clicked.connect(self.add_image_as_layer)

    def _on_active_panelitem_changed(self, event):
        """Callback on change of active panelitem in the key frames list."""
        active_panelitem = event.value
        self.panelElementListControlWidget.deleteButton.setEnabled(
            bool(active_panelitem)
        )
        self.napari_panel.set_to_panelitem(self.PanelItemListWidget.currentIndex().row())

    def _delete_panelitem_callback(self, event=None):
        """Delete current key-frame"""
        if self.napari_panel.key_frames.selection.active:
            self.napari_panel.key_frames.remove_selected()
        else:
            raise ValueError("No selected panelitem to delete !")

    def _on_panelitems_changed(self, event=None):

        has_frames = bool(self.napari_panel.key_frames)

        self.PanelItemListWidget.setEnabled(has_frames)
    
    def _on_panelitems_moved(self, event=None):
        """Reconstruct panel object with existing snapshots."""
        for panelitem_index, key_frame in enumerate(self.napari_panel.key_frames):
            #self.napari_panel.update_viewer(panelitem_index)
            self.add_snapshot_to_panel(panelitem_index, reuse_snapshot=True)
            pos_row, pos_col = self.linear_to_pos_col(panelitem_index)
            key_frame.name = f"Panel elem. [{pos_row}, {pos_col}]"

        self.update_preview()

    def _capture_panel_item_callback(self):
        """Callback on capture button. Captures both panelitem and snapshot."""

        current_pos = self.PanelItemListWidget.currentIndex().row()
        self.add_snapshot_to_panel(current_pos)

        pos_row, pos_col = self.linear_to_pos_col(current_pos)
        self.napari_panel.capture_panelitem(insert=False, pos_panel=[pos_row, pos_col])
        
        self.reinitialize()
        self.update_preview()

    def _init_panel(self):
        """Initialize panel with snapshots of key-frames."""

        self.panel = microfilm.microplot.Micropanel(
            self.numrows.value(), self.numcolumns.value())
        
        self.napari_panel.key_frames.clear()
        for i in range(self.numrows.value() * self.numcolumns.value()):
            pos_row, pos_col = self.linear_to_pos_col(i)
            self.viewer.reset_view()
            self.napari_panel.capture_panelitem(pos_panel=[pos_row, pos_col])

        self.update_preview()

    def reinitialize(self):
        """Recreate the panel with existing snapshots and annotations. Used to 
        update changes to labels."""

        self.panel.fig.clear()
        self.panel = microfilm.microplot.Micropanel(
            self.numrows.value(), self.numcolumns.value())

        for i in range(self.numrows.value() * self.numcolumns.value()):
            pos_row, pos_col = self.linear_to_pos_col(i)
            self.add_snapshot_to_panel(i, reuse_snapshot=True)

        self._on_add_label()
        self._on_show_channel_labels()

    def add_snapshot_to_panel(self, pos_index, reuse_snapshot=False):
        """Capture a snaphot of key-frame at index pos_index and add it to panel"""
        
        pos_row, pos_col = self.linear_to_pos_col(pos_index)

        if reuse_snapshot:
            sshot = np.rollaxis(self.napari_panel.key_frames[pos_index].snapshot[:,:,0:3],2, 0)
        else:
            sshot = np.rollaxis(self.viewer.screenshot()[:,:,0:3],2, 0)
        if self.panel:
            self.panel.add_element(
                pos=[pos_row, pos_col], 
                microim = microfilm.microplot.microshow(sshot,
                ax=self.panel.ax[pos_row,pos_col], 
                cmaps=['pure_red', 'pure_green', 'pure_blue'])
            )

    def _change_number_rows_cols(self, value):
        """Change number of rows and columns of panel. Re-use existing panelitems."""

        old_num = len(self.napari_panel.key_frames)
        new_num = self.numrows.value() * self.numcolumns.value()
        self.panel = microfilm.microplot.Micropanel(
            self.numrows.value(), self.numcolumns.value())
        if new_num < old_num:
            for i in range(old_num, new_num, -1):
                self.napari_panel.key_frames.remove(self.napari_panel.key_frames[i-1])
        for i in range(self.numrows.value() * self.numcolumns.value()):
            pos_row, pos_col = self.linear_to_pos_col(i)
            if i<old_num:
                self.add_snapshot_to_panel(i, reuse_snapshot=True)
            else:
                self.viewer.reset_view()
                self.napari_panel.capture_panelitem(position=i, pos_panel=[pos_row, pos_col])
        self._on_add_label()
        self._on_show_channel_labels()
        self.update_preview()

    def update_preview(self):
        """Update the preview"""

        self.panel.savefig('temp.png')
        self.pixmap = QPixmap('temp.png')
        self.pixlabel.setPixmap(self.pixmap.scaledToWidth(self.pixlabel.size().width()))
        if self.pixlabel.isVisible():
            self.show_preview()

    def _on_resize_preview(self, event):
        """Adjust the image size to fit to the widget size."""

        self.pixmap = QPixmap('temp.png')
        self.pixlabel.setPixmap(self.pixmap.scaledToWidth(self.pixlabel.size().width()))

    def show_preview(self):
        """Display preview."""
        
        #self.reinitialize()
        self.pixlabel.show()
        
    def _init_panel_items_widget(self, layout):
        """Initialize panel items"""

        self.PanelItemListWidget = PanelItemListWidget(
            root=self.napari_panel.key_frames, parent=self
        )
        layout.addWidget(self.PanelItemListWidget)
        
        self._init_panel()

    def _on_add_label(self):
        """Callback to add labels to each element of panel."""

        # Use custom label if provided otherwise use default label A, B, C, ...
        if self._label_custom.text() == "":
            labels = string.ascii_uppercase
        else:
            labels = self._label_custom.text().strip().split(',')
            diff_lab = len(self.panel.microplots.flatten()) - len(labels)
            if diff_lab > 0:
                labels += diff_lab *'X'

        # Go through each element, remove existing text and add label
        for ind, m in enumerate(self.panel.microplots.flatten()):
            if m is not None:
                if len(m.ax.texts) > 0:
                    m.ax.texts.clear()
                if self._label_checkbox.isChecked():
                    m.add_label(
                        label_text=labels[ind],
                        label_font_size=self._label_size.value(),
                        label_color=[x/255 for x in self._label_color.currentColor().getRgb()])
        self.update_preview()

    def _on_show_channel_labels(self):
        """Display channel names as panel elements title. Unused"""

        # visibility is initalized as bool by napari, but then changes to
        # integers (probabl a bug). We ensure here it is always int
        for x in self.viewer.layers:
            if type(x.visible) == bool:
                x.visible = int(x.visible)

        #self._on_panelitems_moved()
        #self.reinitialize()
        if self._check_channel_labels.isChecked():

            visible_layers = [[None for j in range(self.numcolumns.value())] for i in range(self.numrows.value())]
            layer_colors = [[None for j in range(self.numcolumns.value())] for i in range(self.numrows.value())]
            for i in range(self.numrows.value() * self.numcolumns.value()):
                pos_row, pos_col = self.linear_to_pos_col(i)
                
                cur_layer = self.napari_panel.key_frames[i].viewer_state.layers
                visible_layers[pos_row][pos_col] = [cur_layer[x]['name'] for x in cur_layer if cur_layer[x]['visible'] > 0]
                layer_colors[pos_row][pos_col] = [self.viewer.layers[x].colormap.colors[-1] for x in visible_layers[pos_row][pos_col]]

            self.panel.add_channel_label(
                channel_names=visible_layers, channel_label_size=self._channellabel_size.value()/100,
                channel_colors=layer_colors)
        self.update_preview()

    def save_panel(self):
        """Save panel to file."""
        
        self.select_file, _ = QFileDialog.getSaveFileName(self, "Save Panel", "", "*.png")
        self.panel.savefig(self.select_file, dpi=self._save_dpi.value())

    def linear_to_pos_col(self, pos_index):
        """Compute row, col from linear index"""

        (pos_row, pos_col) = np.unravel_index(pos_index, shape=(self.numrows.value(), self.numcolumns.value()))
        return pos_row, pos_col
    
    def add_image_as_layer(self, event=None):
        
        rgb_image = [x.data for x in self.viewer.layers if x.visible]
        contrasts = [np.array(x.contrast_limits).tolist() for x in self.viewer.layers if x.visible]

        cmaps = [Colormap(x.colormap.colors).to_matplotlib() for x in self.viewer.layers if x.visible]

        if self.viewer.dims.ndim == 3:
            rgb_sequence = []
            for ind in range(rgb_image[0].shape[0]):
                rgb_to_plot = np.stack([x[ind] for x in rgb_image], axis=0)
                rgb_to_plot, _, _, _ = colorify.multichannel_to_rgb(
                    rgb_to_plot,
                    cmaps=cmaps,
                    rescale_type='limits', 
                    limits=contrasts,
                    proj_type='sum')
                rgb_sequence.append(rgb_to_plot)
            rgb_sequence = np.stack(rgb_sequence, axis=0)
        elif self.viewer.dims.ndim == 2:
            rgb_sequence, _, _, _ = colorify.multichannel_to_rgb(
                rgb_image,
                cmaps=cmaps,
                rescale_type='limits', 
                limits=contrasts,
                proj_type='sum')
        else:
            raise ValueError(f'Viewer dimension {self.viewer.dims.ndim} not supported')

        self.viewer.add_image(rgb_sequence)
