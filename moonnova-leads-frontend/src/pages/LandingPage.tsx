import {
  ArrowRight,
  BarChart3,
  Bot,
  CheckCircle2,
  Database,
  Download,
  Globe2,
  MailCheck,
  MapPin,
  Menu,
  PlayCircle,
  Search,
  ShieldCheck,
  Sparkles,
  Star,
  Target,
  X
} from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";

const features = [
  {
    icon: Search,
    title: "Google Maps Lead Scraping",
    description:
      "Find businesses by keyword and location, then collect structured lead data in one clean dashboard."
  },
  {
    icon: Globe2,
    title: "Website Quality Detection",
    description:
      "Quickly identify businesses with no website, broken sites, expired domains, SSL issues, or weak website builders."
  },
  {
    icon: MailCheck,
    title: "Email & Website Enrichment",
    description:
      "Run enrichment after scraping to discover emails, website details, and contact-ready business data."
  },
  {
    icon: Bot,
    title: "AI Lead Insights",
    description:
      "Use AI to score leads, generate outreach angles, create first lines, and understand the best sales opportunity."
  },
  {
    icon: BarChart3,
    title: "Live Progress Tracking",
    description:
      "Monitor search jobs in real time with progress, completed tasks, collected leads, and enrichment status."
  },
  {
    icon: Download,
    title: "Clean CSV Export",
    description:
      "Export selected or filtered leads with contact details, website status, AI insights, and campaign-ready fields."
  }
];

const workflow = [
  {
    step: "01",
    title: "Enter keywords and locations",
    description:
      "Add business categories like plumbers, roofers, dentists, gyms, contractors, restaurants, or any niche you want."
  },
  {
    step: "02",
    title: "Scrape business leads",
    description:
      "MoonNova Leads collects business names, categories, phone numbers, addresses, websites, ratings, and map links."
  },
  {
    step: "03",
    title: "Check website opportunities",
    description:
      "The system highlights no-website businesses, broken websites, social-only listings, and weak website builders."
  },
  {
    step: "04",
    title: "Enrich and score leads",
    description:
      "Run enrichment to find emails and use AI to score each lead based on opportunity, fit, and outreach readiness."
  },
  {
    step: "05",
    title: "Export and start outreach",
    description:
      "Download clean lead files for cold email, LinkedIn outreach, WhatsApp, calling, or agency prospecting."
  }
];

const useCases = [
  "Web design agencies finding businesses without websites",
  "SEO agencies targeting weak local SEO opportunities",
  "Cold email teams building niche-specific prospect lists",
  "Lead generation freelancers delivering verified business data",
  "Local service agencies finding high-intent local businesses",
  "Sales teams building location-based outbound campaigns"
];

const stats = [
  ["10x", "Faster prospect research"],
  ["24/7", "Search job tracking"],
  ["CSV", "Export-ready lead files"],
  ["AI", "Lead scoring and insights"]
];

const faqs = [
  {
    question: "What is MoonNova Leads?",
    answer:
      "MoonNova Leads is a lead generation SaaS for scraping, enriching, scoring, filtering, and exporting local business leads from Google Maps style searches."
  },
  {
    question: "Who is it best for?",
    answer:
      "It is best for web design agencies, SEO agencies, lead generation freelancers, cold email teams, local marketing agencies, and B2B sales teams."
  },
  {
    question: "What type of leads can I find?",
    answer:
      "You can find businesses by keyword and location, such as plumbers in Perth, dentists in Sydney, roofers in Brisbane, gyms in Melbourne, or any custom niche."
  },
  {
    question: "Can it find businesses without websites?",
    answer:
      "Yes. One of the strongest use cases is identifying businesses with no website, broken website, social-only presence, free-builder websites, or technical website issues."
  },
  {
    question: "Does it export leads?",
    answer:
      "Yes. You can export selected or filtered leads into CSV files with business, contact, website, enrichment, and AI insight fields."
  }
];

export function LandingPage() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen overflow-x-hidden bg-[#f7f3ea] text-slate-950">
      <header className="sticky top-0 z-50 border-b border-amber-900/10 bg-[#f7f3ea]/85 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <Link to="/" className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-500 to-orange-700 text-white shadow-lg shadow-orange-900/20">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <div className="text-lg font-black leading-none tracking-tight">
                MoonNova Leads
              </div>
              <div className="mt-1 text-xs font-bold text-amber-800">
                Premium Lead Intelligence
              </div>
            </div>
          </Link>

          <nav className="hidden items-center gap-8 text-sm font-bold text-slate-700 lg:flex">
            <a href="#features" className="transition hover:text-amber-700">
              Features
            </a>
            <a href="#workflow" className="transition hover:text-amber-700">
              Workflow
            </a>
            <a href="#use-cases" className="transition hover:text-amber-700">
              Use Cases
            </a>
            <a href="#faq" className="transition hover:text-amber-700">
              FAQ
            </a>
          </nav>

          <div className="hidden items-center gap-3 lg:flex">
            <Link to="/auth/login">
              <Button variant="outline">Login</Button>
            </Link>
            <Link to="/auth/register">
              <Button>
                Start Free
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>

          <button
            className="inline-flex h-11 w-11 items-center justify-center rounded-xl border border-amber-900/15 bg-white/70 lg:hidden"
            onClick={() => setMobileOpen((value) => !value)}
            aria-label="Toggle navigation"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

        {mobileOpen && (
          <div className="border-t border-amber-900/10 bg-[#f7f3ea] px-4 py-4 lg:hidden">
            <div className="grid gap-3 text-sm font-bold text-slate-700">
              <a href="#features" onClick={() => setMobileOpen(false)}>
                Features
              </a>
              <a href="#workflow" onClick={() => setMobileOpen(false)}>
                Workflow
              </a>
              <a href="#use-cases" onClick={() => setMobileOpen(false)}>
                Use Cases
              </a>
              <a href="#faq" onClick={() => setMobileOpen(false)}>
                FAQ
              </a>
              <div className="mt-3 grid gap-2">
                <Link to="/auth/login">
                  <Button variant="outline" className="w-full">
                    Login
                  </Button>
                </Link>
                <Link to="/auth/register">
                  <Button className="w-full">Start Free</Button>
                </Link>
              </div>
            </div>
          </div>
        )}
      </header>

      <main>
        <section className="relative overflow-hidden">
          <div className="absolute left-0 top-0 h-96 w-96 rounded-full bg-amber-500/20 blur-3xl" />
          <div className="absolute right-0 top-24 h-96 w-96 rounded-full bg-teal-700/15 blur-3xl" />

          <div className="relative mx-auto grid max-w-7xl gap-12 px-4 py-16 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:px-8 lg:py-24">
            <div className="flex flex-col justify-center">
              <div className="inline-flex w-fit items-center gap-2 rounded-full border border-amber-900/15 bg-white/70 px-4 py-2 text-xs font-black uppercase tracking-[0.18em] text-amber-800 shadow-sm">
                <Star className="h-4 w-4 fill-amber-500 text-amber-500" />
                Built for agencies, freelancers, and outbound teams
              </div>

              <h1 className="mt-6 max-w-4xl text-4xl font-black tracking-tight text-slate-950 sm:text-5xl lg:text-6xl">
                Find, enrich, score, and export high-quality business leads.
              </h1>

              <p className="mt-6 max-w-2xl text-base leading-8 text-slate-600 sm:text-lg">
                MoonNova Leads helps you turn local business searches into clean,
                export-ready prospect lists. Find businesses with no websites, broken
                websites, weak online presence, missing emails, and strong outreach
                opportunities.
              </p>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Link to="/auth/register">
                  <Button size="lg" className="w-full sm:w-auto">
                    Start Building Leads
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Button>
                </Link>

                <a href="#workflow">
                  <Button size="lg" variant="outline" className="w-full sm:w-auto">
                    <PlayCircle className="mr-2 h-5 w-5" />
                    See How It Works
                  </Button>
                </a>
              </div>

              <div className="mt-8 grid gap-3 sm:grid-cols-3">
                {[
                  "No website detection",
                  "Email enrichment",
                  "AI lead scoring"
                ].map((item) => (
                  <div
                    key={item}
                    className="flex items-center gap-2 text-sm font-bold text-slate-700"
                  >
                    <CheckCircle2 className="h-5 w-5 text-teal-700" />
                    {item}
                  </div>
                ))}
              </div>
            </div>

            <div className="relative">
              <div className="rounded-[2rem] border border-amber-900/10 bg-white/70 p-3 shadow-2xl shadow-slate-900/10 backdrop-blur-xl">
                <div className="rounded-[1.5rem] border border-amber-900/10 bg-[#11100d] p-4 text-white">
                  <div className="flex items-center justify-between border-b border-white/10 pb-4">
                    <div>
                      <div className="text-sm font-black">MoonNova Command Center</div>
                      <div className="mt-1 text-xs text-white/50">
                        Live search and enrichment pipeline
                      </div>
                    </div>
                    <div className="rounded-full bg-emerald-500/15 px-3 py-1 text-xs font-black text-emerald-300">
                      Live
                    </div>
                  </div>

                  <div className="mt-5 grid gap-3 sm:grid-cols-2">
                    {[
                      ["Total Leads", "8,420", Database],
                      ["Emails Found", "3,128", MailCheck],
                      ["Web Opportunities", "2,470", Target],
                      ["AI Scored", "6,900", Bot]
                    ].map(([label, value, Icon]: any) => (
                      <div
                        key={label}
                        className="rounded-2xl border border-white/10 bg-white/[0.04] p-4"
                      >
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-bold text-white/50">{label}</p>
                          <Icon className="h-4 w-4 text-amber-400" />
                        </div>
                        <p className="mt-3 text-2xl font-black">{value}</p>
                      </div>
                    ))}
                  </div>

                  <div className="mt-5 rounded-2xl border border-white/10 bg-white/[0.04] p-4">
                    <div className="mb-4 flex items-center justify-between">
                      <div>
                        <p className="text-sm font-black">Recent Search</p>
                        <p className="mt-1 text-xs text-white/50">
                          roofing contractor in Perth WA
                        </p>
                      </div>
                      <span className="rounded-full bg-emerald-500/15 px-3 py-1 text-xs font-black text-emerald-300">
                        Completed
                      </span>
                    </div>

                    <div className="space-y-3">
                      {[
                        ["Scraping business listings", "100%"],
                        ["Checking websites", "92%"],
                        ["Finding emails", "68%"],
                        ["Generating AI insights", "74%"]
                      ].map(([label, percent]) => (
                        <div key={label}>
                          <div className="mb-1 flex justify-between text-xs">
                            <span className="text-white/60">{label}</span>
                            <span className="font-bold text-white">{percent}</span>
                          </div>
                          <div className="h-2 rounded-full bg-white/10">
                            <div
                              className="h-2 rounded-full bg-gradient-to-r from-amber-500 to-teal-500"
                              style={{ width: percent }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="mt-5 grid gap-3 sm:grid-cols-3">
                    {stats.map(([value, label]) => (
                      <div
                        key={label}
                        className="rounded-2xl border border-white/10 bg-white/[0.04] p-3 text-center"
                      >
                        <div className="text-lg font-black text-amber-300">
                          {value}
                        </div>
                        <div className="mt-1 text-[11px] font-bold text-white/50">
                          {label}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="absolute -bottom-6 -left-4 hidden rounded-2xl border border-amber-900/10 bg-white p-4 shadow-xl sm:block">
                <div className="flex items-center gap-3">
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700">
                    <ShieldCheck className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-sm font-black">Website quality checked</p>
                    <p className="text-xs text-slate-500">
                      No website, broken, social-only, free builder
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="features" className="border-y border-amber-900/10 bg-white/45 py-16">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-3xl text-center">
              <p className="text-xs font-black uppercase tracking-[0.22em] text-amber-800">
                Features
              </p>
              <h2 className="mt-3 text-3xl font-black tracking-tight sm:text-4xl">
                Everything needed to build better lead lists
              </h2>
              <p className="mt-4 text-base leading-7 text-slate-600">
                From scraping to enrichment, scoring, filtering, and exporting,
                MoonNova Leads gives your outbound system a clean data foundation.
              </p>
            </div>

            <div className="mt-12 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
              {features.map((feature) => (
                <div
                  key={feature.title}
                  className="rounded-3xl border border-amber-900/10 bg-white/80 p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-xl"
                >
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-50 text-amber-800 ring-1 ring-amber-900/10">
                    <feature.icon className="h-6 w-6" />
                  </div>
                  <h3 className="mt-5 text-lg font-black">{feature.title}</h3>
                  <p className="mt-3 text-sm leading-7 text-slate-600">
                    {feature.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="workflow" className="py-16 lg:py-20">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="grid gap-10 lg:grid-cols-[0.8fr_1.2fr] lg:items-start">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.22em] text-amber-800">
                  Workflow
                </p>
                <h2 className="mt-3 text-3xl font-black tracking-tight sm:text-4xl">
                  A simple lead generation process from search to export
                </h2>
                <p className="mt-4 text-base leading-7 text-slate-600">
                  MoonNova Leads keeps the workflow easy for users. Start a search,
                  review leads, identify website opportunities, enrich contacts, and
                  export clean files for outreach.
                </p>

                <div className="mt-6 rounded-3xl border border-amber-900/10 bg-white/70 p-5">
                  <div className="flex items-start gap-3">
                    <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-teal-50 text-teal-700">
                      <MapPin className="h-5 w-5" />
                    </div>
                    <div>
                      <h3 className="font-black">Example search</h3>
                      <p className="mt-1 text-sm leading-6 text-slate-600">
                        Search: <strong>roofing contractor</strong> in{" "}
                        <strong>Perth WA</strong>. Then filter businesses with no
                        website or website issues and export them for web design
                        outreach.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="grid gap-4">
                {workflow.map((item) => (
                  <div
                    key={item.step}
                    className="grid gap-4 rounded-3xl border border-amber-900/10 bg-white/80 p-5 shadow-sm sm:grid-cols-[80px_1fr]"
                  >
                    <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#11100d] text-lg font-black text-amber-300">
                      {item.step}
                    </div>
                    <div>
                      <h3 className="text-lg font-black">{item.title}</h3>
                      <p className="mt-2 text-sm leading-7 text-slate-600">
                        {item.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section id="use-cases" className="bg-[#11100d] py-16 text-white lg:py-20">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="grid gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.22em] text-amber-300">
                  Use Cases
                </p>
                <h2 className="mt-3 text-3xl font-black tracking-tight sm:text-4xl">
                  Built for real outbound and agency workflows
                </h2>
                <p className="mt-4 text-base leading-8 text-white/65">
                  Whether you sell websites, SEO, local marketing, software, B2B
                  services, or appointment-setting, MoonNova Leads helps you find
                  better prospects faster.
                </p>

                <Link to="/auth/register">
                  <Button className="mt-7">
                    Start Your First Search
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </Link>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                {useCases.map((item) => (
                  <div
                    key={item}
                    className="flex gap-3 rounded-2xl border border-white/10 bg-white/[0.04] p-4"
                  >
                    <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-amber-300" />
                    <p className="text-sm font-semibold leading-6 text-white/80">
                      {item}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="py-16 lg:py-20">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="rounded-[2rem] border border-amber-900/10 bg-white/80 p-8 shadow-xl shadow-slate-900/5 lg:p-10">
              <div className="grid gap-8 lg:grid-cols-[1fr_0.8fr] lg:items-center">
                <div>
                  <p className="text-xs font-black uppercase tracking-[0.22em] text-amber-800">
                    Why MoonNova Leads
                  </p>
                  <h2 className="mt-3 text-3xl font-black tracking-tight sm:text-4xl">
                    Better lead quality means better outreach results
                  </h2>
                  <p className="mt-4 text-base leading-8 text-slate-600">
                    Most outreach campaigns fail because the data is poor. MoonNova
                    Leads is designed around high-intent prospecting signals like
                    missing websites, weak online presence, business category,
                    location, website quality, and AI opportunity scoring.
                  </p>
                </div>

                <div className="grid gap-4">
                  {[
                    ["Cleaner targeting", "Build focused lists by niche and location."],
                    [
                      "Stronger sales angles",
                      "Use website issues and missing web presence as real reasons to reach out."
                    ],
                    [
                      "Less manual research",
                      "Scrape, enrich, filter, score, and export in one workflow."
                    ]
                  ].map(([title, description]) => (
                    <div
                      key={title}
                      className="rounded-2xl border border-amber-900/10 bg-[#f9f4e9] p-4"
                    >
                      <h3 className="font-black">{title}</h3>
                      <p className="mt-1 text-sm leading-6 text-slate-600">
                        {description}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="faq" className="border-t border-amber-900/10 bg-white/45 py-16">
          <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <p className="text-xs font-black uppercase tracking-[0.22em] text-amber-800">
                FAQ
              </p>
              <h2 className="mt-3 text-3xl font-black tracking-tight sm:text-4xl">
                Common questions
              </h2>
            </div>

            <div className="mt-10 grid gap-4">
              {faqs.map((faq) => (
                <div
                  key={faq.question}
                  className="rounded-3xl border border-amber-900/10 bg-white/80 p-6"
                >
                  <h3 className="text-base font-black">{faq.question}</h3>
                  <p className="mt-2 text-sm leading-7 text-slate-600">
                    {faq.answer}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="px-4 py-16 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-5xl rounded-[2rem] bg-gradient-to-br from-[#11100d] to-[#20170f] p-8 text-center text-white shadow-2xl shadow-slate-900/20 lg:p-12">
            <p className="text-xs font-black uppercase tracking-[0.22em] text-amber-300">
              Start Today
            </p>
            <h2 className="mt-3 text-3xl font-black tracking-tight sm:text-4xl">
              Build your next lead list with MoonNova Leads
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-base leading-8 text-white/65">
              Start searching by keyword and location, review business opportunities,
              enrich contacts, generate AI insights, and export your leads.
            </p>

            <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
              <Link to="/auth/register">
                <Button size="lg" className="w-full sm:w-auto">
                  Create Free Account
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>

              <Link to="/auth/login">
                <Button size="lg" variant="outline" className="w-full bg-white text-slate-950 hover:bg-amber-50 sm:w-auto">
                  Login
                </Button>
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-amber-900/10 bg-[#11100d] py-8 text-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 sm:px-6 md:flex-row md:items-center md:justify-between lg:px-8">
          <div>
            <div className="text-lg font-black">MoonNova Leads</div>
            <div className="mt-1 text-sm text-white/50">
              Premium lead intelligence for agencies and outbound teams.
            </div>
          </div>

          <div className="flex flex-wrap gap-4 text-sm font-bold text-white/60">
            <a href="#features" className="hover:text-white">
              Features
            </a>
            <a href="#workflow" className="hover:text-white">
              Workflow
            </a>
            <a href="#use-cases" className="hover:text-white">
              Use Cases
            </a>
            <Link to="/auth/login" className="hover:text-white">
              Login
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}