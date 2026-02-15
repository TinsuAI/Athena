import { UserList } from "./components/UserList";

export default function UsersPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-slate-900 mb-6">
        User Management
      </h1>
      <UserList />
    </div>
  );
}
