import { useEffect, useState, type ReactNode } from "react";
import { Link } from "@tanstack/react-router";
import { BookOpenText, History, LayoutDashboard, Menu, PenLine, UserRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { OwnerProvider, useOwner } from "./owner-context";

const nav = [
  { to: "/" as const, label: "Dashboard", icon: LayoutDashboard, exact: true },
  { to: "/new-research" as const, label: "New Research", icon: PenLine },
  { to: "/history" as const, label: "History", icon: History },
];

function SidebarContent({ close }: { close?: () => void }) {
  const { ownerName, setEditing } = useOwner();
  return <div className="flex h-full flex-col">
    <Link to="/" onClick={close} className="flex items-center gap-3 px-5 py-6 text-sidebar-foreground">
      <span className="brand-mark"><BookOpenText /></span><span className="text-base font-semibold">Deep Research</span>
    </Link>
    <nav className="mt-3 space-y-1 px-3" aria-label="Workspace navigation">
      {nav.map(({ to, label, icon: Icon, exact }) => <Link key={to} to={to} activeOptions={{ exact: Boolean(exact) }} onClick={close} activeProps={{ className: "sidebar-link sidebar-link--active" }} inactiveProps={{ className: "sidebar-link" }}><Icon />{label}</Link>)}
    </nav>
    <div className="mt-auto border-t border-sidebar-border p-4">
      <div className="flex items-center gap-3">
        <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-sidebar-accent text-sm font-semibold text-sidebar-accent-foreground">{ownerName ? ownerName.charAt(0).toUpperCase() : <UserRound className="size-4" />}</span>
        <div className="min-w-0 flex-1"><p className="truncate text-sm font-medium text-sidebar-foreground">{ownerName || "Researcher"}</p><button type="button" onClick={() => { setEditing(true); close?.(); }} className="text-xs text-sidebar-foreground/55 transition hover:text-sidebar-foreground">Change name</button></div>
      </div>
    </div>
  </div>;
}

function OwnerDialog() {
  const { ownerName, editing, setEditing, saveOwnerName } = useOwner();
  const [name, setName] = useState(ownerName);
  useEffect(() => setName(ownerName), [ownerName, editing]);
  return <Dialog open={editing} onOpenChange={(open) => { if (ownerName) setEditing(open); }}>
    <DialogContent className="max-w-sm" hideClose={!ownerName} onPointerDownOutside={(e) => { if (!ownerName) e.preventDefault(); }} onEscapeKeyDown={(e) => { if (!ownerName) e.preventDefault(); }}>
      <DialogHeader><DialogTitle>What should we call you?</DialogTitle><DialogDescription>Your name personalizes this research workspace and its history.</DialogDescription></DialogHeader>
      <form onSubmit={(e) => { e.preventDefault(); saveOwnerName(name); }}>
        <Input autoFocus value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name" maxLength={80} className="h-11" />
        <DialogFooter className="mt-5"><Button type="submit" disabled={!name.trim()}>Continue</Button></DialogFooter>
      </form>
    </DialogContent>
  </Dialog>;
}

function ShellInner({ children }: { children: ReactNode }) {
  const { ready } = useOwner();
  const [mobileOpen, setMobileOpen] = useState(false);
  return <div className="min-h-screen bg-background">
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 bg-sidebar lg:block"><SidebarContent /></aside>
    <header className="sticky top-0 z-20 flex h-16 items-center border-b bg-background/95 px-4 backdrop-blur lg:hidden">
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}><SheetTrigger asChild><Button size="icon" variant="ghost" aria-label="Open navigation"><Menu /></Button></SheetTrigger><SheetContent side="left" className="w-72 border-sidebar-border bg-sidebar p-0 text-sidebar-foreground"><SheetTitle className="sr-only">Navigation</SheetTitle><SidebarContent close={() => setMobileOpen(false)} /></SheetContent></Sheet>
      <span className="ml-3 font-semibold">Deep Research</span>
    </header>
    <main className="min-h-screen lg:pl-64">{ready ? children : <div className="workspace-loading">Preparing your workspace…</div>}</main>
    <OwnerDialog />
  </div>;
}

export function WorkspaceShell({ children }: { children: ReactNode }) { return <OwnerProvider><ShellInner>{children}</ShellInner></OwnerProvider>; }
