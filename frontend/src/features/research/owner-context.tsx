import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

const STORAGE_KEY = "owner_name";
type OwnerContextValue = {
  ownerName: string;
  ready: boolean;
  editing: boolean;
  setEditing: (open: boolean) => void;
  saveOwnerName: (name: string) => void;
};

const OwnerContext = createContext<OwnerContextValue | null>(null);

export function OwnerProvider({ children }: { children: ReactNode }) {
  const [ownerName, setOwnerName] = useState("");
  const [ready, setReady] = useState(false);
  const [editing, setEditing] = useState(false);

  useEffect(() => {
    const stored = window.localStorage.getItem(STORAGE_KEY)?.trim() ?? "";
    setOwnerName(stored);
    setEditing(!stored);
    setReady(true);
  }, []);

  const value = useMemo(
    () => ({
      ownerName,
      ready,
      editing,
      setEditing,
      saveOwnerName: (name: string) => {
        const clean = name.trim();
        if (!clean) return;
        window.localStorage.setItem(STORAGE_KEY, clean);
        setOwnerName(clean);
        setEditing(false);
      },
    }),
    [ownerName, ready, editing],
  );

  return <OwnerContext.Provider value={value}>{children}</OwnerContext.Provider>;
}

export function useOwner() {
  const value = useContext(OwnerContext);
  if (!value) throw new Error("useOwner must be used inside OwnerProvider");
  return value;
}
