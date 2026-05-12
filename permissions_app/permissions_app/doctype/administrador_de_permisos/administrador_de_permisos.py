import frappe
import json
from frappe.model.document import Document
from frappe.cache_manager import clear_user_cache
from frappe.core.page.permission_manager.permission_manager import setup_custom_perms

class AdministradordePermisos(Document):
    def on_update(self):
        if not self.rol_principal:
            frappe.throw("Por favor, seleccione un Rol Principal.")

        # 1. Actualizar permisos de la tabla manual
        self._actualizar_permisos_principales()
        
        # 2. Heredar dependencias (La "Vacuna" con Fiscal Year incluido)
        agregados = self._heredar_y_blindar_permisos()
        
        # 3. LIMPIEZA ABSOLUTA DE CACHÉ
        frappe.db.commit()
        frappe.clear_cache()
        clear_user_cache()
        
        frappe.cache().delete_value("role_permissions")
        frappe.cache().delete_value("has_role")
        frappe.cache().delete_value("bootinfo")
        
        # --- MENSAJE DE ÉXITO ---
        msg = f"Sincronización exitosa para <b>{self.rol_principal}</b>. "
        msg += f"Se habilitaron <b>{len(agregados)}</b> permisos adicionales para garantizar un acceso sin bloqueos."
        
        frappe.msgprint(msg, alert=True)

    def _actualizar_permisos_principales(self):
        for row in self.lista_de_permisos:
            if not row.tipo_de_documento: continue
            
            perm_data = {
                "read": int(row.get("leer") or 0),
                "write": int(row.get("escribir") or 0),
                "create": int(row.get("crear") or 0),
                "delete": int(row.get("eliminar") or 0),
                "select": 1, # Crítico para que funcionen los campos Link
                "report": 1, # Crítico para que funcionen los Dashboards
                "print": 1,
                "email": 1,
                "export": int(row.get("exportar") or 0),
                "import": int(row.get("importar__exportar") or 0),
                "share": int(row.get("compartir") or 0)
            }
            self._aplicar_permiso_bd(row.tipo_de_documento, perm_data)
            self._asignar_rol_a_reportes(row.tipo_de_documento)

    def _heredar_y_blindar_permisos(self):
        doctypes_en_tabla = [row.tipo_de_documento for row in self.lista_de_permisos if row.tipo_de_documento]
        if not doctypes_en_tabla: return []

        # Obtener dependencias de campos Link y Tablas
        links = frappe.get_all("DocField", 
            filters={"parent": ["in", doctypes_en_tabla], "fieldtype": ["in", ["Link", "Table", "Dynamic Link"]]},
            fields=["options"])
        
        custom_links = frappe.get_all("Custom Field",
            filters={"dt": ["in", doctypes_en_tabla], "fieldtype": ["in", ["Link", "Table", "Dynamic Link"]]},
            fields=["options as options"])
        
        dependencias = {l.options for l in (links + custom_links) if l.options}
        
        # Lista maestra de documentos que ERPNext consulta en background (Dashboards/Leaderboards)
        maestros_criticos = [
            "Company", "Cost Center", "Account", "Currency", "Warehouse", "Item",
            "Customer", "Supplier", "Contact", "Address", "Employee",
            "Sales Order", "Sales Invoice", "Delivery Note", "Quotation",
            "Purchase Order", "Purchase Invoice", "Material Request", "Stock Entry",
            "Payment Entry", "Journal Entry", "Tax Rule", "Pricing Rule", "Project",
            "Fiscal Year", "Fiscal Year Company", "Accounting Period" # <--- ¡Nuevos blindajes!
        ]
        dependencias.update(maestros_criticos)

        agregados = []
        for dt in dependencias:
            if dt in doctypes_en_tabla or dt in ["User", "Role", "DocType", "Print Format", "Workspace"]: 
                continue
            
            if dt and frappe.db.exists("DocType", dt):
                # VERIFICACIÓN EXTRA: Solo aplicar permisos a documentos reales, no a tablas hijas (Child Tables)
                if not frappe.db.get_value("DocType", dt, "istable"):
                    # Permisos mínimos de lectura/reporte para evitar el 403
                    self._aplicar_permiso_bd(dt, {
                        "read": 1, "select": 1, "report": 1, "print": 1, "email": 1
                    })
                    self._asignar_rol_a_reportes(dt)
                    agregados.append(dt)
                
        return agregados

    def _aplicar_permiso_bd(self, doctype_name, perm_values):
        """Asigna permisos. Maneja la diferencia entre DocPerm y Custom DocPerm."""
        is_custom = frappe.db.get_value("DocType", doctype_name, "custom")
        perm_table = "DocPerm" if is_custom else "Custom DocPerm"
        
        # CLAVE: Si es estándar y no tiene Custom DocPerm, clonamos los originales.
        # Esto soluciona el error "Insufficient Permission" de Frappe
        if not is_custom and not frappe.db.exists("Custom DocPerm", {"parent": doctype_name}):
            try:
                setup_custom_perms(doctype_name)
            except Exception:
                pass
        
        filters = {"parent": doctype_name, "role": self.rol_principal, "permlevel": 0}
        name_perm = frappe.db.get_value(perm_table, filters)
        
        if name_perm:
            # USAMOS .save() en lugar de db.set_value para que Frappe limpie la caché
            doc_perm = frappe.get_doc(perm_table, name_perm)
            doc_perm.update(perm_values)
            doc_perm.save(ignore_permissions=True)
        else:
            new_perm = frappe.new_doc(perm_table)
            new_perm.update(filters)
            new_perm.update({
                "parenttype": "DocType", 
                "parentfield": "permissions"
            })
            new_perm.update(perm_values)
            new_perm.insert(ignore_permissions=True)
            
        # Forzar limpieza de caché para este doctype específico
        frappe.clear_cache(doctype=doctype_name)

    def _asignar_rol_a_reportes(self, doctype_name):
        reportes = frappe.get_all("Report", filters={"ref_doctype": doctype_name}, fields=["name"])
        for r in reportes:
            if not frappe.db.exists("Has Role", {"parent": r.name, "role": self.rol_principal}):
                doc_has_role = frappe.get_doc({
                    "doctype": "Has Role",
                    "parent": r.name,
                    "parentfield": "roles",
                    "parenttype": "Report",
                    "role": self.rol_principal
                })
                doc_has_role.db_insert()

# --- Funciones Whitelisted ---
@frappe.whitelist()
def get_permisos_por_documento(role):
    fields = ["parent", "read", "write", "create", "delete", "select", "print", "email", "report", "export", "`import`", "share"]
    
    # Consultamos ambas tablas para no perder registros custom
    res_custom = frappe.get_all('Custom DocPerm', filters={"role": role}, fields=fields)
    res_std = frappe.get_all('DocPerm', filters={"role": role}, fields=fields)
    
    permisos_dict = {p.parent: p for p in res_std}
    for p in res_custom:
        permisos_dict[p.parent] = p 
        
    return [{
        "tipo_de_documento": p.parent,
        "leer": p.read, "escribir": p.write, "crear": p.create, "eliminar": p.delete,
        "seleccionar": p.select, "impresion": p.print, "correo_electronico": p.email,
        "reporte": p.report, "exportar": p.export, "importar__exportar": getattr(p, 'import'), "compartir": p.share
    } for p in permisos_dict.values()]

@frappe.whitelist()
def get_doctypes_faltantes(doctypes):
    if isinstance(doctypes, str):
        doctypes = json.loads(doctypes)
    
    faltantes = []
    vistos = set()
    
    links_std = frappe.get_all("DocField", 
        filters={"parent": ["in", doctypes], "fieldtype": ["in", ["Link", "Table", "Dynamic Link"]]},
        fields=["parent as doctype_origen", "options as tipo_documento", "label", "fieldname"]
    )

    links_custom = frappe.get_all("Custom Field",
        filters={"dt": ["in", doctypes], "fieldtype": ["in", ["Link", "Table", "Dynamic Link"]]},
        fields=["dt as doctype_origen", "options as tipo_documento", "label", "fieldname"]
    )

    for link in (links_std + links_custom):
        destino = link.tipo_documento
        if destino and destino not in doctypes and destino not in vistos and destino not in ["User", "Role", "DocType", "File"]:
            if frappe.db.exists("DocType", destino):
                vistos.add(destino)
                faltantes.append({
                    "doctype_origen": link.doctype_origen,
                    "tipo_documento": destino,
                    "campo": link.label or link.fieldname
                })
                
    return sorted(faltantes, key=lambda x: x["tipo_documento"])