import io
from pymongo import MongoClient
from matplotlib import pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from flask import Response, Flask

app = Flask(__name__)
app.debug = True



client = MongoClient()

wall = client.green_wall.description.find_one({"@type":"green_wall", "name":"IMT Lobby"})

print (wall)

w_dimension = wall["dimension"]

print ("Wall dimension", w_dimension)


def create_figure():
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    res = client.green_wall.description.aggregate([
                {"$match":  { "$and" : [
                                {"@type": "humidity_loc"},
                                {"wall" : wall["_id"]}
                                ]
                             }
                },

                {"$group" : {
                     "_id": None,
                     "count": {"$sum": 1},
                     "coordinates": {"$push": "$position"},
                            }
                 }
           ])

    for r in res:
        print (r)
        data = np.array(r["coordinates"])

        x, y = data.T

        axis.scatter(x, y)
        return fig

@app.route('/plot.png')
def plot_png():
    fig = create_figure()
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

    
app.run(host="0.0.0.0", port=8080)
