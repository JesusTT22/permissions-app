import frappe

def heredar_al_insertar(doc, method):
    """
    Esta función se ejecuta automáticamente después de insertar un nuevo Rol.
    'doc' es el objeto del Rol que se acaba de crear.
    """
    # Obtener el nombre del Rol Padre desde el campo creado
    role_parent = doc.parent_role
    
    # Si el usuario no seleccionó un padre, se detiene la ejecución
    if not role_parent:
        return

    # Definir los campos de permisos que se quiere copiar. 
    fields = ["parent", "permlevel", "read", "write", "create", "delete", 
              "submit", "cancel", "amend", "report", "export", "import", 
              "print", "email", "share"]

    # Primero buscamos si el padre tiene permisos personalizados (Custom DocPerm)
    custom_perms = frappe.get_all("Custom DocPerm", filters={"role": role_parent}, fields=fields)

    # Si no tiene personalizados, buscamos los permisos estándar del sistema (DocPerm)
    if not custom_perms:
        custom_perms = frappe.get_all("DocPerm", filters={"role": role_parent}, fields=fields)

    # Empezar a recorrer cada permiso encontrado del padre
    for perm in custom_perms:
        doctype_nombre = perm.get("parent") # El DocType al que pertenece el permiso
        if not doctype_nombre: continue

        # Verificar si este permiso ya existe para el nuevo rol (para evitar errores de duplicidad)
        existe = frappe.db.exists("Custom DocPerm", {
            "parent": doctype_nombre, 
            "role": doc.name, 
            "permlevel": perm.get("permlevel", 0)
        })

        if not existe:
            # Si no existe, creamos el nuevo registro de permiso
            new_perm = frappe.get_doc({
                "doctype": "Custom DocPerm",
                "parent": doctype_nombre,
                "parenttype": "DocType",
                "parentfield": "permissions",
                "role": doc.name,
                # Esta línea de abajo copia todos los valores de 'perm' (read, write, etc.) 
                # excepto el nombre original y el padre para que no choquen
                **{k: v for k, v in perm.items() if k not in ['parent', 'name']}
            })
            # Insertar el permiso ignorando restricciones de sistema
            new_perm.insert(ignore_permissions=True)