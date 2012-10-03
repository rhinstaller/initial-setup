import gui

class O(object):
    pass

g = gui.FirstbootGraphicalUserInterface(None, None, None)
data = O()
g.setup(data)
g.run()

