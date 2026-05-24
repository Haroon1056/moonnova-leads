import { Outlet } from "react-router-dom";
import { CheckCircle2, Database, Sparkles, Wand2 } from "lucide-react";
import { APP_NAME } from "@/lib/constants";

export function AuthLayout() {
  return (
    <div className="min-h-screen bg-background">
      <div className="grid min-h-screen lg:grid-cols-[1.05fr_0.95fr]">
        <div className="relative hidden overflow-hidden gradient-dark p-10 text-white lg:flex lg:flex-col lg:justify-between">
          <div className="absolute -left-24 top-16 h-72 w-72 rounded-full bg-amber-600/20 blur-3xl" />
          <div className="absolute -right-24 bottom-16 h-72 w-72 rounded-full bg-teal-600/20 blur-3xl" />

          <div className="relative">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-500 to-orange-700 shadow-lg shadow-amber-900/30">
                <Sparkles className="h-6 w-6" />
              </div>
              <div>
                <div className="text-2xl font-black tracking-tight">{APP_NAME}</div>
                <p className="text-xs font-semibold uppercase tracking-[0.3em] text-amber-100/60">
                  Lead Intelligence SaaS
                </p>
              </div>
            </div>

            <div className="mt-20 max-w-xl">
              <p className="rounded-full border border-amber-200/15 bg-white/5 px-4 py-2 text-xs font-bold uppercase tracking-[0.24em] text-amber-100/80">
                Search • Enrich • Score • Export
              </p>
              <h1 className="mt-6 text-5xl font-black leading-tight tracking-tight">
                Build cleaner prospect lists with a premium workflow.
              </h1>
              <p className="mt-5 text-base leading-8 text-stone-300">
                Scrape business data, review website quality, enrich emails,
                generate AI insights, and export campaign-ready lead files from
                one focused workspace.
              </p>
            </div>
          </div>

          <div className="relative grid gap-3 rounded-3xl border border-white/10 bg-white/[0.06] p-5 backdrop-blur">
            {[
              { icon: Database, text: "Organized searches and lead records" },
              { icon: Wand2, text: "Optional enrichment and AI personalization" },
              { icon: CheckCircle2, text: "Clean exports for outreach workflows" }
            ].map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.text} className="flex items-center gap-3 text-sm font-semibold text-stone-200">
                  <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-500/12 text-amber-100 ring-1 ring-amber-300/15">
                    <Icon className="h-4 w-4" />
                  </span>
                  {item.text}
                </div>
              );
            })}
          </div>
        </div>

        <div className="flex items-center justify-center px-4 py-10">
          <div className="w-full max-w-md">
            <div className="mb-8 text-center lg:hidden">
              <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl gradient-gold text-white shadow-glow">
                <Sparkles className="h-6 w-6" />
              </div>
              <div className="text-2xl font-black text-slate-950">{APP_NAME}</div>
              <p className="mt-2 text-sm text-slate-500">Lead intelligence dashboard</p>
            </div>
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  );
}
