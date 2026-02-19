import { PermissionManager } from "./components/PermissionManager";

export default function PermissionsPage() {
  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-slate-900 mb-6">
        Quan ly quyen han
      </h1>
      <PermissionManager />
    </div>
  );
}
