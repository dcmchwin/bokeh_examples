"""App to demo streaming plus JS interaction.

A sine wave with random noise is streamed from the server.
Callbacks on the client side allow:
    - User to pause/unpause the streaming
    - User variation of signal amplitude
    - User variation of streaming speed

To run the application, type the following from the "server" dir:
    $ bokeh serve server_sandbox
The application will stream on localhost:5006 by default.
"""

from bokeh.events import ButtonClick
from bokeh.io import curdoc
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Button, Slider
from bokeh.plotting import figure
import logging
import numpy as np

# SET UP LOGGER
# -------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# BOKEH STUFF
# -----------

def _init_param_source():
    """Get parameters as a ColumnDataSource object.

    Collecting parameters like this is a bit of a hack to enable
    dynamic updating of parameters from the bokeh client."""

    amp_sine = 1
    amp_rand = 1
    rollover = 100 # length of data to display
    update_delay = 100 # time between delays of update in ms
    param_source = ColumnDataSource(dict(
        amp_sine=[amp_sine],
        amp_rand=[amp_rand],
        rollover=[rollover],
        update_delay=[update_delay]
        ))
    return param_source


def _init_data_source():
    """Initialise the data to stream."""

    x = np.array([1])
    y = np.sin(x)
    avg = np.cumsum(y) / np.arange(1.0, len(y) + 1.0)
    data_source = ColumnDataSource(dict(x=x, y=y, avg=avg))
    return data_source


def _get_new_avg(source, y_n1, rollover):
    """Get new value of rolling average.

    This approach minimises the number of calculations required.
    """
    avg_n0 = source.data['avg'][-1]
    y_0 = source.data['y'][0]
    N0 = len(source.data['x'])
    if N0 < rollover:
        N1 = N0 + 1
        dy = y_n1
    else:
        N1 = N0
        dy = y_n1 - y_0
    avg_n1 = (N0 / N1) * avg_n0 + dy / N1

    return avg_n1 


def update():
    """Update the data to display."""

    # Get last new x value as last x value + 1
    x_n0 = data_source.data['x'][-1]
    x_n1 = x_n0 + 0.1

    # Assign a new y value
    y_n1 = param_source.data['amp_sine'][0] * np.sin(x_n1) +\
           param_source.data['amp_rand'][0] * np.random.rand(1)

    # Get old last average and use to calculate new average
    avg_n1 = _get_new_avg(data_source,
                          y_n1,
                          param_source.data['rollover'][0])

    # Make a dict of data to add on to the end of the source
    additional_data = dict(x=[x_n1], y=[y_n1], avg=[avg_n1])

    # Stream the new data with a rollover value of 10
    data_source.stream(additional_data,
                       rollover=param_source.data['rollover'][0])

    # logger.debug(param_source.data['update_delay'][0])


def pause():
    """Pause/unpause the graph."""

    if any(cb.callback.__name__ == update.__name__ for
           cb in curdoc().session_callbacks):
        curdoc().remove_periodic_callback(update)
    else:
        curdoc().add_periodic_callback(
            update,
            param_source.data['update_delay'][0])

# Set up param_source
param_source = _init_param_source()

# Set up data source
data_source = _init_data_source()

# Set up figure
fig = figure()
fig.line(source=data_source, x='x', y='y')
fig.line(source=data_source, x='x', y='avg', line_color="red")

# Set up pause button
btn = Button(label='Pause')
btn.on_click(pause)

# Set up slider to change update speed
def _change_update_delay(attr, old, new):
    logger.debug('Slider has been moved, new {}: {}'.format(attr, new))
    param_source.data['update_delay'][0] = new
    curdoc().remove_periodic_callback(update)
    curdoc().add_periodic_callback(update,
                                   param_source.data['update_delay'][0])

delay_slider = Slider(start=10, end=100, value=50, step=10,
                      title='Streaming Delay')
delay_slider.on_change('value', _change_update_delay)

# Set up sider to change amplitude of sine wave
def _change_amp_sine(attr, old, new):
    logger.debug('Slider has been moved, new {}: {}'.format(attr, new))
    param_source.data['amp_sine'][0] = new

amp_sine_slider = Slider(start=0.1, end=2, value=1, step=0.1,
                         title='Sinusoid Amplitude')
amp_sine_slider.on_change('value', _change_amp_sine)

# Set up sider to change amplitude of random part of data
def _change_amp_rand(attr, old, new):
    logger.debug('Slider has been moved, new {}: {}'.format(attr, new))
    param_source.data['amp_rand'][0] = new

amp_rand_slider = Slider(start=0.1, end=2, value=1, step=0.1,
                         title='Random Amplitude')
amp_rand_slider.on_change('value', _change_amp_rand)

# Add figure, pause button and sliders to the document
curdoc().add_periodic_callback(update,
                               param_source.data['update_delay'][0])

curdoc().add_root(column(delay_slider, amp_sine_slider, amp_rand_slider,
                         btn, fig))