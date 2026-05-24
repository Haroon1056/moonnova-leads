import { Bell, Code2, Lock, Mail, Save, Settings, ShieldCheck, User, Workflow } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { API_URL, WS_URL } from "@/lib/constants";
import { useAuth } from "@/hooks/useAuth";

function Toggle({ checked = true }: { checked?: boolean }) {
  return <span className={`inline-flex h-6 w-11 items-center rounded-full p-1 ${checked ? "bg-primary" : "bg-slate-300"}`}><span className={`h-4 w-4 rounded-full bg-white shadow transition ${checked ? "translate-x-5" : "translate-x-0"}`} /></span>;
}

function SettingRow({ icon: Icon, title, description, children }: any) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-2xl border border-borderSoft bg-white/70 p-4">
      <div className="flex items-start gap-3"><div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primarySoft text-primaryDark ring-1 ring-orange-200"><Icon className="h-4 w-4" /></div><div><p className="text-sm font-black text-slate-900">{title}</p><p className="mt-1 text-xs leading-5 text-slate-500">{description}</p></div></div>
      {children}
    </div>
  );
}

export function SettingsPage() {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-black uppercase tracking-[0.22em] text-primaryDark">Workspace Settings</p>
        <h2 className="mt-2 text-3xl font-black tracking-tight text-slate-950">Account and SaaS preferences</h2>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">Profile, security, workflow defaults, notification preferences, and local development configuration.</p>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader><CardTitle className="flex items-center gap-2"><User className="h-5 w-5 text-primaryDark" /> Profile</CardTitle><CardDescription>Profile update API can be added in the backend later. Current profile is read from /auth/profile/.</CardDescription></CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div><Label>Full Name</Label><Input value={user?.full_name || ""} readOnly /></div>
            <div><Label>Email</Label><Input value={user?.email || ""} readOnly /></div>
            <div><Label>Role</Label><Input value={user?.is_superuser ? "Super Admin" : user?.is_staff ? "Staff" : "User"} readOnly /></div>
            <div><Label>Email Status</Label><Input value={user?.is_verified ? "Verified" : "Not verified"} readOnly /></div>
            <div className="md:col-span-2"><Button disabled><Save className="mr-2 h-4 w-4" /> Save Changes</Button></div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><ShieldCheck className="h-5 w-5 text-primaryDark" /> Security</CardTitle><CardDescription>Important account safety controls.</CardDescription></CardHeader>
          <CardContent className="space-y-3">
            <SettingRow icon={Lock} title="Password" description="Use a unique password to avoid Chrome breach warnings."><Button variant="outline" size="sm">Change</Button></SettingRow>
            <SettingRow icon={Mail} title="Email verification" description="Backend email verification required before login."><Toggle checked={Boolean(user?.is_verified)} /></SettingRow>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Workflow className="h-5 w-5 text-primaryDark" /> Workflow Defaults</CardTitle><CardDescription>Recommended defaults for a smooth SaaS experience.</CardDescription></CardHeader>
          <CardContent className="space-y-3">
            <SettingRow icon={Settings} title="Default Scrape Mode" description="Balanced mode for normal searches."><span className="text-sm font-black text-slate-900">Balanced</span></SettingRow>
            <SettingRow icon={Workflow} title="Email Enrichment" description="Keep enrichment optional and user-controlled."><Toggle checked /></SettingRow>
            <SettingRow icon={Bell} title="Completion Alerts" description="Notify users when search/export jobs complete."><Toggle checked /></SettingRow>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Code2 className="h-5 w-5 text-primaryDark" /> Developer Configuration</CardTitle><CardDescription>Local URLs used by Axios and WebSocket.</CardDescription></CardHeader>
          <CardContent className="space-y-4">
            <div><Label>API URL</Label><Input value={API_URL} readOnly /></div>
            <div><Label>WebSocket URL</Label><Input value={WS_URL} readOnly /></div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
