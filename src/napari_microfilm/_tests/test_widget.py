import numpy as np
from napari_microfilm import MicrofilmWidget


# make_napari_viewer is a pytest fixture that returns a napari viewer object
# capsys is a pytest fixture that captures stdout and stderr output streams
def test_example_q_widget(make_napari_viewer, capsys):
    # make viewer and add an image layer using our fixture
    viewer = make_napari_viewer()
    viewer.add_image(np.random.random((3, 100, 100)), channel_axis=0)

    # create our widget, passing in the viewer
    my_widget = MicrofilmWidget(viewer)

    # call our widget method
    my_widget.add_image_as_layer()

    # read captured output and check that it's as we expected
    assert 'rgb_sequence' in viewer.layers