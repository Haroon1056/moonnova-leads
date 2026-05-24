import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  Brain,
  ChevronLeft,
  Download,
  Home,
  LifeBuoy,
  ListChecks,
  LogOut,
  Menu,
  Search,
  Server,
  Settings,
  Sparkles,
  WalletCards,
  X
} from "lucide-react";
import { useMemo, useState } from "react";
import { APP_NAME } from "@/lib/constants";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/store/authStore";
import { useLeadFiltersStore } from "@/store/leadFiltersStore";
import { cn } from "@/lib/utils";

const baseNavItems = [
  { label: "Dashboard", href: "/dashboard", icon: Home },
  { label: "Searches", href: "/dashboard/searches", icon: Search },
  { label: "Leads", href: "/dashboard/leads", icon: ListChecks },
  { label: "AI Workspace", href: "/dashboard/ai", icon: Brain },
  { label: "Exports", href: "/dashboard/exports", icon: Download },
  { label: "Usage", href: "/dashboard/usage", icon: WalletCards },
  { label: "Settings", href: "/dashboard/settings", icon: Settings }
];

const adminNavItem = { label: "Admin", href: "/dashboard/admin", icon: Server };

function initials(name?: string | null, email?: string | null) {
  const value = name || email || "User";
  return value
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export function DashboardLayout() {
  const [open, setOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [globalSearch, setGlobalSearch] = useState("");
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const setLeadFilter = useLeadFiltersStore((state) => state.setFilter);

  const isAdmin = Boolean(user?.is_staff || user?.is_superuser);
  const navItems = useMemo(
    () => (isAdmin ? [...baseNavItems, adminNavItem] : baseNavItems),
    [isAdmin]
  );

  function handleLogout() {
    logout();
    navigate("/auth/login");
  }

  function handleGlobalSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = globalSearch.trim();
    if (!value) return;
    setLeadFilter("search", value);
    navigate("/dashboard/leads");
  }

  return (
    <div className="min-h-screen text-slate-950">
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 transform overflow-hidden border-r border-white/10 gradient-dark text-white shadow-2xl shadow-black/30 transition-all duration-300 lg:translate-x-0",
          collapsed ? "lg:w-24" : "lg:w-72",
          open ? "w-72 translate-x-0" : "w-72 -translate-x-full"
        )}
      >
        <div className="relative flex h-full min-h-0 flex-col">
          <div className="flex h-20 shrink-0 items-center gap-3 border-b border-white/10 px-5">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-500 to-orange-700 shadow-lg shadow-amber-700/30">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            {!collapsed && (
              <div className="min-w-0">
                <div className="truncate text-xl font-black tracking-tight text-white">
                  {APP_NAME}
                </div>
                <div className="mt-1 text-xs font-semibold text-amber-100/70">
                  Premium Lead Intelligence
                </div>
              </div>
            )}
            <button
              className="ml-auto rounded-xl p-2 text-white/70 hover:bg-white/10 hover:text-white lg:hidden"
              onClick={() => setOpen(false)}
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <nav className="min-h-0 flex-1 space-y-1.5 overflow-y-auto px-3 py-5">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.href}
                  to={item.href}
                  end={item.href === "/dashboard"}
                  onClick={() => setOpen(false)}
                  className={({ isActive }) =>
                    cn(
                      "group flex items-center gap-3 rounded-2xl px-3 py-2.5 text-sm font-bold transition-all duration-200",
                      isActive
                        ? "bg-gradient-to-r from-amber-600 to-orange-700 text-white shadow-lg shadow-amber-950/30"
                        : "text-stone-300 hover:bg-white/10 hover:text-white",
                      collapsed && "lg:justify-center lg:px-2"
                    )
                  }
                  title={collapsed ? item.label : undefined}
                >
                  {({ isActive }) => (
                    <>
                      <span
                        className={cn(
                          "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl transition",
                          isActive
                            ? "bg-white/16 text-white"
                            : "bg-white/5 text-stone-300 group-hover:bg-white/10 group-hover:text-white"
                        )}
                      >
                        <Icon className="h-4 w-4" />
                      </span>
                      {!collapsed && <span className="truncate">{item.label}</span>}
                    </>
                  )}
                </NavLink>
              );
            })}
          </nav>

          <div className="shrink-0 border-t border-white/10 p-3">
            {!collapsed && (
              <div className="mb-3 rounded-2xl border border-amber-200/15 bg-white/[0.06] p-3">
                <div className="flex items-start gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-500/15 text-sm font-black text-amber-100 ring-1 ring-amber-300/20">
                    {initials(user?.full_name, user?.email)}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-bold text-white">
                      {user?.full_name || user?.email || "User"}
                    </div>
                    <div className="truncate text-xs text-stone-400">{user?.email}</div>
                    {isAdmin && (
                      <div className="mt-2 inline-flex rounded-full border border-amber-400/30 bg-amber-500/10 px-2 py-0.5 text-[10px] font-black uppercase tracking-wide text-amber-100">
                        {user?.is_superuser ? "Super Admin" : "Staff"}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            <div className="grid gap-2">
              <NavLink to="/dashboard/settings" className="lg:hidden">
                <Button variant="ghost" className="w-full justify-start text-stone-300 hover:bg-white/10 hover:text-white">
                  <LifeBuoy className="mr-2 h-4 w-4" /> Help & Settings
                </Button>
              </NavLink>
              <Button
                variant="ghost"
                onClick={handleLogout}
                className={cn(
                  "w-full text-stone-300 hover:bg-red-500/15 hover:text-red-100",
                  collapsed ? "lg:px-0" : "justify-start"
                )}
                title={collapsed ? "Logout" : undefined}
              >
                <LogOut className={cn("h-4 w-4", !collapsed && "mr-2")} />
                {!collapsed && "Logout"}
              </Button>
            </div>
          </div>
        </div>
      </aside>

      {open && <button className="fixed inset-0 z-30 bg-slate-950/45 lg:hidden" onClick={() => setOpen(false)} />}

      <div className={cn("transition-all duration-300", collapsed ? "lg:pl-24" : "lg:pl-72")}>
        <header className="sticky top-0 z-20 border-b border-borderSoft/80 bg-[#fbfaf7]/82 backdrop-blur-xl">
          <div className="flex h-16 items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
            <div className="flex items-center gap-3">
              <button
                className="rounded-xl border border-borderSoft bg-white/70 p-2 shadow-sm lg:hidden"
                onClick={() => setOpen(true)}
              >
                <Menu className="h-5 w-5" />
              </button>
              <button
                className="hidden rounded-xl border border-borderSoft bg-white/70 p-2 shadow-sm hover:bg-white lg:inline-flex"
                onClick={() => setCollapsed((value) => !value)}
                title="Collapse sidebar"
              >
                <ChevronLeft className={cn("h-5 w-5 transition", collapsed && "rotate-180")} />
              </button>
              <div>
                <h1 className="text-base font-black text-slate-950">MoonNova Command Center</h1>
                <p className="hidden text-xs font-medium text-slate-500 sm:block">
                  Search, verify, enrich, score, and export qualified leads.
                </p>
              </div>
            </div>

            <form
              onSubmit={handleGlobalSearch}
              className="hidden w-full max-w-lg items-center rounded-2xl border border-borderSoft bg-white/75 px-3 py-2 shadow-sm md:flex"
            >
              <Search className="mr-2 h-4 w-4 text-slate-400" />
              <input
                className="w-full bg-transparent text-sm font-medium outline-none placeholder:text-slate-400"
                placeholder="Search leads, phone, email, category, city..."
                value={globalSearch}
                onChange={(event) => setGlobalSearch(event.target.value)}
              />
            </form>
          </div>
        </header>

        <main className="min-h-[calc(100vh-4rem)] px-4 py-6 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
