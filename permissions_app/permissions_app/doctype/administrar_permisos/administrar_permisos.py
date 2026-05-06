import frappe
import json
from frappe.model.document import Document

class AdministrarPermisos(Document):
    def on_update(self):
        if not self.rol_principal:
            frappe.throw("Por favor, seleccione un Rol Principal.")

        # 1. Actualizar permisos manuales (Tabla superior)
        self._actualizar_permisos_principales()
        
        # 2. Heredar dependencias y asignar permisos de Reportes
        agregados = self._heredar_y_blindar_permisos()
        
        frappe.db.commit()
        frappe.clear_cache()
        
        msg = f"Sincronización exitosa para <b>{self.rol_principal}</b>."
        if agregados:
            msg += f"<br>Se habilitaron <b>{len(agregados)}</b> dependencias y sus reportes asociados."
        
        frappe.msgprint(msg)

    def _actualizar_permisos_principales(self):
        for row in self.lista_de_permisos:
            if not row.tipo_de_documento: continue
            
            # Otorgamos Report y Print por defecto para evitar errores de Desk
            perm_data = {
                "read": int(row.get("leer") or 0),
                "write": int(row.get("escribir") or 0),
                "create": int(row.get("crear") or 0),
                "delete": int(row.get("eliminar") or 0),
                "select": int(row.get("seleccionar") or 0),
                "report": 1, 
                "print": 1,
                "email": 1,
                "export": int(row.get("exportar") or 0),
                "import": int(row.get("importar__exportar") or 0),
                "share": int(row.get("compartir") or 0)
            }
            self._aplicar_permiso_bd(row.tipo_de_documento, perm_data)
            self._asignar_rol_a_reportes(row.tipo_de_documento)

    def _heredar_y_blindar_permisos(self):
        """Busca dependencias, les da permiso de lectura/reporte y habilita sus informes."""
        doctypes_en_tabla = [row.tipo_de_documento for row in self.lista_de_permisos if row.tipo_de_documento]
        if not doctypes_en_tabla: return []

        # Obtener todos los enlaces
        links = frappe.get_all("DocField", 
            filters={"parent": ["in", doctypes_en_tabla], "fieldtype": ["in", ["Link", "Table"]]},
            fields=["options"])
        
        custom_links = frappe.get_all("Custom Field",
            filters={"dt": ["in", doctypes_en_tabla], "fieldtype": ["in", ["Link", "Table"]]},
            fields=["options as options"])
        
        todos_los_links = links + custom_links
        dependencias = {l.options for l in todos_los_links if l.options}
        
        # Forzar maestros críticos de ERPNext
        dependencias.update(["Cost Center", "Company", "Account", "Purchase Invoice", "Sales Invoice"])

        agregados = []
        for dt in dependencias:
            if dt in doctypes_en_tabla or dt in ["User", "Role", "DocType"]: continue
            
            if frappe.db.exists("DocType", dt):
                if not frappe.db.exists("Custom DocPerm", {"parent": dt, "role": self.rol_principal}):
                    # PERMISO OPERATIVO COMPLETO
                    self._aplicar_permiso_bd(dt, {
                        "read": 1, "select": 1, "report": 1, "print": 1, "email": 1
                    })
                    # HABILITAR REPORTES DEL DOCTYPE (Soluciona el error 403 de get_script)
                    self._asignar_rol_a_reportes(dt)
                    agregados.append(dt)
        return agregados
    
    def _asignar_rol_a_reportes(self, doctype_name):
        """
        Busca todos los Reportes vinculados al DocType y les asigna el Rol.
        Usamos db_insert para evitar validaciones de enlaces rotos (como Membretes inexistentes).
        """
        reportes = frappe.get_all("Report", filters={"ref_doctype": doctype_name}, fields=["name"])
        
        for r in reportes:
            # Verificar si el rol ya está asignado al reporte en la tabla 'tabHas Role'
            existe = frappe.db.exists("Has Role", {
                "parent": r.name, 
                "role": self.rol_principal,
                "parenttype": "Report"
            })
            
            if not existe:
                # Insertamos directamente en la base de datos para saltar validaciones de Letter Head/Membrete
                doc_has_role = frappe.get_doc({
                    "doctype": "Has Role",
                    "parent": r.name,
                    "parentfield": "roles",
                    "parenttype": "Report",
                    "role": self.rol_principal
                })
                doc_has_role.db_insert()

    def _aplicar_permiso_bd(self, doctype_name, perm_values):
        name_perm = frappe.db.get_value("Custom DocPerm", {"parent": doctype_name, "role": self.rol_principal})
        if name_perm:
            frappe.db.set_value("Custom DocPerm", name_perm, perm_values)
        else:
            new_perm = frappe.new_doc("Custom DocPerm")
            new_perm.update({"parent": doctype_name, "role": self.rol_principal, 
                             "parenttype": "DocType", "parentfield": "permissions", "permlevel": 0})
            new_perm.update(perm_values)
            new_perm.insert(ignore_permissions=True)

# --- Funciones Whitelisted ---

@frappe.whitelist()
def get_permisos_por_documento(role):
    # En v13 usamos comillas simples para la palabra reservada import
    fields = ["parent", "read", "write", "create", "delete", "select", "print", "email", "report", "export", "`import`", "share"]
    res = frappe.get_all('Custom DocPerm', filters={"role": role}, fields=fields)
    return [{
        "tipo_de_documento": p.parent,
        "leer": p.read, "escribir": p.write, "crear": p.create, "eliminar": p.delete,
        "seleccionar": p.select, "impresion": p.print, "correo_electronico": p.email,
        "reporte": p.report, "exportar": p.export, "importar__exportar": getattr(p, 'import'), "compartir": p.share
    } for p in res]

@frappe.whitelist()
def get_doctypes_faltantes(doctypes):
    """
    Analiza una lista de DocTypes y devuelve todos sus enlaces (Link/Table)
    que NO están presentes en la lista actual.
    """
    if isinstance(doctypes, str):
        doctypes = json.loads(doctypes)
    
    faltantes = []
    vistos = set()
    
    # 1. Buscar en campos estándar (DocField)
    links_std = frappe.get_all("DocField", 
        filters={
            "parent": ["in", doctypes], 
            "fieldtype": ["in", ["Link", "Table"]]
        },
        fields=["parent as doctype_origen", "options as tipo_documento", "label", "fieldname"]
    )

    # 2. Buscar en campos personalizados (Custom Field)
    links_custom = frappe.get_all("Custom Field",
        filters={
            "dt": ["in", doctypes],
            "fieldtype": ["in", ["Link", "Table"]]
        },
        fields=["dt as doctype_origen", "options as tipo_documento", "label", "fieldname"]
    )

    todos_los_enlaces = links_std + links_custom
    
    for link in todos_los_enlaces:
        destino = link.tipo_documento
        # Solo procesar si el destino existe, no está en la lista actual y no es del sistema
        if (destino and 
            destino not in doctypes and 
            destino not in vistos and 
            destino not in ["User", "Role", "DocType", "File"]):
            
            if frappe.db.exists("DocType", destino):
                vistos.add(destino)
                faltantes.append({
                    "doctype_origen": link.doctype_origen,
                    "tipo_documento": destino,
                    "campo": link.label or link.fieldname
                })
                
    return sorted(faltantes, key=lambda x: x["tipo_documento"])