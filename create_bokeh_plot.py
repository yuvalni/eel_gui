from bokeh.models import ColumnDataSource
from bokeh.embed import components
from bokeh.plotting import figure, show

source = ColumnDataSource(data=dict(T=[0],R=[0]),name='RT_data')

p = figure(title="Resistance vs. Temperature")
p.circle('T', 'R', source=source)

script, div = components(p)
with open('bokeh_embed.html','w') as file:
    file.write(script)
    file.write(div)
