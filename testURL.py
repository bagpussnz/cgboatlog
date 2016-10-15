from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.network.urlrequest import UrlRequest

class Example(FloatLayout):
    def __init__(self, **kwargs):
        super(Example, self).__init__(**kwargs)

    def on_success(req, result, *args):
        print result

    def on_prog(req, result, *args):
        print result

    # headers = {
		# 		'Authorization': 'Basic ' + ('%s:%s' % (
		# 		'admin', '1234')).encode('base-64'),
		# 		'Accept': '*/*',
		# 		}

    UrlRequest('http://www.linz.govt.nz/sites/default/files/docs/hydro/tidal-info/tide-tables/maj-ports/csv/Auckland%202016.csv',
               on_success=on_success, on_progress=on_prog)

class Demo(App):
	def build(self):
		return Example()

if __name__ == '__main__':
    Demo().run()