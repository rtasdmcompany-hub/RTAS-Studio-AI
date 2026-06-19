"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const STORAGE_KEY = "rtas-cookie-consent";

export function CookieConsent() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    try {
      if (!localStorage.getItem(STORAGE_KEY)) setVisible(true);
    } catch {
      setVisible(true);
    }
  }, []);

  const accept = (value: "all" | "essential") => {
    try {
      localStorage.setItem(STORAGE_KEY, value);
    } catch {
      /* ignore */
    }
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div className="rtas-cookie" role="dialog" aria-label="Cookie preferences">
      <div className="rtas-cookie__panel">
        <p className="rtas-cookie__text">
          We use essential cookies for sign-in and studio preferences. Optional
          analytics help us improve performance. See our{" "}
          <Link href="/cookies">Cookie Policy</Link>.
        </p>
        <div className="rtas-cookie__actions">
          <button
            type="button"
            className="btn-ghost rtas-cookie__btn"
            onClick={() => accept("essential")}
          >
            Essential only
          </button>
          <button
            type="button"
            className="btn-primary rtas-cookie__btn"
            onClick={() => accept("all")}
          >
            Accept all
          </button>
        </div>
      </div>
    </div>
  );
}
