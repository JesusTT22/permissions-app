# Copyright (c) 2026, Jesus T. and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document


class AdministrarPermisos(Document):
    pass


@frappe.whitelist()
def get_permisos_por_documento(role: str) -> list[dict]:
    """
    Obtiene los DocTypes a los que el rol tiene acceso,
    junto con sus permisos (leer, escribir, crear, etc.).
    Los permisos Custom sobreescriben a los estándar.
    """
    if not role:
        return []

    try:
        standard = frappe.get_all(
            'DocPerm',
            filters={"role": role},
            fields=[
                "parent", "read", "write", "create",
                "delete", "select", "print", "email"
            ],
        )
        custom = frappe.get_all(
            'Custom DocPerm',
            filters={"role": role},
            fields=[
                "parent", "read", "write", "create",
                "delete", "select", "print", "email"
            ],
        )

        result = {}
        for perm in standard:
            result[perm.parent] = perm
        for perm in custom:
            result[perm.parent] = perm

        return [
            {
                "tipo_documento": doctype,
                "leer":        int(perm.read   or 0),
                "escribir":    int(perm.write  or 0),
                "crear":       int(perm.create or 0),
                "eliminar":    int(perm.delete or 0),
                "seleccionar": int(perm.select or 0),
                "impresion":   int(perm.print  or 0),
                "correo":      int(perm.email  or 0),
            }
            for doctype, perm in sorted(result.items())
        ]

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Error en get_permisos_por_documento")
        return []


@frappe.whitelist()
def get_doctypes_faltantes(doctypes: str) -> list[dict]:
    """
    Dado una lista JSON de DocTypes que el rol YA TIENE,
    detecta qué otros DocTypes son necesarios (referenciados
    via campos Link) pero que el rol AÚN NO TIENE.

    Estos son los que causan problemas de permisos:
    el doctype existe en el rol pero necesita leer/acceder
    a otro doctype para el que el rol no tiene permiso.
    """
    import json

    if not doctypes:
        return []

    try:
        name_doctype = json.loads(doctypes)
        if not name_doctype:
            return []

        campos_excluidos = [
            'amended_from', 'owner', 'modified_by',
            'parenttype', 'creation', 'docstatus'
        ]

        # Buscar todos los campos Link de los doctypes del rol
        # para saber qué otros doctypes referencian
        todos_links = frappe.get_all(
            'DocField',
            filters={
                "parent": ["in", name_doctype],
                "fieldtype": "Link",
                "fieldname": ["not in", campos_excluidos]
            },
            fields=["parent", "label", "fieldname", "options"],
        )

        # Detectar cuáles de esos destinos NO están en la lista del rol
        faltantes = []
        vistos = []

        for doc in todos_links:
            destino = doc.options
            # Si el destino no está en los doctypes del rol y no lo hemos visto
            if destino not in name_doctype and destino not in vistos:
                vistos.append(destino)
                faltantes.append({
                    "tipo_documento":   destino,
                    "requerido_por":    doc.parent,
                    "campo":            doc.label or doc.fieldname,
                    "tipo_permiso":     doc.parent + " -> " + destino,
                    "doctype_origen":   doc.parent,
                    "doctype_destino":  destino,
                })

        return sorted(faltantes, key=lambda x: x["tipo_documento"])

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Error en get_doctypes_faltantes")
        return []

def update_links_faltantes(todos_links):

	try:
		# Obtener la función todos los links
		if not todos_links:
			return []

		# Actualizar 
		update_link = frappe.get_doc('DocField',
			filters={
				"parent": ["in", todos_links],
				"fieldtype": "Link",
			},
			fields=["parent", "fieldtype"]
		)

		return update_link
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error en update_links_faltantes")