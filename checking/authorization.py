from zope.interface import implements

from repoze.bfg.interfaces import IAuthorizationPolicy
from repoze.bfg.security import ACLAllowed
from repoze.bfg.security import ACLDenied
from repoze.bfg.security import Allow
from repoze.bfg.security import Deny
from repoze.bfg.security import Everyone
from repoze.bfg.security import Authenticated

GLOBAL_ACL = [ (Deny,  Authenticated, "signup"),
               (Allow, Everyone,      "signup"),
               (Allow, Authenticated, ("auth", "add-customer")),
             ]

class RouteAuthorizationPolicy(object):
    """Variant of the default BFG ACL authorization policy. This policy checks
    both the current context, if there is one, and a global ACL list.
    """
    implements(IAuthorizationPolicy)

    def permits(self, context, principals, permission):
        """ Return ``ACLAllowed`` if the policy permits access,
        ``ACLDenied`` if not. """
        acls = [ GLOBAL_ACL ]
        try:
            acls.insert(0, context.__acl__)
        except AttributeError:
            pass

        for acl in acls:
            for ace in acl:
                ace_action, ace_principal, ace_permissions = ace
                if ace_principal in principals:
                    if not hasattr(ace_permissions, '__iter__'):
                        ace_permissions = [ace_permissions]
                    if permission in ace_permissions:
                        if ace_action == Allow:
                            return ACLAllowed(ace, acl, permission,
                                              principals, context)
                        else:
                            return ACLDenied(ace, acl, permission,
                                             principals, context)

        # default deny if no ACL in lineage at all
        return ACLDenied(None, None, permission, principals, context)

    def principals_allowed_by_permission(self, context, permission):
        """ Return the set of principals explicitly granted the
        permission named ``permission`` according to the ACL directly
        attached to the context context as well as inherited ACLs. """
        allowed = set()

        acls = [ GLOBAL_ACL ]
        try:
            acls.append(context.__acl__)
        except AttributeError:
            pass

        for acl in acls:
            allowed_here = set()
            denied_here = set()
            
            for ace_action, ace_principal, ace_permissions in acl:
                if not hasattr(ace_permissions, '__iter__'):
                    ace_permissions = [ace_permissions]
                if ace_action == Allow and permission in ace_permissions:
                    if not ace_principal in denied_here:
                        allowed_here.add(ace_principal)
                if ace_action == Deny and permission in ace_permissions:
                    denied_here.add(ace_principal)
                    if ace_principal == Everyone:
                        # clear the entire allowed set, as we've hit a
                        # deny of Everyone ala (Deny, Everyone, ALL)
                        allowed = set()
                        break
                    elif ace_principal in allowed:
                        allowed.remove(ace_principal)

            allowed.update(allowed_here)

        return allowed
