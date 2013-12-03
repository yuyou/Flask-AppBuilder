from flask import current_app
from models import (User, Role, PermissionView, Permission, ViewMenu)
from functools import wraps


class SecurityManager(object):

    session = None
    auth_role_admin = ""

    def __init__(self, session, auth_role_admin):
        self.session = session
        self.auth_role_admin = auth_role_admin
  
  
    def has_access(f):
    """
        Use this decorator to allow access only to security 
        defined permissions
    """
    def wrap(self, *args, **kwargs):
        if current_user.is_authenticated():
            if g.user.has_permission_on_view("can_" + f.__name__, self.__class__.__name__):
                return f(self, *args, **kwargs)
            else:
                flash("Access is Denied %s %s" % (f.__name__, self.__class__.__name__),"danger")
        else:
            if is_item_public("can_" + f.__name__, self.__class__.__name__):
                return f(self, *args, **kwargs)
            else:
                flash("Access is Denied %s %s" % (f.__name__, self.__class__.__name__),"danger")
        return redirect(url_for("AuthView.login"))
    return wrap
    
  
    def is_menu_public(self, item):
        """
            Check if menu item has public permissions
    
            param item:
                menu item
        """
        role_public = current_app.config['AUTH_ROLE_PUBLIC']
        role = self.session.query(Role).filter_by(name = role_public).first()
        lst = role.permissions
        if lst:
            for i in lst:
                if item == i.view_menu.name:
                    return  True
            return False
        else: return False

    def is_item_public(self, permission_name, view_name):
        """
            Check if view has public permissions
    
            param permission_name:
                the permission: can_show, can_edit...
            param view_name:
                the name of the class view (child of BaseView)
        """
        role_public = current_app.config['AUTH_ROLE_PUBLIC']
        role = self.session.query(Role).filter_by(name = role_public).first()
        lst = role.permissions
        if lst:
            for i in lst:
                if (view_name == i.view_menu.name) and (permission_name == i.permission.name):
                    return True
            return False
        else: return False
        
    def has_menu_access(self, user, menu_name):
        
        lst = user.role.permissions
        if lst:
            for i in lst:
                if menu_name == i.view_menu.name:
                    return  True
            return False
        else: return False

    def has_permission_on_view(self, user, permission_name, view_name):
        lst = user.role.permissions
        if lst:
            for i in lst:
                if (view_name == i.view_menu.name) and (permission_name == i.permission.name):
                    return True
            return False
        else: return False
    
    def _add_permission(self, name):
        """
            Adds a permission to the backend
            param name:
                name of the permission to add: 'can_add','can_edit' etc...
        """
        perm = self.session.query(Permission).filter_by(name = name).first()
        if perm == None:
            perm = Permission()
            perm.name = name
            self.session.add(perm)
            self.session.commit()
            return perm
        return perm
        
        
    def _add_view_menu(self, name):
        """
            Adds a view menu to the backend
            param name:
                name of the view menu to add
        """
        view_menu = self.session.query(ViewMenu).filter_by(name = name).first()
        if view_menu == None:
            view_menu = ViewMenu()
            view_menu.name = name
            self.session.add(view_menu)
            self.session.commit()
            return view_menu
        return view_menu

    def _add_permission_view_menu(self, permission_name, view_menu_name):
        """
            Adds a permission on a view menu to the backend
            param permission_name:
                name of the permission to add: 'can_add','can_edit' etc...
            param view_menu_name:
                name of the view menu to add
        """
        vm = self._add_view_menu(view_menu_name)
        perm = self._add_permission(permission_name)
        pv = PermissionView()
        pv.view_menu_id, pv.permission_id = vm.id, perm.id
        self.session.add(pv)
        self.session.commit()
        print "Added Permission View" , str(pv)
        return pv
    
    
    def _find_permission(self, lst, item):
        for i in lst:
            if i.permission.name == item:
                return True
        return False
    
    def add_permissions_view(self, base_permissions, view_menu):
        """
            Adds a permission on a view menu to the backend
            param base_permissions:
                list of permissions from view (all exposed methods): 'can_add','can_edit' etc...
            param view_menu:
                name of the view or menu to add
        """
        view_menu_db = self.session.query(ViewMenu).filter_by(name = view_menu).first()
        if view_menu_db == None:
            view_menu_db = ViewMenu()
            view_menu_db = view_menu_db.add_unique(view_menu)
        lst = self.session.query(PermissionView).filter_by(view_menu_id = view_menu_db.id).all()
        # No permissions for this view
        if lst == []:
            for permission in base_permissions:
                pv = self._add_permission_view_menu(permission, view_menu)
                role_admin = self.session.query(Role).filter_by(name = self.auth_role_admin).first()
                self.add_permission_role(role_admin, pv)
        else:
            for permission in base_permissions:
                if not self._find_permission(lst, permission):
                    pv = self._add_permission_view_menu(permission, view_menu)
                    role_admin = self.session.query(Role).filter_by(name = self.auth_role_admin).first()
                    self.add_permission_role(role_admin, pv)
            for item in lst:
                if item.permission.name not in base_permissions:
                    # perm to delete
                    pass

    def add_permissions_menu(self, view_menu):
        view_menu_db = self.session.query(ViewMenu).filter_by(name = view_menu).first()
        if view_menu_db == None:
            view_menu_db = self._add_view_menu(view_menu)
        lst = self.session.query(PermissionView).filter_by(view_menu_id = view_menu_db.id).all()
        if lst == []:
            pv = self._add_permission_view_menu('menu_access', view_menu)
            role_admin = self.session.query(Role).filter_by(name = self.auth_role_admin).first()
            self.add_permission_role(role_admin, pv)

    
    def add_permission_role(self, role, perm_view):
        if perm_view not in role.permissions:
            role.permissions.append(perm_view)
            self.session.merge(role)
            self.session.commit()
            print "Added Permission" , str(perm_view) , " to Role " , role.name
