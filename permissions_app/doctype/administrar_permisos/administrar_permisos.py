# Copyright (c) 2026, Jesus T. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class AdministrarPermisos(Document):
	pass

	@frappe.whitelist()
	def get_documentos_rol(rol):

		# Validar si se obtuvo el ID del rol.
		if not rol:
			return []

		# Obtener el tipo de documento del rol.
		document = frappe.get_all('Custom DocPerm', filters={
			"role": rol,
			"read": 1,
		}, fields=["parent"])

		clean_list = list(set([d.doctype_name for d in document]))

		return [{"tipo_documento": doc} for doc in clean_list]