import { Edit, Trash2, FileText, Check } from "lucide-react";

/**
 * Table of workflow definitions with CRUD actions.
 */
export function WorkflowDefinitionList({
  definitions,
  onEdit,
  onDelete,
  onTest,
  loading = false,
}) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border-collapse">
        <thead>
          <tr className="bg-gray-50 border-b border-gray-200">
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">Name</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">Slug</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">Object Type</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">States</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">Steps</th>
            <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {definitions.map((def) => (
            <tr key={def.id} className="hover:bg-gray-50">
              <td className="px-4 py-3">
                <p className="text-sm font-medium text-gray-900">{def.name}</p>
              </td>
              <td className="px-4 py-3">
                <code className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded">
                  {def.slug}
                </code>
              </td>
              <td className="px-4 py-3">
                <p className="text-sm text-gray-600">{def.object_type}</p>
              </td>
              <td className="px-4 py-3">
                <div className="flex gap-1 flex-wrap">
                  {def.states?.map((state) => (
                    <span
                      key={state}
                      className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded"
                    >
                      {state}
                    </span>
                  ))}
                </div>
              </td>
              <td className="px-4 py-3">
                <div className="flex gap-1 flex-wrap">
                  {def.approval_steps?.map((step) => (
                    <span
                      key={step}
                      className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded"
                    >
                      {step}
                    </span>
                  ))}
                </div>
              </td>
              <td className="px-4 py-3">
                <div className="flex justify-center gap-2">
                  <button
                    onClick={() => onTest(def)}
                    title="Test"
                    className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                    disabled={loading}
                  >
                    <FileText className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => onEdit(def)}
                    title="Edit"
                    className="p-2 text-gray-600 hover:bg-gray-100 rounded"
                    disabled={loading}
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => onDelete(def)}
                    title="Delete"
                    className="p-2 text-red-600 hover:bg-red-50 rounded"
                    disabled={loading}
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {definitions.length === 0 && (
        <div className="text-center py-8">
          <p className="text-gray-500">No workflow definitions found</p>
        </div>
      )}
    </div>
  );
}
