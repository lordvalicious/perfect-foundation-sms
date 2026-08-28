import { useAuth } from "./auth";

/**
 * PermissionGate - Conditionally render children based on permission.
 * 
 * Usage:
 * <PermissionGate permission="student.create">
 *   <CreateStudentButton />
 * </PermissionGate>
 * 
 * <PermissionGate permission="finance.invoice.view" fallback={<AccessDenied />}>
 *   <InvoiceList />
 * </PermissionGate>
 */
export function PermissionGate({ permission, children, fallback = null }) {
  const { hasPermission } = useAuth();
  
  if (hasPermission(permission)) {
    return children;
  }
  
  return fallback;
}

/**
 * RoleGate - Conditionally render children based on role.
 * 
 * Usage:
 * <RoleGate roles={["admin", "principal"]}>
 *   <AdminPanel />
 * </RoleGate>
 */
export function RoleGate({ roles, children, fallback = null }) {
  const { hasRole } = useAuth();
  
  if (hasRole(roles)) {
    return children;
  }
  
  return fallback;
}

/**
 * RequirePermission - HOC to wrap a component with permission check.
 * 
 * Usage:
 * const AdminOnlyComponent = RequirePermission("user.manage", AdminPanel);
 */
export function RequirePermission(permission, WrappedComponent, fallback = null) {
  return function WithPermission(props) {
    const { hasPermission } = useAuth();
    
    if (hasPermission(permission)) {
      return <WrappedComponent {...props} />;
    }
    
    return fallback;
  };
}

/**
 * RequireRole - HOC to wrap a component with role check.
 */
export function RequireRole(roles, WrappedComponent, fallback = null) {
  return function WithRole(props) {
    const { hasRole } = useAuth();
    
    if (hasRole(roles)) {
      return <WrappedComponent {...props} />;
    }
    
    return fallback;
  };
}