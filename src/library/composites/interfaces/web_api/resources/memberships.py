from library.composites.app.commands.extend_membership import extend_membership
from library.interfaces.web_api.resources.memberships import MembershipsResource

memberships = MembershipsResource(extend_membership=extend_membership)
