from library.composites.app.commands.extend_membership import extend_membership
from library.interfaces.api.resources.readers import MembershipsResource

memberships_resource = MembershipsResource(extend_membership=extend_membership)
