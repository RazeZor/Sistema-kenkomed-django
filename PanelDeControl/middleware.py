from django.utils.deprecation import MiddlewareMixin


class NoCacheMiddleware(MiddlewareMixin):
	"""Middleware para agregar cabeceras que deshabilitan el cache del navegador.

	Esto evita que, tras hacer logout (session.flush()), el usuario vea páginas protegidas
	desde la caché al pulsar el botón 'Atrás'.

	Añadir a MIDDLEWARE en settings.py: 'PanelDeControl.middleware.NoCacheMiddleware'
	"""

	def process_response(self, request, response):
		# Cabeceras HTTP para impedir cache en el navegador
		response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
		response['Pragma'] = 'no-cache'
		response['Expires'] = '0'
		return response

